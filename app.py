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
    "Regina, SK": (50.4452, -104.6189),
    "Quebec City, QC": (46.8139, -71.2080),
    "Victoria, BC": (48.4284, -123.3656),
    "Halifax, NS": (44.6488, -63.5752),
    "Moncton, NB": (46.0878, -64.7782),
    "St. John's, NL": (47.5615, -52.7126),
    "Yellowknife, NT": (62.4540, -114.3718),
    "Whitehorse, YT": (60.7212, -135.0568),
    "Iqaluit, NU": (63.7467, -68.5170),
}

AIRPORTS = {
    "YYZ": {"name": "Toronto Pearson", "lat": 43.6777, "lon": -79.6248, "remote": False},
    "YTZ": {"name": "Toronto Billy Bishop", "lat": 43.6285, "lon": -79.3962, "remote": False},
    "YUL": {"name": "Montreal Trudeau", "lat": 45.4706, "lon": -73.7408, "remote": False},
    "YHU": {"name": "Montreal Saint-Hubert", "lat": 45.5175, "lon": -73.4169, "remote": False},
    "YVR": {"name": "Vancouver", "lat": 49.1967, "lon": -123.1815, "remote": False},
    "YYC": {"name": "Calgary", "lat": 51.1215, "lon": -114.0076, "remote": False},
    "YEG": {"name": "Edmonton", "lat": 53.3097, "lon": -113.5797, "remote": False},
    "YOW": {"name": "Ottawa", "lat": 45.3225, "lon": -75.6692, "remote": False},
    "YWG": {"name": "Winnipeg", "lat": 49.9099, "lon": -97.2399, "remote": False},
    "YXE": {"name": "Saskatoon", "lat": 52.1708, "lon": -106.6997, "remote": False},
    "YQR": {"name": "Regina", "lat": 50.4319, "lon": -104.6658, "remote": False},
    "YQB": {"name": "Quebec City", "lat": 46.7911, "lon": -71.3933, "remote": False},
    "YYJ": {"name": "Victoria", "lat": 48.6469, "lon": -123.4258, "remote": False},
    "YLW": {"name": "Kelowna", "lat": 49.9561, "lon": -119.3778, "remote": False},
    "YXX": {"name": "Abbotsford", "lat": 49.0253, "lon": -122.3606, "remote": False},
    "YQQ": {"name": "Comox", "lat": 49.7108, "lon": -124.8867, "remote": False},
    "YCD": {"name": "Nanaimo", "lat": 49.0523, "lon": -123.8702, "remote": False},
    "YKA": {"name": "Kamloops", "lat": 50.7022, "lon": -120.4444, "remote": False},
    "YXS": {"name": "Prince George", "lat": 53.8894, "lon": -122.6789, "remote": False},
    "YMM": {"name": "Fort McMurray", "lat": 56.6533, "lon": -111.2219, "remote": False},
    "YQU": {"name": "Grande Prairie", "lat": 55.1797, "lon": -118.8850, "remote": False},
    "YQL": {"name": "Lethbridge", "lat": 49.6303, "lon": -112.7997, "remote": False},
    "YBR": {"name": "Brandon", "lat": 49.9100, "lon": -99.9519, "remote": False},
    "YHZ": {"name": "Halifax", "lat": 44.8808, "lon": -63.5086, "remote": False},
    "YYG": {"name": "Charlottetown", "lat": 46.2900, "lon": -63.1211, "remote": False},
    "YFC": {"name": "Fredericton", "lat": 45.8689, "lon": -66.5372, "remote": False},
    "YSJ": {"name": "Saint John", "lat": 45.3161, "lon": -65.8903, "remote": False},
    "YQM": {"name": "Moncton", "lat": 46.1122, "lon": -64.6786, "remote": False},
    "YYT": {"name": "St. John's", "lat": 47.6186, "lon": -52.7519, "remote": False},
    "YDF": {"name": "Deer Lake", "lat": 49.2108, "lon": -57.3914, "remote": False},
    "YQX": {"name": "Gander", "lat": 48.9369, "lon": -54.5681, "remote": False},
    "YYR": {"name": "Goose Bay", "lat": 53.3192, "lon": -60.4258, "remote": True},
    "YHM": {"name": "Hamilton", "lat": 43.1736, "lon": -79.9350, "remote": False},
    "YKF": {"name": "Kitchener-Waterloo", "lat": 43.4608, "lon": -80.3786, "remote": False},
    "YXU": {"name": "London", "lat": 43.0356, "lon": -81.1539, "remote": False},
    "YQG": {"name": "Windsor", "lat": 42.2756, "lon": -82.9556, "remote": False},
    "YQT": {"name": "Thunder Bay", "lat": 48.3719, "lon": -89.3239, "remote": False},
    "YSB": {"name": "Sudbury", "lat": 46.6250, "lon": -80.7989, "remote": False},
    "YAM": {"name": "Sault Ste. Marie", "lat": 46.4850, "lon": -84.5094, "remote": False},
    "YTS": {"name": "Timmins", "lat": 48.5697, "lon": -81.3767, "remote": False},
    "YYB": {"name": "North Bay", "lat": 46.3636, "lon": -79.4228, "remote": False},
    "YBG": {"name": "Saguenay-Bagotville", "lat": 48.3306, "lon": -70.9964, "remote": False},
    "YZV": {"name": "Sept-Iles", "lat": 50.2233, "lon": -66.2656, "remote": False},
    "YUY": {"name": "Rouyn-Noranda", "lat": 48.2061, "lon": -78.8356, "remote": False},
    "YVO": {"name": "Val-d'Or", "lat": 48.0533, "lon": -77.7828, "remote": False},
    "YZF": {"name": "Yellowknife", "lat": 62.4628, "lon": -114.4403, "remote": True},
    "YXY": {"name": "Whitehorse", "lat": 60.7096, "lon": -135.0673, "remote": True},
    "YFB": {"name": "Iqaluit", "lat": 63.7564, "lon": -68.5558, "remote": True},
    "YRT": {"name": "Rankin Inlet", "lat": 62.8114, "lon": -92.1158, "remote": True},
    "YCB": {"name": "Cambridge Bay", "lat": 69.1081, "lon": -105.1383, "remote": True},
    "YEV": {"name": "Inuvik", "lat": 68.3042, "lon": -133.4828, "remote": True},
}

