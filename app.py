from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd
import pydeck as pdk
import streamlit as st


TORONTO = {"name": "Toronto, ON", "lat": 43.6532, "lon": -79.3832}

CANADIAN_LOCATIONS = {
    "Toronto, ON": (43.6532, -79.3832),
    "Montreal, QC": (45.5019, -73.5674),
    "Vancouver, BC": (49.2827, -123.1207),
    "Calgary, AB": (51.0447, -114.0719),
    "Edmonton, AB": (53.5461, -113.4938),
    "Ottawa, ON": (45.4215, -75.6972),
    "Winnipeg, MB": (49.8951, -97.1384),
    "Quebec City, QC": (46.8139, -71.2080),
    "Halifax, NS": (44.6488, -63.5752),
    "St. John's, NL": (47.5615, -52.7126),
    "Yellowknife, NT": (62.4540, -114.3718),
    "Whitehorse, YT": (60.7212, -135.0568),
    "Iqaluit, NU": (63.7467, -68.5170),
}

AIRPORTS = {
    "YYZ": {"name": "Toronto Pearson", "lat": 43.6777, "lon": -79.6248, "remote": False},
    "YUL": {"name": "Montreal Trudeau", "lat": 45.4706, "lon": -73.7408, "remote": False},
    "YVR": {"name": "Vancouver", "lat": 49.1967, "lon": -123.1815, "remote": False},
    "YYC": {"name": "Calgary", "lat": 51.1215, "lon": -114.0076, "remote": False},
    "YEG": {"name": "Edmonton", "lat": 53.3097, "lon": -113.5797, "remote": False},
    "YOW": {"name": "Ottawa", "lat": 45.3225, "lon": -75.6692, "remote": False},
    "YWG": {"name": "Winnipeg", "lat": 49.9099, "lon": -97.2399, "remote": False},
    "YQB": {"name": "Quebec City", "lat": 46.7911, "lon": -71.3933, "remote": False},
    "YHZ": {"name": "Halifax", "lat": 44.8808, "lon": -63.5086, "remote": False},
    "YYT": {"name": "St. John's", "lat": 47.6186, "lon": -52.7519, "remote": False},
    "YZF": {"name": "Yellowknife", "lat": 62.4628, "lon": -114.4403, "remote": True},
    "YXY": {"name": "Whitehorse", "lat": 60.7096, "lon": -135.0673, "remote": True},
    "YFB": {"name": "Iqaluit", "lat": 63.7564, "lon": -68.5558, "remote": True},
}

DIRECT_AIRPORTS = {"YYZ", "YUL", "YVR", "YYC", "YEG", "YOW", "YWG", "YQB", "YHZ", "YYT"}

CANADA_BOUNDS = {
    "min_lat": 41.0,
    "max_lat": 84.0,
    "min_lon": -142.0,
    "max_lon": -52.0,
}
CELL_STEP_DEGREES = 0.15

MAINLAND_POLYGON = [
    (-141.0, 69.5),
    (-136.5, 60.5),
    (-132.5, 56.5),
    (-127.5, 51.0),
    (-124.0, 48.7),
    (-114.0, 49.0),
    (-102.0, 49.0),
    (-95.0, 49.0),
    (-88.0, 47.8),
    (-82.0, 42.0),
    (-75.0, 44.5),
    (-68.0, 45.0),
    (-61.0, 46.5),
    (-53.5, 51.5),
    (-58.0, 54.0),
    (-65.0, 56.5),
    (-72.0, 59.5),
    (-81.0, 62.0),
    (-90.0, 64.0),
    (-98.0, 68.0),
    (-109.0, 69.0),
    (-121.0, 70.0),
    (-134.0, 70.5),
    (-141.0, 69.5),
]

