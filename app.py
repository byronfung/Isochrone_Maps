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

CANADA_BOUNDS = {
    "min_lat": 41.0,
    "max_lat": 84.0,
    "min_lon": -142.0,
    "max_lon": -52.0,
}

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
    {"label": "Under 2 hr", "max_hours": 2, "color": [248, 232, 137, 190]},
    {"label": "2-4 hr", "max_hours": 4, "color": [178, 210, 110, 190]},
    {"label": "4-8 hr", "max_hours": 8, "color": [84, 177, 132, 190]},
    {"label": "8-12 hr", "max_hours": 12, "color": [58, 145, 180, 190]},
    {"label": "12-24 hr", "max_hours": 24, "color": [69, 102, 170, 190]},
    {"label": "1-2 days", "max_hours": 48, "color": [124, 92, 157, 190]},
    {"label": "2-3 days", "max_hours": 72, "color": [177, 89, 126, 190]},
    {"label": "3-5 days", "max_hours": 120, "color": [183, 123, 74, 190]},
    {"label": "Over 5 days", "max_hours": float("inf"), "color": [115, 86, 72, 190]},
]

MODE_CONTEXT = {
    "Rail + road": "Quebec-Windsor corridor and nearby southern routes",
    "Road": "regional overland travel",
    "Air + ground": "long-distance intercity travel",
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
    point_count = len(polygon)
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


def region_access_penalty(lat: float, lon: float) -> float:
    penalty = 0.8
    if lat >= 55:
        penalty += 1.8
    if lat >= 60:
        penalty += 4.0
    if lat >= 66:
        penalty += 10.0
    if lon <= -125 or lon >= -58:
        penalty += 1.3
    if lat >= 72:
        penalty += 18.0
    return penalty


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


def estimate_travel(origin: Place, lat: float, lon: float) -> TravelEstimate:
    distance_km = haversine_km(origin.lat, origin.lon, lat, lon)
    access_penalty = region_access_penalty(lat, lon)
    candidates: list[tuple[str, float]] = []

    if lat <= 61.5:
        ground_hours = 0.20 + (distance_km * road_multiplier(lat, lon)) / 90
        candidates.append(("Road", ground_hours))

    in_corridor = 42.0 <= lat <= 48.2 and -84.5 <= lon <= -69.5
    if in_corridor:
        rail_hours = 0.6 + (distance_km * 1.10) / 105
        candidates.append(("Rail + road", rail_hours))

    if distance_km >= 650 or lat >= 55:
        air_hours = 3.2 + distance_km / 760 + access_penalty
        mode = "Air + remote access" if access_penalty >= 5.0 or lat >= 58 else "Air + ground"
        candidates.append((mode, air_hours))

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
def build_passage_cells(origin_name: str, origin_lat: float, origin_lon: float, step: float) -> pd.DataFrame:
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

    st.sidebar.header("Chart")
    resolution = st.sidebar.select_slider(
        "Resolution",
        options=["Coarse", "Standard", "Fine"],
        value="Standard",
    )
    step = {"Coarse": 1.25, "Standard": 0.85, "Fine": 0.55}[resolution]

    return {
        "origin": Place(name=origin_name, lat=float(lat), lon=float(lon)),
        "resolution": resolution,
        "step": step,
    }


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
        st.subheader("Time Bands")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "band": band["label"],
                        "upper_bound": "open" if band["max_hours"] == float("inf") else format_travel_time(band["max_hours"]),
                    }
                    for band in TIME_BANDS
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
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

    cells = build_passage_cells(origin.name, origin.lat, origin.lon, controls["step"])
    city_estimates = build_city_estimates(origin)

    top_row = st.columns([2, 1, 1, 1])
    top_row[0].metric("Origin", origin.name)
    top_row[1].metric("Latitude", f"{origin.lat:.4f}")
    top_row[2].metric("Longitude", f"{origin.lon:.4f}")
    top_row[3].metric("Resolution", controls["resolution"])

    st.pydeck_chart(make_map(origin, cells), use_container_width=True)
    render_context(cells, city_estimates)


if __name__ == "__main__":
    main()