DIRECT_AIRPORTS = {
    "YYZ",
    "YTZ",
    "YUL",
    "YVR",
    "YYC",
    "YEG",
    "YOW",
    "YWG",
    "YXE",
    "YQR",
    "YQB",
    "YYJ",
    "YLW",
    "YXX",
    "YQQ",
    "YCD",
    "YKA",
    "YXS",
    "YMM",
    "YQU",
    "YQL",
    "YBR",
    "YHZ",
    "YYG",
    "YFC",
    "YSJ",
    "YQM",
    "YYT",
    "YDF",
    "YQX",
    "YYR",
    "YHM",
    "YKF",
    "YXU",
    "YQG",
    "YQT",
    "YSB",
    "YAM",
    "YTS",
    "YYB",
    "YBG",
    "YZV",
    "YUY",
    "YVO",
    "YZF",
    "YXY",
    "YFB",
    "YRT",
    "YCB",
    "YEV",
}

DIRECT_SERVICE_HUBS = {"YYZ", "YUL", "YVR", "YYC", "YEG", "YWG", "YHZ", "YOW"}

DIRECT_FLIGHT_PAIRS = {
    frozenset((origin, destination))
    for origin in DIRECT_SERVICE_HUBS
    for destination in DIRECT_SERVICE_HUBS
    if origin != destination
}
DIRECT_FLIGHT_PAIRS.update(
    frozenset(pair)
    for pair in [
        ("YTZ", "YUL"),
        ("YTZ", "YOW"),
        ("YTZ", "YQB"),
        ("YTZ", "YHZ"),
        ("YTZ", "YQM"),
        ("YTZ", "YFC"),
        ("YTZ", "YQT"),
        ("YTZ", "YSB"),
        ("YTZ", "YAM"),
        ("YTZ", "YTS"),
        ("YTZ", "YYB"),
        ("YTZ", "YXU"),
        ("YTZ", "YQG"),
        ("YHU", "YUL"),
        ("YHU", "YQB"),
        ("YXE", "YYC"),
        ("YXE", "YWG"),
        ("YXE", "YYZ"),
        ("YQR", "YYC"),
        ("YQR", "YWG"),
        ("YQR", "YYZ"),
        ("YQB", "YUL"),
        ("YQB", "YOW"),
        ("YQB", "YYZ"),
        ("YYJ", "YVR"),
        ("YYJ", "YYC"),
        ("YYJ", "YYZ"),
        ("YLW", "YVR"),
        ("YLW", "YYC"),
        ("YLW", "YEG"),
        ("YLW", "YYZ"),
        ("YXX", "YVR"),
        ("YXX", "YYC"),
        ("YXX", "YEG"),
        ("YXX", "YWG"),
        ("YXX", "YYZ"),
        ("YQQ", "YVR"),
        ("YQQ", "YYC"),
        ("YQQ", "YEG"),
        ("YQQ", "YYZ"),
        ("YQQ", "YLW"),
        ("YCD", "YVR"),
        ("YCD", "YYC"),
        ("YCD", "YEG"),
        ("YKA", "YVR"),
        ("YKA", "YYC"),
        ("YXS", "YVR"),
        ("YXS", "YYC"),
        ("YMM", "YEG"),
        ("YMM", "YYC"),
        ("YMM", "YYZ"),
        ("YQU", "YEG"),
        ("YQU", "YYC"),
        ("YQL", "YYC"),
        ("YBR", "YWG"),
        ("YBR", "YYC"),
        ("YYG", "YHZ"),
        ("YYG", "YYZ"),
        ("YYG", "YUL"),
        ("YFC", "YHZ"),
        ("YFC", "YYZ"),
        ("YFC", "YUL"),
        ("YSJ", "YHZ"),
        ("YSJ", "YYZ"),
        ("YSJ", "YUL"),
        ("YQM", "YHZ"),
        ("YQM", "YYZ"),
        ("YQM", "YUL"),
        ("YYT", "YHZ"),
        ("YYT", "YYZ"),
        ("YYT", "YUL"),
        ("YYT", "YOW"),
        ("YDF", "YHZ"),
        ("YDF", "YYZ"),
        ("YQX", "YHZ"),
        ("YQX", "YYT"),
        ("YYR", "YHZ"),
        ("YYR", "YYT"),
        ("YHM", "YYC"),
        ("YHM", "YEG"),
        ("YHM", "YHZ"),
        ("YHM", "YVR"),
        ("YKF", "YYC"),
        ("YKF", "YVR"),
        ("YKF", "YHZ"),
        ("YXU", "YYZ"),
        ("YXU", "YOW"),
        ("YXU", "YUL"),
        ("YQG", "YYZ"),
        ("YQT", "YYZ"),
        ("YQT", "YWG"),
        ("YSB", "YYZ"),
        ("YAM", "YYZ"),
        ("YTS", "YYZ"),
        ("YYB", "YYZ"),
        ("YBG", "YUL"),
        ("YZV", "YUL"),
        ("YZV", "YQB"),
        ("YUY", "YUL"),
        ("YVO", "YUL"),
        ("YZF", "YEG"),
        ("YZF", "YYC"),
        ("YZF", "YVR"),
        ("YXY", "YVR"),
        ("YXY", "YYC"),
        ("YXY", "YEG"),
        ("YXY", "YZF"),
        ("YFB", "YOW"),
        ("YFB", "YUL"),
        ("YRT", "YWG"),
        ("YRT", "YFB"),
        ("YCB", "YZF"),
        ("YCB", "YRT"),
        ("YEV", "YZF"),
        ("YEV", "YXY"),
    ]
)
ROUTING_MODEL_VERSION = "|".join(
    [
        "air-routing-v4",
        *(
            f"{code}:{airport['lat']}:{airport['lon']}:{airport['remote']}"
            for code, airport in sorted(AIRPORTS.items())
        ),
        f"direct:{','.join(sorted(DIRECT_AIRPORTS))}",
        f"hubs:{','.join(sorted(DIRECT_SERVICE_HUBS))}",
        f"routes:{','.join(sorted('-'.join(sorted(pair)) for pair in DIRECT_FLIGHT_PAIRS))}",
    ]
)