LAND_POLYGONS = [
    MAINLAND_POLYGON,
    [(-128.8, 50.8), (-125.2, 48.3), (-123.0, 48.3), (-124.5, 50.9), (-127.8, 51.4), (-128.8, 50.8)],
    [(-59.8, 52.0), (-55.0, 51.7), (-52.5, 49.4), (-53.4, 47.2), (-57.3, 46.4), (-59.6, 48.6), (-59.8, 52.0)],
    [(-64.6, 47.3), (-61.8, 47.1), (-61.9, 45.7), (-64.2, 45.8), (-64.6, 47.3)],
    [(-91.0, 76.0), (-80.0, 72.5), (-65.0, 66.0), (-63.0, 62.0), (-72.0, 62.0), (-85.0, 66.0), (-92.0, 70.5), (-91.0, 76.0)],
    [(-125.0, 76.0), (-112.0, 72.0), (-102.0, 72.5), (-100.0, 76.0), (-112.0, 78.0), (-125.0, 76.0)],
    [(-101.0, 80.8), (-86.0, 78.0), (-75.0, 78.8), (-68.0, 81.0), (-78.0, 83.2), (-94.0, 83.0), (-101.0, 80.8)],
    [(-122.0, 73.5), (-114.0, 70.5), (-105.0, 70.0), (-108.0, 73.2), (-116.5, 75.0), (-122.0, 73.5)],
]

EXCLUDED_WATER_POLYGONS = [
    [(-96.5, 51.0), (-88.5, 51.0), (-80.0, 55.0), (-78.0, 60.0), (-85.5, 64.0), (-94.0, 62.5), (-97.5, 57.0), (-96.5, 51.0)],
]

TIME_BANDS = [
    {"label": "Under 30 min", "max_hours": 0.5, "color": [255, 247, 188, 190]},
    {"label": "30-60 min", "max_hours": 1, "color": [254, 227, 145, 190]},
    {"label": "1-1.5 hr", "max_hours": 1.5, "color": [254, 196, 79, 190]},
    {"label": "1.5-2 hr", "max_hours": 2, "color": [251, 154, 41, 190]},
    {"label": "2-3 hr", "max_hours": 3, "color": [236, 112, 20, 190]},
    {"label": "3-4 hr", "max_hours": 4, "color": [204, 76, 2, 190]},
    {"label": "4-5 hr", "max_hours": 5, "color": [166, 120, 42, 190]},
    {"label": "5-6 hr", "max_hours": 6, "color": [128, 155, 61, 190]},
    {"label": "6-8 hr", "max_hours": 8, "color": [83, 176, 86, 190]},
    {"label": "8-10 hr", "max_hours": 10, "color": [49, 163, 111, 190]},
    {"label": "10-12 hr", "max_hours": 12, "color": [26, 143, 141, 190]},
    {"label": "12-16 hr", "max_hours": 16, "color": [34, 123, 169, 190]},
    {"label": "16-20 hr", "max_hours": 20, "color": [55, 102, 175, 190]},
    {"label": "20-24 hr", "max_hours": 24, "color": [78, 80, 170, 190]},
    {"label": "1-1.5 days", "max_hours": 36, "color": [111, 75, 159, 190]},
    {"label": "1.5-2 days", "max_hours": 48, "color": [143, 71, 146, 190]},
    {"label": "2-3 days", "max_hours": 72, "color": [174, 69, 126, 190]},
    {"label": "3-4 days", "max_hours": 96, "color": [190, 91, 94, 190]},
    {"label": "4-5 days", "max_hours": 120, "color": [178, 117, 72, 190]},
    {"label": "Over 5 days", "max_hours": float("inf"), "color": [111, 78, 65, 190]},
]
TIME_BAND_VERSION = "|".join(f"{band['label']}:{band['max_hours']}:{band['color']}" for band in TIME_BANDS)

MODE_CONTEXT = {
    "Rail + road": "Quebec-Windsor corridor and nearby southern routes",
    "Road": "regional overland travel",
    "Direct flight + ground": "major airport-to-airport service",
    "Connecting flight + ground": "air travel through a hub",
    "Air + remote access": "northern and low-access areas",
}


@dataclass(frozen=True)
class Place:
    name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class TravelEstimate:
    hours: float
    mode: str
    distance_km: float


def point_in_polygon(lon: float, lat: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    previous_lon, previous_lat = polygon[-1]

    for current_lon, current_lat in polygon:
        crosses_lat = (current_lat > lat) != (previous_lat > lat)
        if crosses_lat:
            slope_lon = (previous_lon - current_lon) * (lat - current_lat) / (previous_lat - current_lat) + current_lon
            if lon < slope_lon:
                inside = not inside
        previous_lon, previous_lat = current_lon, current_lat

    return inside


def is_canadian_land(lat: float, lon: float) -> bool:
    in_land = any(point_in_polygon(lon, lat, polygon) for polygon in LAND_POLYGONS)
    in_excluded_water = any(point_in_polygon(lon, lat, polygon) for polygon in EXCLUDED_WATER_POLYGONS)
    return in_land and not in_excluded_water


def haversine_km(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> float:
    radius_km = 6371.0088
    start_lat_rad = math.radians(start_lat)
    end_lat_rad = math.radians(end_lat)
    delta_lat = math.radians(end_lat - start_lat)
    delta_lon = math.radians(end_lon - start_lon)

    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(start_lat_rad) * math.cos(end_lat_rad) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * radius_km * math.asin(math.sqrt(value))


def format_travel_time(hours: float) -> str:
    if hours < 24:
        rounded_hours = int(hours)
        minutes = round((hours - rounded_hours) * 60)
        if rounded_hours and minutes:
            return f"{rounded_hours} hr {minutes} min"
        if rounded_hours:
            return f"{rounded_hours} hr"
        return f"{max(1, minutes)} min"

    days = hours / 24
    if days < 10:
        return f"{days:.1f} days"
    return f"{round(days)} days"


def time_band(hours: float) -> dict[str, object]:
    for band in TIME_BANDS:
        if hours <= band["max_hours"]:
            return band
    return TIME_BANDS[-1]


def road_multiplier(lat: float, lon: float) -> float:
    multiplier = 1.22
    if lat >= 52:
        multiplier += 0.18
    if lat >= 57:
        multiplier += 0.45
    if lat >= 60:
        multiplier += 0.85
    if lon <= -120:
        multiplier += 0.25
    if lon >= -64:
        multiplier += 0.20
    return multiplier


def nearest_airport(lat: float, lon: float) -> tuple[str, dict[str, object], float]:
    airport_code = ""
    airport = {}
    distance = float("inf")

    for code, candidate in AIRPORTS.items():
        candidate_distance = haversine_km(lat, lon, candidate["lat"], candidate["lon"])
        if candidate_distance < distance:
            airport_code = code
            airport = candidate
            distance = candidate_distance

    return airport_code, airport, distance


def airport_access_hours(distance_km: float, lat: float) -> float:
    if distance_km <= 35:
        return 0.45 + distance_km / 75
    if lat >= 58:
        return 0.8 + distance_km / 45
    return 0.65 + distance_km / 65


def air_travel_candidate(origin: Place, lat: float, lon: float, direct_distance_km: float) -> tuple[str, float] | None:
    origin_code, origin_airport, origin_access_km = nearest_airport(origin.lat, origin.lon)
    destination_code, destination_airport, destination_access_km = nearest_airport(lat, lon)
    destination_is_airport_reachable = destination_access_km <= 260 or lat >= 58

    if direct_distance_km < 420 and destination_access_km > 70:
        return None
    if not destination_is_airport_reachable:
        return None

    airport_distance_km = haversine_km(
        origin_airport["lat"],
        origin_airport["lon"],
        destination_airport["lat"],
        destination_airport["lon"],
    )
    origin_access_hours = airport_access_hours(origin_access_km, origin.lat)
    destination_access_hours = airport_access_hours(destination_access_km, lat)
    direct_service = origin_code in DIRECT_AIRPORTS and destination_code in DIRECT_AIRPORTS
    connection_hours = 0.0 if direct_service else 1.35
    terminal_hours = 1.0 if direct_service else 1.25
    flight_hours = airport_distance_km / 820
    total_hours = terminal_hours + origin_access_hours + flight_hours + connection_hours + destination_access_hours

    if destination_airport["remote"] or destination_access_km > 100 or lat >= 58:
        mode = "Air + remote access"
    elif direct_service:
        mode = "Direct flight + ground"
    else:
        mode = "Connecting flight + ground"

    return mode, total_hours


def estimate_travel(origin: Place, lat: float, lon: float) -> TravelEstimate:
    distance_km = haversine_km(origin.lat, origin.lon, lat, lon)
    candidates: list[tuple[str, float]] = []

    if lat <= 61.5:
        ground_hours = 0.20 + (distance_km * road_multiplier(lat, lon)) / 90
        candidates.append(("Road", ground_hours))

    in_corridor = 42.0 <= lat <= 48.2 and -84.5 <= lon <= -69.5
    if in_corridor:
        rail_hours = 0.6 + (distance_km * 1.10) / 105
        candidates.append(("Rail + road", rail_hours))

    air_candidate = air_travel_candidate(origin, lat, lon, distance_km)
    if air_candidate:
        candidates.append(air_candidate)

    if not candidates:
        candidates.append(("Road", distance_km / 40))

    mode, hours = min(candidates, key=lambda item: item[1])
    return TravelEstimate(hours=hours, mode=mode, distance_km=distance_km)


def cell_polygon(lat: float, lon: float, step: float) -> list[list[float]]:
    half = step / 2
    return [
        [lon - half, lat - half],
        [lon + half, lat - half],
        [lon + half, lat + half],
        [lon - half, lat + half],
        [lon - half, lat - half],
    ]


@st.cache_data(show_spinner=False)
def build_passage_cells(
    origin_name: str,
    origin_lat: float,
    origin_lon: float,
    step: float,
    time_band_version: str,
) -> pd.DataFrame:
    _ = time_band_version
    origin = Place(name=origin_name, lat=origin_lat, lon=origin_lon)
    rows = []
    lat = CANADA_BOUNDS["min_lat"]

    while lat <= CANADA_BOUNDS["max_lat"]:
        lon = CANADA_BOUNDS["min_lon"]
        while lon <= CANADA_BOUNDS["max_lon"]:
            if is_canadian_land(lat, lon):
                estimate = estimate_travel(origin, lat, lon)
                band = time_band(estimate.hours)
                rows.append(
                    {
                        "lat": lat,
                        "lon": lon,
                        "polygon": cell_polygon(lat, lon, step),
                        "hours": round(estimate.hours, 2),
                        "time": format_travel_time(estimate.hours),
                        "band": band["label"],
                        "fill_color": band["color"],
                        "mode": estimate.mode,
                        "distance_km": round(estimate.distance_km),
                    }
                )
            lon += step
        lat += step

    return pd.DataFrame(rows)


def build_city_estimates(origin: Place) -> pd.DataFrame:
    rows = []
    for name, (lat, lon) in CANADIAN_LOCATIONS.items():
        estimate = estimate_travel(origin, lat, lon)
        rows.append(
            {
                "place": name,
                "time": format_travel_time(estimate.hours),
                "hours": round(estimate.hours, 1),
                "optimal_mode": estimate.mode,
                "distance_km": round(estimate.distance_km),
            }
        )
    return pd.DataFrame(rows).sort_values("hours")


def build_city_label_frame() -> pd.DataFrame:
    rows = []
    for name, (lat, lon) in CANADIAN_LOCATIONS.items():
        city = name.split(",")[0]
        rows.append(
            {
                "name": name,
                "label": city,
                "lat": lat,
                "lon": lon,
                "size": 15 if name in {"Toronto, ON", "Montreal, QC", "Vancouver, BC", "Calgary, AB"} else 13,
            }
        )
    return pd.DataFrame(rows)


def make_map(origin: Place, cells: pd.DataFrame) -> pdk.Deck:
    origin_df = pd.DataFrame(
        [
            {
                "name": origin.name,
                "lat": origin.lat,
                "lon": origin.lon,
            }
        ]
    )
    city_df = build_city_label_frame()

    layers = [
        pdk.Layer(
            "PolygonLayer",
            data=cells,
            get_polygon="polygon",
            get_fill_color="fill_color",
            get_line_color=[76, 67, 56, 80],
            get_line_width=35,
            line_width_min_pixels=0,
            pickable=True,
            stroked=True,
            filled=True,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=city_df,
            get_position="[lon, lat]",
            get_radius=23000,
            get_fill_color=[47, 43, 36, 220],
            get_line_color=[255, 255, 255, 230],
            line_width_min_pixels=1,
            stroked=True,
            pickable=False,
        ),
        pdk.Layer(
            "TextLayer",
            data=city_df,
            get_position="[lon, lat]",
            get_text="label",
            get_size="size",
            get_color=[35, 31, 27, 240],
            get_text_anchor='"middle"',
            get_alignment_baseline='"bottom"',
            get_pixel_offset=[0, -10],
            pickable=False,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=origin_df,
            get_position="[lon, lat]",
            get_radius=55000,
            get_fill_color=[194, 35, 38, 240],
            get_line_color=[255, 255, 255, 255],
            line_width_min_pixels=2,
            stroked=True,
            pickable=True,
        ),
    ]

    return pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
        initial_view_state=pdk.ViewState(latitude=58.5, longitude=-96.5, zoom=3.0, pitch=0),
        layers=layers,
        tooltip={
            "html": "<b>{band}</b><br/>{time} from origin<br/>{mode}<br/>{distance_km} km direct",
            "style": {"backgroundColor": "#2f2b24", "color": "white"},
        },
    )


def render_sidebar() -> dict[str, object]:
    st.sidebar.header("Origin")
    location_name = st.sidebar.selectbox(
        "Canadian city",
        options=list(CANADIAN_LOCATIONS),
        index=list(CANADIAN_LOCATIONS).index(TORONTO["name"]),
    )
    city_lat, city_lon = CANADIAN_LOCATIONS[location_name]

    custom_location = st.sidebar.checkbox("Use custom origin coordinates")
    if custom_location:
        lat = st.sidebar.number_input(
            "Latitude",
            min_value=CANADA_BOUNDS["min_lat"],
            max_value=CANADA_BOUNDS["max_lat"],
            value=city_lat,
            format="%.6f",
        )
        lon = st.sidebar.number_input(
            "Longitude",
            min_value=CANADA_BOUNDS["min_lon"],
            max_value=CANADA_BOUNDS["max_lon"],
            value=city_lon,
            format="%.6f",
        )
        origin_name = "Custom origin"
    else:
        lat, lon = city_lat, city_lon
        origin_name = location_name

    return {
        "origin": Place(name=origin_name, lat=float(lat), lon=float(lon)),
        "step": CELL_STEP_DEGREES,
    }


def color_to_hex(color: list[int]) -> str:
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def render_time_band_legend(cells: pd.DataFrame) -> None:
    band_counts = cells["band"].value_counts().to_dict()
    legend_rows = []

    for band in TIME_BANDS:
        mapped_cells = band_counts.get(band["label"], 0)
        upper_bound = "open" if band["max_hours"] == float("inf") else format_travel_time(band["max_hours"])
        legend_rows.append(
            {
                "band": band["label"],
                "upper_bound": upper_bound,
                "mapped_cells": mapped_cells,
                "active": "yes" if mapped_cells else "no",
                "map_color": color_to_hex(band["color"]),
            }
        )

    st.dataframe(
        pd.DataFrame(legend_rows),
        hide_index=True,
        use_container_width=True,
    )


def render_context(cells: pd.DataFrame, city_estimates: pd.DataFrame) -> None:
    fastest = cells.loc[cells["hours"].idxmin()]
    slowest = cells.loc[cells["hours"].idxmax()]
    dominant_mode = cells["mode"].value_counts().idxmax()

    context = st.container(border=True)
    context.subheader("Passage Chart Context")
    metrics = context.columns(4)
    metrics[0].metric("Nearest band", fastest["band"])
    metrics[1].metric("Farthest band", slowest["band"])
    metrics[2].metric("Dominant mode", dominant_mode)
    metrics[3].metric("Mapped cells", f"{len(cells):,}")

    mode_frame = (
        cells.groupby("mode", as_index=False)
        .agg(cells=("mode", "size"), median_hours=("hours", "median"))
        .sort_values("cells", ascending=False)
    )
    mode_frame["median_time"] = mode_frame["median_hours"].map(format_travel_time)
    mode_frame["context"] = mode_frame["mode"].map(MODE_CONTEXT)

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Time Band Legend")
        render_time_band_legend(cells)
    with right:
        st.subheader("Optimal Modes")
        st.dataframe(
            mode_frame[["mode", "median_time", "cells", "context"]],
            hide_index=True,
            use_container_width=True,
        )

    st.subheader("Reference Cities")
    st.dataframe(
        city_estimates[["place", "time", "optimal_mode", "distance_km"]],
        hide_index=True,
        use_container_width=True,
    )


def main() -> None:
    st.set_page_config(page_title="Canada Isochronic Passage Chart", page_icon="CA", layout="wide")
    st.title("Canada Isochronic Passage Chart")

    controls = render_sidebar()
    origin = controls["origin"]

    cells = build_passage_cells(origin.name, origin.lat, origin.lon, controls["step"], TIME_BAND_VERSION)
    city_estimates = build_city_estimates(origin)

    top_row = st.columns([2, 1, 1, 1])
    top_row[0].metric("Origin", origin.name)
    top_row[1].metric("Latitude", f"{origin.lat:.4f}")
    top_row[2].metric("Longitude", f"{origin.lon:.4f}")
    top_row[3].metric("Cell size", f"{controls['step']:.2f} deg")

    st.pydeck_chart(make_map(origin, cells), use_container_width=True)
    render_context(cells, city_estimates)


if __name__ == "__main__":
    main()