CANADA_BOUNDS = {
    "min_lat": 41.0,
    "max_lat": 84.0,
    "min_lon": -142.0,
    "max_lon": -52.0,
}
CELL_STEP_DEGREES = 0.15
CELL_DATA_VERSION = "cell-tooltip-v2"

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


@dataclass(frozen=True)
class RouteLeg:
    mode: str
    start_name: str
    end_name: str
    hours: float
    distance_km: float
    path: list[list[float]]
    color: list[int]


@dataclass(frozen=True)
class RoutePlan:
    destination: Place
    total_hours: float
    total_distance_km: float
    mode: str
    legs: list[RouteLeg]


@dataclass(frozen=True)
class AirRouteCandidate:
    mode: str
    total_hours: float
    origin_code: str
    origin_airport: dict[str, object]
    origin_access_km: float
    destination_code: str
    destination_airport: dict[str, object]
    destination_access_km: float
    direct_service: bool
    hub_code: str | None


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


def nearest_airport(lat: float, lon: float, prefer_hub: bool = False) -> tuple[str, dict[str, object], float]:
    airport_code = ""
    airport = {}
    distance = float("inf")

    if prefer_hub:
        for code in DIRECT_SERVICE_HUBS:
            candidate = AIRPORTS[code]
            candidate_distance = haversine_km(lat, lon, candidate["lat"], candidate["lon"])
            if candidate_distance < distance:
                airport_code = code
                airport = candidate
                distance = candidate_distance
        if distance <= 90:
            return airport_code, airport, distance

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


def airport_display_name(code: str, airport: dict[str, object]) -> str:
    return f"{airport['name']} ({code})"


def airport_city_name(airport: dict[str, object]) -> str:
    replacements = {
        "Toronto Pearson": "Toronto",
        "Toronto Billy Bishop": "Toronto",
        "Montreal Trudeau": "Montreal",
        "Montreal Saint-Hubert": "Montreal",
        "Quebec City": "Quebec City",
        "St. John's": "St. John's",
        "Kitchener-Waterloo": "Kitchener-Waterloo",
        "Sault Ste. Marie": "Sault Ste. Marie",
        "Saguenay-Bagotville": "Saguenay",
        "Sept-Iles": "Sept-Iles",
    }
    name = str(airport["name"])
    return replacements.get(name, name)


def origin_location_options() -> dict[str, tuple[float, float]]:
    options: dict[str, tuple[float, float]] = {
        name.split(",")[0]: coordinates for name, coordinates in CANADIAN_LOCATIONS.items()
    }

    for airport in AIRPORTS.values():
        options.setdefault(airport_city_name(airport), (airport["lat"], airport["lon"]))

    return dict(sorted(options.items(), key=lambda item: item[0].casefold()))


def nearby_airport_label(lat: float, lon: float, threshold_km: float = 20) -> str | None:
    code, airport, distance_km = nearest_airport(lat, lon)
    if distance_km <= threshold_km:
        return airport_display_name(code, airport)
    return None


def airport_access_hours(distance_km: float, lat: float) -> float:
    if distance_km <= 35:
        return 0.45 + distance_km / 75
    if lat >= 58:
        return 0.8 + distance_km / 45
    return 0.65 + distance_km / 65


def destination_ground_hours(distance_km: float, lat: float) -> float:
    if distance_km <= 35:
        return 0.35 + distance_km / 70
    if lat >= 58:
        return 0.8 + distance_km / 45
    return 0.25 + distance_km / 80


def has_direct_service(origin_code: str, destination_code: str) -> bool:
    if origin_code == destination_code:
        return False
    return frozenset((origin_code, destination_code)) in DIRECT_FLIGHT_PAIRS


def airport_distance_km(origin_code: str, destination_code: str) -> float:
    origin_airport = AIRPORTS[origin_code]
    destination_airport = AIRPORTS[destination_code]
    return haversine_km(
        origin_airport["lat"],
        origin_airport["lon"],
        destination_airport["lat"],
        destination_airport["lon"],
    )


def flight_block_hours(distance_km: float) -> float:
    return max(0.55, distance_km / 820)


def best_connection_hub(origin_code: str, destination_code: str) -> tuple[str, dict[str, object], float] | None:
    candidates = []

    for hub_code in DIRECT_SERVICE_HUBS:
        if hub_code in {origin_code, destination_code}:
            continue
        if not has_direct_service(origin_code, hub_code):
            continue
        if not has_direct_service(hub_code, destination_code):
            continue

        first_distance = airport_distance_km(origin_code, hub_code)
        second_distance = airport_distance_km(hub_code, destination_code)
        flight_hours = flight_block_hours(first_distance) + flight_block_hours(second_distance)
        candidates.append((hub_code, AIRPORTS[hub_code], flight_hours))

    if not candidates:
        return None

    return min(candidates, key=lambda item: item[2])


def flight_itinerary_hours(origin_code: str, destination_code: str) -> tuple[bool, str | None, float]:
    terminal_hours = 1.0
    connection_hours = 1.2

    if origin_code == destination_code:
        return False, None, 0.0

    if has_direct_service(origin_code, destination_code):
        return True, None, terminal_hours + flight_block_hours(airport_distance_km(origin_code, destination_code))

    connection = best_connection_hub(origin_code, destination_code)
    if not connection:
        return False, None, float("inf")

    hub_code = connection[0]
    first_distance = airport_distance_km(origin_code, hub_code)
    second_distance = airport_distance_km(hub_code, destination_code)
    total_hours = terminal_hours + flight_block_hours(first_distance) + connection_hours + flight_block_hours(second_distance)
    return False, hub_code, total_hours


def best_air_route(origin: Place, lat: float, lon: float, direct_distance_km: float) -> AirRouteCandidate | None:
    origin_code, origin_airport, origin_access_km = nearest_airport(origin.lat, origin.lon, prefer_hub=True)
    origin_access_hours = airport_access_hours(origin_access_km, origin.lat)
    candidates: list[AirRouteCandidate] = []

    for destination_code, destination_airport in AIRPORTS.items():
        destination_access_km = haversine_km(lat, lon, destination_airport["lat"], destination_airport["lon"])
        if direct_distance_km < 420 and destination_access_km > 70:
            continue

        destination_access_hours = destination_ground_hours(destination_access_km, lat)
        direct_service, hub_code, flight_hours = flight_itinerary_hours(origin_code, destination_code)
        if not math.isfinite(flight_hours):
            continue

        total_hours = origin_access_hours + flight_hours + destination_access_hours

        if destination_airport["remote"] or destination_access_km > 180 or lat >= 58:
            mode = "Air + remote access"
        elif direct_service:
            mode = "Direct flight + ground"
        else:
            mode = "Connecting flight + ground"

        candidates.append(
            AirRouteCandidate(
                mode=mode,
                total_hours=total_hours,
                origin_code=origin_code,
                origin_airport=origin_airport,
                origin_access_km=origin_access_km,
                destination_code=destination_code,
                destination_airport=destination_airport,
                destination_access_km=destination_access_km,
                direct_service=direct_service,
                hub_code=hub_code,
            )
        )

    if not candidates:
        return None

    return min(candidates, key=lambda candidate: candidate.total_hours)


def air_travel_candidate(origin: Place, lat: float, lon: float, direct_distance_km: float) -> tuple[str, float] | None:
    candidate = best_air_route(origin, lat, lon, direct_distance_km)
    if not candidate:
        return None
    return candidate.mode, candidate.total_hours


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


def route_path(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> list[list[float]]:
    return [[start_lon, start_lat], [end_lon, end_lat]]


def nearest_known_place(lat: float, lon: float, threshold_km: float = 60) -> str:
    nearest_name = ""
    nearest_distance = float("inf")

    for name, coordinates in CANADIAN_LOCATIONS.items():
        place_lat, place_lon = coordinates
        distance = haversine_km(lat, lon, place_lat, place_lon)
        if distance < nearest_distance:
            nearest_name = name
            nearest_distance = distance

    if nearest_distance <= threshold_km:
        return nearest_name

    nearest_airport_name = ""
    nearest_airport_distance = float("inf")
    for code, airport in AIRPORTS.items():
        distance = haversine_km(lat, lon, airport["lat"], airport["lon"])
        if distance < nearest_airport_distance:
            nearest_airport_name = f"{airport['name']} ({code})"
            nearest_airport_distance = distance

    if nearest_airport_distance <= threshold_km:
        return nearest_airport_name

    return f"Selected destination ({lat:.2f}, {lon:.2f})"


def build_route_plan(origin: Place, destination: Place) -> RoutePlan:
    estimate = estimate_travel(origin, destination.lat, destination.lon)
    direct_distance_km = estimate.distance_km

    air_route = best_air_route(origin, destination.lat, destination.lon, direct_distance_km)
    if estimate.mode in {"Direct flight + ground", "Connecting flight + ground", "Air + remote access"} and air_route:
        origin_code = air_route.origin_code
        origin_airport = air_route.origin_airport
        origin_access_km = air_route.origin_access_km
        destination_code = air_route.destination_code
        destination_airport = air_route.destination_airport
        destination_access_km = air_route.destination_access_km
        direct_service = air_route.direct_service
        hub_code = air_route.hub_code
        origin_access_hours = airport_access_hours(origin_access_km, origin.lat)
        destination_access_hours = destination_ground_hours(destination_access_km, destination.lat)
        legs = [
            RouteLeg(
                mode="Ground access",
                start_name=origin.name,
                end_name=f"{origin_airport['name']} ({origin_code})",
                hours=origin_access_hours,
                distance_km=origin_access_km,
                path=route_path(origin.lat, origin.lon, origin_airport["lat"], origin_airport["lon"]),
                color=[88, 88, 88, 230],
            )
        ]

        if origin_code == destination_code:
            pass
        elif direct_service or not hub_code:
            flight_distance = airport_distance_km(origin_code, destination_code)
            legs.append(
                RouteLeg(
                    mode="Direct flight" if direct_service else "Connecting flight",
                    start_name=f"{origin_airport['name']} ({origin_code})",
                    end_name=f"{destination_airport['name']} ({destination_code})",
                    hours=1.0 + flight_block_hours(flight_distance),
                    distance_km=flight_distance,
                    path=route_path(
                        origin_airport["lat"],
                        origin_airport["lon"],
                        destination_airport["lat"],
                        destination_airport["lon"],
                    ),
                    color=[0, 90, 181, 235] if direct_service else [116, 78, 166, 235],
                )
            )
        else:
            hub_airport = AIRPORTS[hub_code]
            first_distance = airport_distance_km(origin_code, hub_code)
            second_distance = airport_distance_km(hub_code, destination_code)
            legs.extend(
                [
                    RouteLeg(
                        mode="Flight",
                        start_name=f"{origin_airport['name']} ({origin_code})",
                        end_name=f"{hub_airport['name']} ({hub_code})",
                        hours=1.0 + flight_block_hours(first_distance),
                        distance_km=first_distance,
                        path=route_path(
                            origin_airport["lat"],
                            origin_airport["lon"],
                            hub_airport["lat"],
                            hub_airport["lon"],
                        ),
                        color=[116, 78, 166, 235],
                    ),
                    RouteLeg(
                        mode="Connection",
                        start_name=f"{hub_airport['name']} ({hub_code})",
                        end_name=f"{hub_airport['name']} ({hub_code})",
                        hours=1.2,
                        distance_km=0,
                        path=route_path(hub_airport["lat"], hub_airport["lon"], hub_airport["lat"], hub_airport["lon"]),
                        color=[88, 88, 88, 180],
                    ),
                    RouteLeg(
                        mode="Flight",
                        start_name=f"{hub_airport['name']} ({hub_code})",
                        end_name=f"{destination_airport['name']} ({destination_code})",
                        hours=flight_block_hours(second_distance),
                        distance_km=second_distance,
                        path=route_path(
                            hub_airport["lat"],
                            hub_airport["lon"],
                            destination_airport["lat"],
                            destination_airport["lon"],
                        ),
                        color=[116, 78, 166, 235],
                    ),
                ]
            )

        legs.append(
            RouteLeg(
                mode="Drive",
                start_name=f"{destination_airport['name']} ({destination_code})",
                end_name=destination.name,
                hours=destination_access_hours,
                distance_km=destination_access_km,
                path=route_path(destination_airport["lat"], destination_airport["lon"], destination.lat, destination.lon),
                color=[213, 94, 0, 235],
            )
        )
        total_hours = sum(leg.hours for leg in legs)
        total_distance_km = sum(leg.distance_km for leg in legs)
        return RoutePlan(
            destination=destination,
            total_hours=total_hours,
            total_distance_km=total_distance_km,
            mode=estimate.mode,
            legs=legs,
        )

    leg = RouteLeg(
        mode=estimate.mode,
        start_name=origin.name,
        end_name=destination.name,
        hours=estimate.hours,
        distance_km=direct_distance_km,
        path=route_path(origin.lat, origin.lon, destination.lat, destination.lon),
        color=[0, 150, 136, 235] if estimate.mode == "Rail + road" else [213, 94, 0, 235],
    )
    return RoutePlan(
        destination=destination,
        total_hours=estimate.hours,
        total_distance_km=direct_distance_km,
        mode=estimate.mode,
        legs=[leg],
    )


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
    routing_model_version: str,
    cell_data_version: str,
) -> pd.DataFrame:
    _ = time_band_version
    _ = routing_model_version
    _ = cell_data_version
    origin = Place(name=origin_name, lat=origin_lat, lon=origin_lon)
    rows = []
    lat = CANADA_BOUNDS["min_lat"]

    while lat <= CANADA_BOUNDS["max_lat"]:
        lon = CANADA_BOUNDS["min_lon"]
        while lon <= CANADA_BOUNDS["max_lon"]:
            if is_canadian_land(lat, lon):
                estimate = estimate_travel(origin, lat, lon)
                band = time_band(estimate.hours)
                airport_label = nearby_airport_label(lat, lon)
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
                        "tooltip_title": band["label"],
                        "tooltip_time": f"{format_travel_time(estimate.hours)} from {origin.name}",
                        "tooltip_mode": estimate.mode,
                        "tooltip_detail": (
                            f"Near {airport_label}" if airport_label else "Click to select this destination"
                        ),
                        "tooltip_distance": f"{round(estimate.distance_km):,} km direct",
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


def make_route_frame(route_plan: RoutePlan) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "step": index,
            "mode": leg.mode,
            "from": leg.start_name,
            "to": leg.end_name,
            "time": format_travel_time(leg.hours),
            "hours": round(leg.hours, 2),
            "distance_km": round(leg.distance_km, 1),
        }
        for index, leg in enumerate(route_plan.legs, start=1)
    )


def make_map(origin: Place, cells: pd.DataFrame, route_plan: RoutePlan | None = None) -> pdk.Deck:
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
    destination_df = pd.DataFrame()
    route_df = pd.DataFrame()
    if route_plan:
        destination_df = pd.DataFrame(
            [
                {
                    "name": route_plan.destination.name,
                    "lat": route_plan.destination.lat,
                    "lon": route_plan.destination.lon,
                }
            ]
        )
        route_df = pd.DataFrame(
            {
                "mode": leg.mode,
                "from": leg.start_name,
                "to": leg.end_name,
                "time": format_travel_time(leg.hours),
                "band": "",
                "distance_km": round(leg.distance_km),
                "tooltip_title": leg.mode,
                "tooltip_time": format_travel_time(leg.hours),
                "tooltip_mode": "",
                "tooltip_detail": f"{leg.start_name} to {leg.end_name}",
                "tooltip_distance": f"{round(leg.distance_km):,} km",
                "path": leg.path,
                "color": leg.color,
            }
            for leg in route_plan.legs
        )

    layers = [
        pdk.Layer(
            "PolygonLayer",
            id="time-cells",
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
            "PathLayer",
            id="route-legs",
            data=route_df,
            get_path="path",
            get_color="color",
            get_width=5,
            width_min_pixels=3,
            pickable=False,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            id="city-dots",
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
            id="city-labels",
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
            id="selected-destination",
            data=destination_df,
            get_position="[lon, lat]",
            get_radius=45000,
            get_fill_color=[0, 113, 188, 245],
            get_line_color=[255, 255, 255, 255],
            line_width_min_pixels=2,
            stroked=True,
            pickable=False,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            id="origin-marker",
            data=origin_df,
            get_position="[lon, lat]",
            get_radius=55000,
            get_fill_color=[194, 35, 38, 240],
            get_line_color=[255, 255, 255, 255],
            line_width_min_pixels=2,
            stroked=True,
            pickable=False,
        ),
    ]

    return pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
        initial_view_state=pdk.ViewState(latitude=58.5, longitude=-96.5, zoom=3.0, pitch=0),
        layers=layers,
        tooltip={
            "html": "<b>{tooltip_title}</b><br/>{tooltip_time}<br/>{tooltip_mode}<br/>{tooltip_detail}<br/>{tooltip_distance}",
            "style": {"backgroundColor": "#2f2b24", "color": "white"},
        },
    )


def render_sidebar() -> dict[str, object]:
    st.sidebar.header("Origin")
    origin_options = origin_location_options()
    location_name = st.sidebar.selectbox(
        "Origin city",
        options=list(origin_options),
        index=list(origin_options).index("Toronto"),
    )
    city_lat, city_lon = origin_options[location_name]

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
    _ = cells
    rows = "\n".join(
        f"""
        <div class="legend-row">
            <span class="legend-swatch" style="background:{color_to_hex(band['color'])};"></span>
            <span>{band['label']}</span>
        </div>
        """
        for band in TIME_BANDS
    )
    st.markdown(
        f"""
        <style>
            .time-band-legend {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 0.35rem;
            }}
            .legend-row {{
                display: grid;
                grid-template-columns: 2rem 1fr;
                align-items: center;
                gap: 0.65rem;
                min-height: 1.6rem;
            }}
            .legend-swatch {{
                display: inline-block;
                width: 2rem;
                height: 1rem;
                border: 1px solid rgba(47, 43, 36, 0.35);
                border-radius: 2px;
            }}
        </style>
        <div class="time-band-legend">
            {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


def selected_destination_from_event(event: object) -> Place | None:
    if not event:
        return None

    try:
        selection = event.selection
    except AttributeError:
        selection = event.get("selection", {}) if isinstance(event, dict) else {}

    try:
        objects = selection.objects
    except AttributeError:
        objects = selection.get("objects", {}) if isinstance(selection, dict) else {}

    selected_cells = objects.get("time-cells", []) if isinstance(objects, dict) else []
    if not selected_cells:
        return None

    selected_cell = selected_cells[0]
    lat = float(selected_cell["lat"])
    lon = float(selected_cell["lon"])
    return Place(name=nearest_known_place(lat, lon), lat=lat, lon=lon)


def route_plan_from_selection(origin: Place) -> RoutePlan | None:
    selected_state = st.session_state.get("passage_map")
    destination = selected_destination_from_event(selected_state)
    if destination:
        return build_route_plan(origin, destination)
    return None


def render_route_plan(route_plan: RoutePlan | None) -> None:
    if not route_plan:
        st.info("Click a colored cell on the map to set a destination and show the optimal route.")
        return

    st.subheader("Selected Destination Route")
    route_metrics = st.columns([2, 1, 1, 1])
    route_metrics[0].metric("Destination", route_plan.destination.name)
    route_metrics[1].metric("Total time", format_travel_time(route_plan.total_hours))
    route_metrics[2].metric("Optimal mode", route_plan.mode)
    route_metrics[3].metric("Route distance", f"{route_plan.total_distance_km:,.0f} km")
    st.dataframe(make_route_frame(route_plan), hide_index=True, width="stretch")


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
            width="stretch",
        )

    st.subheader("Reference Cities")
    st.dataframe(
        city_estimates[["place", "time", "optimal_mode", "distance_km"]],
        hide_index=True,
        width="stretch",
    )


def main() -> None:
    st.set_page_config(page_title="Canada Isochronic Passage Chart", page_icon="CA", layout="wide")
    st.title("Canada Isochronic Passage Chart")

    controls = render_sidebar()
    origin = controls["origin"]

    cells = build_passage_cells(
        origin.name,
        origin.lat,
        origin.lon,
        controls["step"],
        TIME_BAND_VERSION,
        ROUTING_MODEL_VERSION,
        CELL_DATA_VERSION,
    )
    city_estimates = build_city_estimates(origin)
    route_plan = route_plan_from_selection(origin)

    top_row = st.columns([2, 1, 1])
    top_row[0].metric("Origin", origin.name)
    top_row[1].metric("Latitude", f"{origin.lat:.4f}")
    top_row[2].metric("Longitude", f"{origin.lon:.4f}")

    chart_event = st.pydeck_chart(
        make_map(origin, cells, route_plan),
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-object",
        key="passage_map",
    )
    if not route_plan:
        destination = selected_destination_from_event(chart_event)
        if destination:
            route_plan = build_route_plan(origin, destination)

    render_route_plan(route_plan)
    render_context(cells, city_estimates)


if __name__ == "__main__":
    main()
