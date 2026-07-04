from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd
import pydeck as pdk
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "cache"
AIRPORT_CACHE_CSV = CACHE_DIR / "world_airports.csv"
FLIGHT_ROUTE_CACHE_CSV = CACHE_DIR / "world_flight_routes.csv"

TORONTO = {"name": "Toronto, ON", "lat": 43.6532, "lon": -79.3832}

WORLD_LOCATIONS = {
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
    "Churchill, MB": (58.7684, -94.1650),
    "Yellowknife, NT": (62.4540, -114.3718),
    "Whitehorse, YT": (60.7212, -135.0568),
    "Iqaluit, NU": (63.7467, -68.5170),
}

WORLD_LOCATIONS.update(
    {
        "New York, NY": (40.7128, -74.0060),
        "Los Angeles, CA": (34.0522, -118.2437),
        "Chicago, IL": (41.8781, -87.6298),
        "Houston, TX": (29.7604, -95.3698),
        "Phoenix, AZ": (33.4484, -112.0740),
        "Philadelphia, PA": (39.9526, -75.1652),
        "San Antonio, TX": (29.4241, -98.4936),
        "San Diego, CA": (32.7157, -117.1611),
        "Dallas, TX": (32.7767, -96.7970),
        "San Jose, CA": (37.3382, -121.8863),
        "Austin, TX": (30.2672, -97.7431),
        "Jacksonville, FL": (30.3322, -81.6557),
        "Fort Worth, TX": (32.7555, -97.3308),
        "Columbus, OH": (39.9612, -82.9988),
        "Charlotte, NC": (35.2271, -80.8431),
        "San Francisco, CA": (37.7749, -122.4194),
        "Indianapolis, IN": (39.7684, -86.1581),
        "Seattle, WA": (47.6062, -122.3321),
        "Denver, CO": (39.7392, -104.9903),
        "Washington, DC": (38.9072, -77.0369),
        "Boston, MA": (42.3601, -71.0589),
        "El Paso, TX": (31.7619, -106.4850),
        "Nashville, TN": (36.1627, -86.7816),
        "Detroit, MI": (42.3314, -83.0458),
        "Portland, OR": (45.5152, -122.6784),
        "Las Vegas, NV": (36.1699, -115.1398),
        "Memphis, TN": (35.1495, -90.0490),
        "Louisville, KY": (38.2527, -85.7585),
        "Baltimore, MD": (39.2904, -76.6122),
        "Milwaukee, WI": (43.0389, -87.9065),
        "Albuquerque, NM": (35.0844, -106.6504),
        "Tucson, AZ": (32.2226, -110.9747),
        "Fresno, CA": (36.7378, -119.7871),
        "Sacramento, CA": (38.5816, -121.4944),
        "Kansas City, MO": (39.0997, -94.5786),
        "Atlanta, GA": (33.7490, -84.3880),
        "Miami, FL": (25.7617, -80.1918),
        "New Orleans, LA": (29.9511, -90.0715),
        "Minneapolis, MN": (44.9778, -93.2650),
        "Anchorage, AK": (61.2181, -149.9003),
        "Mexico City, CMX": (19.4326, -99.1332),
        "Guadalajara, JAL": (20.6597, -103.3496),
        "Monterrey, NLE": (25.6866, -100.3161),
        "Puebla, PUE": (19.0414, -98.2063),
        "Tijuana, BCN": (32.5149, -117.0382),
        "Leon, GUA": (21.1220, -101.6820),
        "Juarez, CHH": (31.6904, -106.4245),
        "Merida, YUC": (20.9674, -89.5926),
        "Cancun, ROO": (21.1619, -86.8515),
        "Queretaro, QUE": (20.5888, -100.3899),
        "Hermosillo, SON": (29.0729, -110.9559),
        "Chihuahua, CHH": (28.6320, -106.0691),
        "Veracruz, VER": (19.1738, -96.1342),
        "Oaxaca, OAX": (17.0732, -96.7266),
        "London, UK": (51.5074, -0.1278),
        "Paris, FR": (48.8566, 2.3522),
        "Madrid, ES": (40.4168, -3.7038),
        "Barcelona, ES": (41.3874, 2.1686),
        "Rome, IT": (41.9028, 12.4964),
        "Milan, IT": (45.4642, 9.1900),
        "Berlin, DE": (52.5200, 13.4050),
        "Frankfurt, DE": (50.1109, 8.6821),
        "Amsterdam, NL": (52.3676, 4.9041),
        "Brussels, BE": (50.8503, 4.3517),
        "Zurich, CH": (47.3769, 8.5417),
        "Vienna, AT": (48.2082, 16.3738),
        "Copenhagen, DK": (55.6761, 12.5683),
        "Stockholm, SE": (59.3293, 18.0686),
        "Oslo, NO": (59.9139, 10.7522),
        "Helsinki, FI": (60.1699, 24.9384),
        "Dublin, IE": (53.3498, -6.2603),
        "Lisbon, PT": (38.7223, -9.1393),
        "Athens, GR": (37.9838, 23.7275),
        "Istanbul, TR": (41.0082, 28.9784),
        "Warsaw, PL": (52.2297, 21.0122),
        "Prague, CZ": (50.0755, 14.4378),
        "Budapest, HU": (47.4979, 19.0402),
        "Moscow, RU": (55.7558, 37.6173),
        "Cairo, EG": (30.0444, 31.2357),
        "Casablanca, MA": (33.5731, -7.5898),
        "Lagos, NG": (6.5244, 3.3792),
        "Nairobi, KE": (-1.2921, 36.8219),
        "Johannesburg, ZA": (-26.2041, 28.0473),
        "Cape Town, ZA": (-33.9249, 18.4241),
        "Addis Ababa, ET": (8.9806, 38.7578),
        "Accra, GH": (5.6037, -0.1870),
        "Doha, QA": (25.2854, 51.5310),
        "Dubai, AE": (25.2048, 55.2708),
        "Riyadh, SA": (24.7136, 46.6753),
        "Tel Aviv, IL": (32.0853, 34.7818),
        "Mumbai, IN": (19.0760, 72.8777),
        "Delhi, IN": (28.6139, 77.2090),
        "Bengaluru, IN": (12.9716, 77.5946),
        "Chennai, IN": (13.0827, 80.2707),
        "Kolkata, IN": (22.5726, 88.3639),
        "Bangkok, TH": (13.7563, 100.5018),
        "Singapore, SG": (1.3521, 103.8198),
        "Kuala Lumpur, MY": (3.1390, 101.6869),
        "Jakarta, ID": (-6.2088, 106.8456),
        "Manila, PH": (14.5995, 120.9842),
        "Ho Chi Minh City, VN": (10.8231, 106.6297),
        "Hanoi, VN": (21.0278, 105.8342),
        "Hong Kong, HK": (22.3193, 114.1694),
        "Taipei, TW": (25.0330, 121.5654),
        "Seoul, KR": (37.5665, 126.9780),
        "Tokyo, JP": (35.6762, 139.6503),
        "Osaka, JP": (34.6937, 135.5023),
        "Beijing, CN": (39.9042, 116.4074),
        "Shanghai, CN": (31.2304, 121.4737),
        "Guangzhou, CN": (23.1291, 113.2644),
        "Shenzhen, CN": (22.5431, 114.0579),
        "Chengdu, CN": (30.5728, 104.0668),
        "Sydney, AU": (-33.8688, 151.2093),
        "Melbourne, AU": (-37.8136, 144.9631),
        "Brisbane, AU": (-27.4698, 153.0251),
        "Perth, AU": (-31.9523, 115.8613),
        "Auckland, NZ": (-36.8509, 174.7645),
        "Sao Paulo, BR": (-23.5558, -46.6396),
        "Rio de Janeiro, BR": (-22.9068, -43.1729),
        "Buenos Aires, AR": (-34.6037, -58.3816),
        "Santiago, CL": (-33.4489, -70.6693),
        "Lima, PE": (-12.0464, -77.0428),
        "Bogota, CO": (4.7110, -74.0721),
        "Medellin, CO": (6.2442, -75.5812),
        "Quito, EC": (-0.1807, -78.4678),
        "Panama City, PA": (8.9824, -79.5199),
        "San Jose, CR": (9.9281, -84.0907),
        "Havana, CU": (23.1136, -82.3666),
        "Santo Domingo, DO": (18.4861, -69.9312),
        "San Juan, PR": (18.4655, -66.1057),
    }
)

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
    "YYQ": {"name": "Churchill", "lat": 58.7392, "lon": -94.0650, "remote": True},
    "YRT": {"name": "Rankin Inlet", "lat": 62.8114, "lon": -92.1158, "remote": True},
    "YCB": {"name": "Cambridge Bay", "lat": 69.1081, "lon": -105.1383, "remote": True},
    "YEV": {"name": "Inuvik", "lat": 68.3042, "lon": -133.4828, "remote": True},
}

AIRPORTS.update(
    {
        "ATL": {"name": "Atlanta Hartsfield-Jackson", "lat": 33.6407, "lon": -84.4277, "remote": False},
        "LAX": {"name": "Los Angeles", "lat": 33.9416, "lon": -118.4085, "remote": False},
        "ORD": {"name": "Chicago O'Hare", "lat": 41.9742, "lon": -87.9073, "remote": False},
        "MDW": {"name": "Chicago Midway", "lat": 41.7868, "lon": -87.7522, "remote": False},
        "DFW": {"name": "Dallas-Fort Worth", "lat": 32.8998, "lon": -97.0403, "remote": False},
        "DAL": {"name": "Dallas Love Field", "lat": 32.8471, "lon": -96.8518, "remote": False},
        "DEN": {"name": "Denver", "lat": 39.8561, "lon": -104.6737, "remote": False},
        "JFK": {"name": "New York JFK", "lat": 40.6413, "lon": -73.7781, "remote": False},
        "LGA": {"name": "New York LaGuardia", "lat": 40.7769, "lon": -73.8740, "remote": False},
        "EWR": {"name": "Newark Liberty", "lat": 40.6895, "lon": -74.1745, "remote": False},
        "BOS": {"name": "Boston Logan", "lat": 42.3656, "lon": -71.0096, "remote": False},
        "PHL": {"name": "Philadelphia", "lat": 39.8744, "lon": -75.2424, "remote": False},
        "DCA": {"name": "Washington National", "lat": 38.8512, "lon": -77.0402, "remote": False},
        "IAD": {"name": "Washington Dulles", "lat": 38.9531, "lon": -77.4565, "remote": False},
        "BWI": {"name": "Baltimore-Washington", "lat": 39.1774, "lon": -76.6684, "remote": False},
        "MIA": {"name": "Miami", "lat": 25.7959, "lon": -80.2870, "remote": False},
        "FLL": {"name": "Fort Lauderdale", "lat": 26.0742, "lon": -80.1506, "remote": False},
        "MCO": {"name": "Orlando", "lat": 28.4312, "lon": -81.3081, "remote": False},
        "TPA": {"name": "Tampa", "lat": 27.9755, "lon": -82.5332, "remote": False},
        "CLT": {"name": "Charlotte Douglas", "lat": 35.2144, "lon": -80.9473, "remote": False},
        "RDU": {"name": "Raleigh-Durham", "lat": 35.8801, "lon": -78.7880, "remote": False},
        "BNA": {"name": "Nashville", "lat": 36.1263, "lon": -86.6774, "remote": False},
        "MEM": {"name": "Memphis", "lat": 35.0424, "lon": -89.9767, "remote": False},
        "DTW": {"name": "Detroit Metro", "lat": 42.2162, "lon": -83.3554, "remote": False},
        "MSP": {"name": "Minneapolis-Saint Paul", "lat": 44.8848, "lon": -93.2223, "remote": False},
        "MKE": {"name": "Milwaukee", "lat": 42.9472, "lon": -87.8966, "remote": False},
        "STL": {"name": "St. Louis", "lat": 38.7499, "lon": -90.3748, "remote": False},
        "MCI": {"name": "Kansas City", "lat": 39.2976, "lon": -94.7139, "remote": False},
        "SDF": {"name": "Louisville", "lat": 38.1744, "lon": -85.7360, "remote": False},
        "CMH": {"name": "Columbus", "lat": 39.9999, "lon": -82.8872, "remote": False},
        "IND": {"name": "Indianapolis", "lat": 39.7173, "lon": -86.2944, "remote": False},
        "IAH": {"name": "Houston Intercontinental", "lat": 29.9902, "lon": -95.3368, "remote": False},
        "HOU": {"name": "Houston Hobby", "lat": 29.6454, "lon": -95.2789, "remote": False},
        "AUS": {"name": "Austin-Bergstrom", "lat": 30.1975, "lon": -97.6664, "remote": False},
        "SAT": {"name": "San Antonio", "lat": 29.5337, "lon": -98.4698, "remote": False},
        "MSY": {"name": "New Orleans", "lat": 29.9934, "lon": -90.2580, "remote": False},
        "PHX": {"name": "Phoenix Sky Harbor", "lat": 33.4342, "lon": -112.0116, "remote": False},
        "TUS": {"name": "Tucson", "lat": 32.1161, "lon": -110.9410, "remote": False},
        "ABQ": {"name": "Albuquerque", "lat": 35.0494, "lon": -106.6172, "remote": False},
        "ELP": {"name": "El Paso", "lat": 31.8072, "lon": -106.3776, "remote": False},
        "LAS": {"name": "Las Vegas", "lat": 36.0840, "lon": -115.1537, "remote": False},
        "SLC": {"name": "Salt Lake City", "lat": 40.7899, "lon": -111.9791, "remote": False},
        "SEA": {"name": "Seattle-Tacoma", "lat": 47.4502, "lon": -122.3088, "remote": False},
        "PDX": {"name": "Portland", "lat": 45.5898, "lon": -122.5951, "remote": False},
        "SFO": {"name": "San Francisco", "lat": 37.6213, "lon": -122.3790, "remote": False},
        "OAK": {"name": "Oakland", "lat": 37.7126, "lon": -122.2197, "remote": False},
        "SJC": {"name": "San Jose", "lat": 37.3639, "lon": -121.9289, "remote": False},
        "SMF": {"name": "Sacramento", "lat": 38.6954, "lon": -121.5908, "remote": False},
        "SAN": {"name": "San Diego", "lat": 32.7338, "lon": -117.1933, "remote": False},
        "FAT": {"name": "Fresno", "lat": 36.7762, "lon": -119.7181, "remote": False},
        "ANC": {"name": "Anchorage", "lat": 61.1744, "lon": -149.9964, "remote": True},
        "FAI": {"name": "Fairbanks", "lat": 64.8151, "lon": -147.8564, "remote": True},
        "JNU": {"name": "Juneau", "lat": 58.3550, "lon": -134.5763, "remote": True},
        "MEX": {"name": "Mexico City", "lat": 19.4361, "lon": -99.0719, "remote": False},
        "NLU": {"name": "Felipe Angeles", "lat": 19.7420, "lon": -99.0140, "remote": False},
        "GDL": {"name": "Guadalajara", "lat": 20.5218, "lon": -103.3112, "remote": False},
        "MTY": {"name": "Monterrey", "lat": 25.7785, "lon": -100.1069, "remote": False},
        "CUN": {"name": "Cancun", "lat": 21.0365, "lon": -86.8771, "remote": False},
        "TIJ": {"name": "Tijuana", "lat": 32.5411, "lon": -116.9702, "remote": False},
        "PVR": {"name": "Puerto Vallarta", "lat": 20.6801, "lon": -105.2542, "remote": False},
        "SJD": {"name": "Los Cabos", "lat": 23.1518, "lon": -109.7210, "remote": False},
        "MID": {"name": "Merida", "lat": 20.9370, "lon": -89.6577, "remote": False},
        "QRO": {"name": "Queretaro", "lat": 20.6173, "lon": -100.1857, "remote": False},
        "BJX": {"name": "Bajio", "lat": 20.9935, "lon": -101.4808, "remote": False},
        "HMO": {"name": "Hermosillo", "lat": 29.0959, "lon": -111.0479, "remote": False},
        "CJS": {"name": "Ciudad Juarez", "lat": 31.6361, "lon": -106.4287, "remote": False},
        "OAX": {"name": "Oaxaca", "lat": 16.9999, "lon": -96.7266, "remote": False},
        "VER": {"name": "Veracruz", "lat": 19.1459, "lon": -96.1873, "remote": False},
        "PBC": {"name": "Puebla", "lat": 19.1581, "lon": -98.3714, "remote": False},
        "CLE": {"name": "Cleveland Hopkins", "lat": 41.4117, "lon": -81.8498, "remote": False},
        "PIT": {"name": "Pittsburgh", "lat": 40.4915, "lon": -80.2329, "remote": False},
        "CVG": {"name": "Cincinnati-Northern Kentucky", "lat": 39.0488, "lon": -84.6678, "remote": False},
        "BUF": {"name": "Buffalo Niagara", "lat": 42.9405, "lon": -78.7322, "remote": False},
        "ROC": {"name": "Rochester", "lat": 43.1189, "lon": -77.6724, "remote": False},
        "SYR": {"name": "Syracuse", "lat": 43.1112, "lon": -76.1063, "remote": False},
        "ALB": {"name": "Albany", "lat": 42.7483, "lon": -73.8017, "remote": False},
        "BDL": {"name": "Hartford Bradley", "lat": 41.9389, "lon": -72.6832, "remote": False},
        "PVD": {"name": "Providence", "lat": 41.7240, "lon": -71.4282, "remote": False},
        "PWM": {"name": "Portland Maine", "lat": 43.6462, "lon": -70.3093, "remote": False},
        "RIC": {"name": "Richmond", "lat": 37.5052, "lon": -77.3197, "remote": False},
        "ORF": {"name": "Norfolk", "lat": 36.8946, "lon": -76.2012, "remote": False},
        "CHS": {"name": "Charleston", "lat": 32.8986, "lon": -80.0405, "remote": False},
        "SAV": {"name": "Savannah", "lat": 32.1276, "lon": -81.2021, "remote": False},
        "JAX": {"name": "Jacksonville", "lat": 30.4941, "lon": -81.6879, "remote": False},
        "PBI": {"name": "Palm Beach", "lat": 26.6832, "lon": -80.0956, "remote": False},
        "RSW": {"name": "Fort Myers", "lat": 26.5362, "lon": -81.7552, "remote": False},
        "BHM": {"name": "Birmingham", "lat": 33.5629, "lon": -86.7535, "remote": False},
        "GSP": {"name": "Greenville-Spartanburg", "lat": 34.8957, "lon": -82.2189, "remote": False},
        "OKC": {"name": "Oklahoma City", "lat": 35.3931, "lon": -97.6007, "remote": False},
        "TUL": {"name": "Tulsa", "lat": 36.1984, "lon": -95.8881, "remote": False},
        "OMA": {"name": "Omaha", "lat": 41.3032, "lon": -95.8941, "remote": False},
        "DSM": {"name": "Des Moines", "lat": 41.5340, "lon": -93.6631, "remote": False},
        "GRR": {"name": "Grand Rapids", "lat": 42.8808, "lon": -85.5228, "remote": False},
        "FAR": {"name": "Fargo", "lat": 46.9207, "lon": -96.8158, "remote": False},
        "BIS": {"name": "Bismarck", "lat": 46.7727, "lon": -100.7460, "remote": False},
        "RAP": {"name": "Rapid City", "lat": 44.0453, "lon": -103.0574, "remote": False},
        "BOI": {"name": "Boise", "lat": 43.5644, "lon": -116.2228, "remote": False},
        "GEG": {"name": "Spokane", "lat": 47.6199, "lon": -117.5338, "remote": False},
        "RNO": {"name": "Reno-Tahoe", "lat": 39.4991, "lon": -119.7681, "remote": False},
        "BUR": {"name": "Burbank", "lat": 34.2007, "lon": -118.3587, "remote": False},
        "LGB": {"name": "Long Beach", "lat": 33.8177, "lon": -118.1516, "remote": False},
        "ONT": {"name": "Ontario California", "lat": 34.0560, "lon": -117.6012, "remote": False},
        "SNA": {"name": "Orange County", "lat": 33.6757, "lon": -117.8682, "remote": False},
        "PSP": {"name": "Palm Springs", "lat": 33.8297, "lon": -116.5067, "remote": False},
        "COS": {"name": "Colorado Springs", "lat": 38.8058, "lon": -104.7008, "remote": False},
        "FSD": {"name": "Sioux Falls", "lat": 43.5820, "lon": -96.7419, "remote": False},
        "XNA": {"name": "Northwest Arkansas", "lat": 36.2819, "lon": -94.3068, "remote": False},
        "CUU": {"name": "Chihuahua", "lat": 28.7029, "lon": -105.9646, "remote": False},
        "CUL": {"name": "Culiacan", "lat": 24.7645, "lon": -107.4747, "remote": False},
        "MZT": {"name": "Mazatlan", "lat": 23.1614, "lon": -106.2661, "remote": False},
        "LAP": {"name": "La Paz", "lat": 24.0727, "lon": -110.3625, "remote": False},
        "CEN": {"name": "Ciudad Obregon", "lat": 27.3926, "lon": -109.8331, "remote": False},
        "AGU": {"name": "Aguascalientes", "lat": 21.7056, "lon": -102.3179, "remote": False},
        "DGO": {"name": "Durango", "lat": 24.1242, "lon": -104.5280, "remote": False},
        "TRC": {"name": "Torreon", "lat": 25.5683, "lon": -103.4106, "remote": False},
        "MLM": {"name": "Morelia", "lat": 19.8499, "lon": -101.0255, "remote": False},
        "ZIH": {"name": "Ixtapa-Zihuatanejo", "lat": 17.6016, "lon": -101.4605, "remote": False},
        "PXM": {"name": "Puerto Escondido", "lat": 15.8769, "lon": -97.0891, "remote": False},
        "VSA": {"name": "Villahermosa", "lat": 17.9969, "lon": -92.8174, "remote": False},
        "TGZ": {"name": "Tuxtla Gutierrez", "lat": 16.5618, "lon": -93.0261, "remote": False},
    }
)

AIRPORTS.update(
    {
        "LHR": {"name": "London Heathrow", "lat": 51.4700, "lon": -0.4543, "remote": False},
        "LGW": {"name": "London Gatwick", "lat": 51.1537, "lon": -0.1821, "remote": False},
        "MAN": {"name": "Manchester", "lat": 53.3650, "lon": -2.2722, "remote": False},
        "EDI": {"name": "Edinburgh", "lat": 55.9500, "lon": -3.3725, "remote": False},
        "DUB": {"name": "Dublin", "lat": 53.4213, "lon": -6.2701, "remote": False},
        "CDG": {"name": "Paris Charles de Gaulle", "lat": 49.0097, "lon": 2.5479, "remote": False},
        "ORY": {"name": "Paris Orly", "lat": 48.7262, "lon": 2.3652, "remote": False},
        "AMS": {"name": "Amsterdam Schiphol", "lat": 52.3105, "lon": 4.7683, "remote": False},
        "BRU": {"name": "Brussels", "lat": 50.9014, "lon": 4.4844, "remote": False},
        "FRA": {"name": "Frankfurt", "lat": 50.0379, "lon": 8.5622, "remote": False},
        "MUC": {"name": "Munich", "lat": 48.3538, "lon": 11.7861, "remote": False},
        "BER": {"name": "Berlin Brandenburg", "lat": 52.3667, "lon": 13.5033, "remote": False},
        "HAM": {"name": "Hamburg", "lat": 53.6304, "lon": 9.9882, "remote": False},
        "ZRH": {"name": "Zurich", "lat": 47.4581, "lon": 8.5555, "remote": False},
        "GVA": {"name": "Geneva", "lat": 46.2381, "lon": 6.1089, "remote": False},
        "VIE": {"name": "Vienna", "lat": 48.1103, "lon": 16.5697, "remote": False},
        "CPH": {"name": "Copenhagen", "lat": 55.6180, "lon": 12.6508, "remote": False},
        "ARN": {"name": "Stockholm Arlanda", "lat": 59.6519, "lon": 17.9186, "remote": False},
        "OSL": {"name": "Oslo", "lat": 60.1939, "lon": 11.1004, "remote": False},
        "HEL": {"name": "Helsinki", "lat": 60.3172, "lon": 24.9633, "remote": False},
        "MAD": {"name": "Madrid Barajas", "lat": 40.4983, "lon": -3.5676, "remote": False},
        "BCN": {"name": "Barcelona", "lat": 41.2974, "lon": 2.0833, "remote": False},
        "LIS": {"name": "Lisbon", "lat": 38.7742, "lon": -9.1342, "remote": False},
        "FCO": {"name": "Rome Fiumicino", "lat": 41.8003, "lon": 12.2389, "remote": False},
        "MXP": {"name": "Milan Malpensa", "lat": 45.6306, "lon": 8.7281, "remote": False},
        "ATH": {"name": "Athens", "lat": 37.9364, "lon": 23.9475, "remote": False},
        "WAW": {"name": "Warsaw Chopin", "lat": 52.1657, "lon": 20.9671, "remote": False},
        "PRG": {"name": "Prague", "lat": 50.1008, "lon": 14.2632, "remote": False},
        "BUD": {"name": "Budapest", "lat": 47.4394, "lon": 19.2611, "remote": False},
        "IST": {"name": "Istanbul", "lat": 41.2753, "lon": 28.7519, "remote": False},
        "SAW": {"name": "Istanbul Sabiha Gokcen", "lat": 40.8986, "lon": 29.3092, "remote": False},
        "SVO": {"name": "Moscow Sheremetyevo", "lat": 55.9726, "lon": 37.4146, "remote": False},
        "DME": {"name": "Moscow Domodedovo", "lat": 55.4088, "lon": 37.9063, "remote": False},
        "LED": {"name": "St. Petersburg", "lat": 59.8003, "lon": 30.2625, "remote": False},
        "CAI": {"name": "Cairo", "lat": 30.1219, "lon": 31.4056, "remote": False},
        "CMN": {"name": "Casablanca", "lat": 33.3675, "lon": -7.5899, "remote": False},
        "RAK": {"name": "Marrakesh", "lat": 31.6069, "lon": -8.0363, "remote": False},
        "LOS": {"name": "Lagos", "lat": 6.5774, "lon": 3.3212, "remote": False},
        "ABV": {"name": "Abuja", "lat": 9.0068, "lon": 7.2632, "remote": False},
        "ACC": {"name": "Accra", "lat": 5.6052, "lon": -0.1668, "remote": False},
        "ADD": {"name": "Addis Ababa", "lat": 8.9779, "lon": 38.7993, "remote": False},
        "NBO": {"name": "Nairobi", "lat": -1.3192, "lon": 36.9278, "remote": False},
        "DAR": {"name": "Dar es Salaam", "lat": -6.8781, "lon": 39.2026, "remote": False},
        "JNB": {"name": "Johannesburg", "lat": -26.1337, "lon": 28.2420, "remote": False},
        "CPT": {"name": "Cape Town", "lat": -33.9694, "lon": 18.5972, "remote": False},
        "DUR": {"name": "Durban", "lat": -29.6144, "lon": 31.1197, "remote": False},
        "DOH": {"name": "Doha", "lat": 25.2731, "lon": 51.6081, "remote": False},
        "DXB": {"name": "Dubai", "lat": 25.2532, "lon": 55.3657, "remote": False},
        "AUH": {"name": "Abu Dhabi", "lat": 24.4330, "lon": 54.6511, "remote": False},
        "RUH": {"name": "Riyadh", "lat": 24.9576, "lon": 46.6988, "remote": False},
        "JED": {"name": "Jeddah", "lat": 21.6796, "lon": 39.1565, "remote": False},
        "TLV": {"name": "Tel Aviv Ben Gurion", "lat": 32.0114, "lon": 34.8867, "remote": False},
        "AMM": {"name": "Amman", "lat": 31.7226, "lon": 35.9932, "remote": False},
        "DEL": {"name": "Delhi", "lat": 28.5562, "lon": 77.1000, "remote": False},
        "BOM": {"name": "Mumbai", "lat": 19.0896, "lon": 72.8656, "remote": False},
        "BLR": {"name": "Bengaluru", "lat": 13.1986, "lon": 77.7066, "remote": False},
        "MAA": {"name": "Chennai", "lat": 12.9941, "lon": 80.1709, "remote": False},
        "HYD": {"name": "Hyderabad", "lat": 17.2403, "lon": 78.4294, "remote": False},
        "CCU": {"name": "Kolkata", "lat": 22.6547, "lon": 88.4467, "remote": False},
        "KHI": {"name": "Karachi", "lat": 24.9065, "lon": 67.1608, "remote": False},
        "ISB": {"name": "Islamabad", "lat": 33.5607, "lon": 72.8516, "remote": False},
        "DAC": {"name": "Dhaka", "lat": 23.8433, "lon": 90.3978, "remote": False},
        "CMB": {"name": "Colombo", "lat": 7.1808, "lon": 79.8841, "remote": False},
        "BKK": {"name": "Bangkok Suvarnabhumi", "lat": 13.6900, "lon": 100.7501, "remote": False},
        "DMK": {"name": "Bangkok Don Mueang", "lat": 13.9126, "lon": 100.6067, "remote": False},
        "SIN": {"name": "Singapore Changi", "lat": 1.3644, "lon": 103.9915, "remote": False},
        "KUL": {"name": "Kuala Lumpur", "lat": 2.7456, "lon": 101.7072, "remote": False},
        "CGK": {"name": "Jakarta", "lat": -6.1256, "lon": 106.6559, "remote": False},
        "DPS": {"name": "Bali Denpasar", "lat": -8.7482, "lon": 115.1672, "remote": False},
        "MNL": {"name": "Manila", "lat": 14.5086, "lon": 121.0196, "remote": False},
        "SGN": {"name": "Ho Chi Minh City", "lat": 10.8188, "lon": 106.6519, "remote": False},
        "HAN": {"name": "Hanoi", "lat": 21.2212, "lon": 105.8072, "remote": False},
        "HKG": {"name": "Hong Kong", "lat": 22.3080, "lon": 113.9185, "remote": False},
        "TPE": {"name": "Taipei Taoyuan", "lat": 25.0797, "lon": 121.2342, "remote": False},
        "ICN": {"name": "Seoul Incheon", "lat": 37.4602, "lon": 126.4407, "remote": False},
        "GMP": {"name": "Seoul Gimpo", "lat": 37.5583, "lon": 126.7906, "remote": False},
        "NRT": {"name": "Tokyo Narita", "lat": 35.7720, "lon": 140.3929, "remote": False},
        "HND": {"name": "Tokyo Haneda", "lat": 35.5494, "lon": 139.7798, "remote": False},
        "KIX": {"name": "Osaka Kansai", "lat": 34.4273, "lon": 135.2440, "remote": False},
        "CTS": {"name": "Sapporo New Chitose", "lat": 42.7752, "lon": 141.6923, "remote": False},
        "FUK": {"name": "Fukuoka", "lat": 33.5859, "lon": 130.4507, "remote": False},
        "PEK": {"name": "Beijing Capital", "lat": 40.0799, "lon": 116.6031, "remote": False},
        "PKX": {"name": "Beijing Daxing", "lat": 39.5099, "lon": 116.4109, "remote": False},
        "PVG": {"name": "Shanghai Pudong", "lat": 31.1443, "lon": 121.8083, "remote": False},
        "SHA": {"name": "Shanghai Hongqiao", "lat": 31.1979, "lon": 121.3363, "remote": False},
        "CAN": {"name": "Guangzhou", "lat": 23.3924, "lon": 113.2988, "remote": False},
        "SZX": {"name": "Shenzhen", "lat": 22.6393, "lon": 113.8107, "remote": False},
        "CTU": {"name": "Chengdu Shuangliu", "lat": 30.5785, "lon": 103.9471, "remote": False},
        "TFU": {"name": "Chengdu Tianfu", "lat": 30.3125, "lon": 104.4410, "remote": False},
        "XIY": {"name": "Xi'an", "lat": 34.4471, "lon": 108.7516, "remote": False},
        "SYD": {"name": "Sydney", "lat": -33.9399, "lon": 151.1753, "remote": False},
        "MEL": {"name": "Melbourne", "lat": -37.6690, "lon": 144.8410, "remote": False},
        "BNE": {"name": "Brisbane", "lat": -27.3842, "lon": 153.1175, "remote": False},
        "PER": {"name": "Perth", "lat": -31.9403, "lon": 115.9669, "remote": False},
        "ADL": {"name": "Adelaide", "lat": -34.9450, "lon": 138.5306, "remote": False},
        "DRW": {"name": "Darwin", "lat": -12.4147, "lon": 130.8777, "remote": False},
        "AKL": {"name": "Auckland", "lat": -37.0082, "lon": 174.7850, "remote": False},
        "WLG": {"name": "Wellington", "lat": -41.3272, "lon": 174.8053, "remote": False},
        "CHC": {"name": "Christchurch", "lat": -43.4894, "lon": 172.5322, "remote": False},
        "NAN": {"name": "Nadi", "lat": -17.7554, "lon": 177.4434, "remote": True},
        "HNL": {"name": "Honolulu", "lat": 21.3187, "lon": -157.9224, "remote": True},
        "SFO": {"name": "San Francisco", "lat": 37.6213, "lon": -122.3790, "remote": False},
        "GRU": {"name": "Sao Paulo Guarulhos", "lat": -23.4356, "lon": -46.4731, "remote": False},
        "CGH": {"name": "Sao Paulo Congonhas", "lat": -23.6261, "lon": -46.6564, "remote": False},
        "GIG": {"name": "Rio de Janeiro Galeao", "lat": -22.8099, "lon": -43.2506, "remote": False},
        "SDU": {"name": "Rio de Janeiro Santos Dumont", "lat": -22.9105, "lon": -43.1631, "remote": False},
        "EZE": {"name": "Buenos Aires Ezeiza", "lat": -34.8222, "lon": -58.5358, "remote": False},
        "AEP": {"name": "Buenos Aires Aeroparque", "lat": -34.5592, "lon": -58.4156, "remote": False},
        "SCL": {"name": "Santiago", "lat": -33.3928, "lon": -70.7856, "remote": False},
        "LIM": {"name": "Lima", "lat": -12.0219, "lon": -77.1143, "remote": False},
        "BOG": {"name": "Bogota", "lat": 4.7016, "lon": -74.1469, "remote": False},
        "MDE": {"name": "Medellin", "lat": 6.1645, "lon": -75.4231, "remote": False},
        "UIO": {"name": "Quito", "lat": -0.1292, "lon": -78.3575, "remote": False},
        "GYE": {"name": "Guayaquil", "lat": -2.1574, "lon": -79.8836, "remote": False},
        "PTY": {"name": "Panama City Tocumen", "lat": 9.0714, "lon": -79.3835, "remote": False},
        "SJO": {"name": "San Jose Costa Rica", "lat": 9.9939, "lon": -84.2088, "remote": False},
        "HAV": {"name": "Havana", "lat": 22.9892, "lon": -82.4091, "remote": False},
        "SDQ": {"name": "Santo Domingo", "lat": 18.4297, "lon": -69.6689, "remote": False},
        "SJU": {"name": "San Juan", "lat": 18.4394, "lon": -66.0018, "remote": False},
        "KEF": {"name": "Reykjavik Keflavik", "lat": 63.9850, "lon": -22.6056, "remote": True},
        "GOH": {"name": "Nuuk", "lat": 64.1909, "lon": -51.6781, "remote": True},
    }
)

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
    "YYQ",
    "YRT",
    "YCB",
    "YEV",
}

DIRECT_SERVICE_HUBS = {"YYZ", "YUL", "YVR", "YYC", "YEG", "YWG", "YHZ", "YOW"}
DIRECT_SERVICE_HUBS.update(
    {
        "ATL",
        "LAX",
        "ORD",
        "DFW",
        "DEN",
        "JFK",
        "EWR",
        "BOS",
        "MIA",
        "CLT",
        "IAH",
        "SEA",
        "SFO",
        "PHX",
        "MSP",
        "DTW",
        "LAS",
        "ANC",
        "MEX",
        "GDL",
        "MTY",
        "CUN",
        "LHR",
        "CDG",
        "AMS",
        "FRA",
        "MUC",
        "MAD",
        "FCO",
        "IST",
        "SVO",
        "CAI",
        "CMN",
        "ADD",
        "NBO",
        "JNB",
        "DOH",
        "DXB",
        "RUH",
        "DEL",
        "BOM",
        "BKK",
        "SIN",
        "KUL",
        "HKG",
        "ICN",
        "NRT",
        "HND",
        "PEK",
        "PVG",
        "CAN",
        "SYD",
        "MEL",
        "AKL",
        "GRU",
        "EZE",
        "SCL",
        "LIM",
        "BOG",
        "PTY",
    }
)
DIRECT_AIRPORTS.update(AIRPORTS.keys())

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
        ("YYQ", "YWG"),
        ("YRT", "YWG"),
        ("YRT", "YFB"),
        ("YCB", "YZF"),
        ("YCB", "YRT"),
        ("YEV", "YZF"),
        ("YEV", "YXY"),
    ]
)


def _setup_haversine_km(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> float:
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


for airport_code in DIRECT_AIRPORTS - DIRECT_SERVICE_HUBS:
    nearest_hubs = sorted(
        (
            (
                hub_code,
                _setup_haversine_km(
                    AIRPORTS[airport_code]["lat"],
                    AIRPORTS[airport_code]["lon"],
                    AIRPORTS[hub_code]["lat"],
                    AIRPORTS[hub_code]["lon"],
                ),
            )
            for hub_code in DIRECT_SERVICE_HUBS
        ),
        key=lambda item: item[1],
    )
    for hub_code, distance_km in nearest_hubs[:3]:
        if distance_km <= 1800 or AIRPORTS[airport_code]["remote"]:
            DIRECT_FLIGHT_PAIRS.add(frozenset((airport_code, hub_code)))

ROUTING_MODEL_VERSION = "|".join(
    [
        "worldwide-air-routing-v1",
        *(
            f"{code}:{airport['lat']}:{airport['lon']}:{airport['remote']}"
            for code, airport in sorted(AIRPORTS.items())
        ),
        f"direct:{','.join(sorted(DIRECT_AIRPORTS))}",
        f"hubs:{','.join(sorted(DIRECT_SERVICE_HUBS))}",
        f"routes:{','.join(sorted('-'.join(sorted(pair)) for pair in DIRECT_FLIGHT_PAIRS))}",
    ]
)

WORLD_BOUNDS = {
    "min_lat": -56.0,
    "max_lat": 84.0,
    "min_lon": -180.0,
    "max_lon": 180.0,
}
CELL_STEP_DEGREES = 1.0
CELL_DATA_VERSION = "worldwide-cell-landmask-v2"

ALASKA_HIGHWAY_CORRIDOR = [
    [60.7096, -135.0673],
    [60.4883, -133.2787],
    [60.1666, -132.7429],
    [60.0640, -128.7089],
    [59.7150, -127.1430],
    [59.4210, -126.0960],
    [58.9260, -125.7660],
    [58.8053, -122.6972],
]

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

UNITED_STATES_POLYGONS = [
    [
        (-124.8, 48.9),
        (-122.8, 48.2),
        (-122.3, 47.4),
        (-124.0, 46.2),
        (-124.4, 43.8),
        (-124.2, 41.9),
        (-122.4, 40.0),
        (-122.5, 38.0),
        (-121.8, 36.8),
        (-119.8, 34.3),
        (-117.1, 32.5),
        (-114.7, 32.5),
        (-111.0, 31.3),
        (-106.5, 31.8),
        (-104.9, 30.0),
        (-101.5, 29.8),
        (-97.0, 25.9),
        (-95.0, 28.6),
        (-90.5, 29.0),
        (-88.0, 30.2),
        (-85.0, 29.7),
        (-82.1, 27.5),
        (-80.1, 25.1),
        (-80.0, 27.0),
        (-81.0, 30.7),
        (-80.2, 32.2),
        (-77.0, 34.7),
        (-75.3, 36.5),
        (-75.0, 39.5),
        (-70.5, 42.8),
        (-67.0, 44.6),
        (-69.6, 45.0),
        (-73.2, 45.0),
        (-79.0, 43.2),
        (-83.0, 42.0),
        (-88.0, 47.8),
        (-95.0, 49.0),
        (-124.8, 48.9),
    ],
    [
        (-170.0, 52.0),
        (-160.0, 54.0),
        (-152.0, 56.0),
        (-141.0, 59.8),
        (-141.0, 70.0),
        (-156.0, 71.0),
        (-166.0, 68.0),
        (-170.0, 63.0),
        (-168.0, 58.0),
        (-170.0, 52.0),
    ],
]

MEXICO_POLYGONS = [
    [
        (-117.2, 32.5),
        (-114.7, 32.5),
        (-111.0, 31.3),
        (-106.5, 31.8),
        (-104.9, 30.0),
        (-101.5, 29.8),
        (-97.1, 25.9),
        (-94.5, 18.5),
        (-90.5, 18.0),
        (-87.0, 21.6),
        (-86.7, 18.7),
        (-90.2, 18.5),
        (-91.5, 17.1),
        (-94.0, 16.0),
        (-96.5, 15.7),
        (-98.5, 16.0),
        (-101.0, 17.0),
        (-103.5, 18.4),
        (-105.7, 20.0),
        (-107.5, 22.5),
        (-110.0, 24.0),
        (-112.2, 26.0),
        (-114.7, 27.7),
        (-117.2, 32.5),
    ],
    [
        (-117.2, 32.5),
        (-116.0, 31.5),
        (-114.8, 30.0),
        (-113.5, 28.0),
        (-112.0, 26.0),
        (-110.8, 23.0),
        (-109.6, 22.8),
        (-110.5, 25.0),
        (-112.0, 28.0),
        (-114.0, 31.0),
        (-117.2, 32.5),
    ],
]

WORLD_LAND_POLYGONS = [
    [(-82.0, 12.0), (-79.0, 8.0), (-78.0, 1.0), (-81.0, -5.0), (-79.0, -12.0), (-76.0, -18.0), (-73.0, -35.0), (-70.0, -55.0), (-60.0, -53.0), (-52.0, -34.0), (-42.0, -23.0), (-35.0, -7.0), (-44.0, 0.0), (-50.0, 5.0), (-60.0, 10.0), (-70.0, 12.0), (-82.0, 12.0)],
    [(-11.0, 36.0), (2.0, 50.0), (20.0, 58.0), (40.0, 60.0), (60.0, 55.0), (55.0, 45.0), (35.0, 36.0), (25.0, 31.0), (15.0, 36.0), (3.0, 43.0), (-9.0, 43.0), (-11.0, 36.0)],
    [(-18.0, 35.0), (-6.0, 36.0), (10.0, 34.0), (32.0, 31.0), (44.0, 12.0), (50.0, -1.0), (42.0, -12.0), (35.0, -25.0), (22.0, -35.0), (12.0, -35.0), (5.0, -30.0), (-5.0, -17.0), (-14.0, 5.0), (-18.0, 20.0), (-18.0, 35.0)],
    [(26.0, 40.0), (45.0, 35.0), (60.0, 28.0), (75.0, 20.0), (80.0, 8.0), (78.0, 6.0), (68.0, 22.0), (50.0, 30.0), (35.0, 36.0), (26.0, 40.0)],
    [(55.0, 56.0), (75.0, 70.0), (110.0, 73.0), (145.0, 70.0), (180.0, 66.0), (180.0, 50.0), (145.0, 44.0), (125.0, 35.0), (105.0, 20.0), (98.0, 5.0), (78.0, 6.0), (80.0, 24.0), (60.0, 34.0), (55.0, 56.0)],
    [(95.0, 7.0), (103.0, 0.0), (110.0, -8.0), (120.0, -10.0), (126.0, -4.0), (120.0, 6.0), (108.0, 12.0), (100.0, 18.0), (95.0, 7.0)],
    [(120.0, 15.0), (126.0, 18.0), (130.0, 12.0), (127.0, 5.0), (120.0, 5.0), (120.0, 15.0)],
    [(130.0, 45.0), (142.0, 46.0), (146.0, 42.0), (141.0, 34.0), (132.0, 31.0), (130.0, 36.0), (130.0, 45.0)],
    [(112.0, -10.0), (154.0, -10.0), (154.0, -39.0), (145.0, -44.0), (130.0, -35.0), (113.0, -34.0), (112.0, -10.0)],
    [(165.0, -34.0), (179.0, -34.0), (179.0, -48.0), (166.0, -48.0), (165.0, -34.0)],
    [(-74.0, 59.0), (-58.0, 60.0), (-42.0, 65.0), (-20.0, 76.0), (-28.0, 83.0), (-50.0, 84.0), (-68.0, 78.0), (-74.0, 59.0)],
    [(-26.0, 63.0), (-13.0, 63.0), (-13.0, 67.5), (-26.0, 67.5), (-26.0, 63.0)],
    [(-11.0, 50.0), (2.0, 50.0), (2.0, 59.0), (-8.0, 59.0), (-11.0, 50.0)],
    [(-162.0, 18.0), (-154.0, 18.0), (-154.0, 23.0), (-162.0, 23.0), (-162.0, 18.0)],
    [(175.0, -19.0), (180.0, -19.0), (180.0, -15.0), (175.0, -15.0), (175.0, -19.0)],
]

WORLD_LAND_COVERAGE_POLYGONS = [
    [(-12.0, 35.0), (45.0, 35.0), (45.0, 72.0), (-12.0, 72.0), (-12.0, 35.0)],
    [(25.0, 12.0), (62.0, 12.0), (62.0, 43.0), (25.0, 43.0), (25.0, 12.0)],
    [(-18.0, -35.0), (52.0, -35.0), (52.0, 37.0), (-18.0, 37.0), (-18.0, -35.0)],
    [(45.0, 5.0), (180.0, 5.0), (180.0, 75.0), (45.0, 75.0), (45.0, 5.0)],
    [(90.0, -12.0), (145.0, -12.0), (145.0, 25.0), (90.0, 25.0), (90.0, -12.0)],
    [(112.0, -45.0), (154.0, -45.0), (154.0, -10.0), (112.0, -10.0), (112.0, -45.0)],
    [(165.0, -48.0), (179.0, -48.0), (179.0, -34.0), (165.0, -34.0), (165.0, -48.0)],
    [(-82.0, -56.0), (-34.0, -56.0), (-34.0, 13.0), (-82.0, 13.0), (-82.0, -56.0)],
    [(-74.0, 59.0), (-20.0, 59.0), (-20.0, 84.0), (-74.0, 84.0), (-74.0, 59.0)],
]

LAND_POLYGONS = [
    MAINLAND_POLYGON,
    [(-141.0, 60.0), (-128.0, 60.0), (-128.0, 70.2), (-141.0, 70.2), (-141.0, 60.0)],
    [(-128.8, 50.8), (-125.2, 48.3), (-123.0, 48.3), (-124.5, 50.9), (-127.8, 51.4), (-128.8, 50.8)],
    [(-59.8, 51.8), (-56.0, 52.0), (-52.2, 49.8), (-52.4, 47.0), (-55.5, 46.4), (-58.8, 47.5), (-59.8, 50.0), (-59.8, 51.8)],
    [(-66.4, 45.4), (-65.7, 44.4), (-64.2, 43.4), (-61.0, 43.5), (-59.7, 45.1), (-60.4, 46.4), (-62.4, 46.1), (-64.8, 45.9), (-66.4, 45.4)],
    [(-61.9, 47.1), (-60.0, 47.2), (-59.1, 46.0), (-60.2, 45.3), (-61.5, 45.6), (-61.9, 47.1)],
    [(-67.2, 57.2), (-64.0, 58.6), (-60.0, 58.9), (-56.0, 55.2), (-56.4, 52.0), (-60.3, 52.0), (-63.8, 54.0), (-67.2, 57.2)],
    [(-91.0, 76.0), (-80.0, 72.5), (-65.0, 66.0), (-63.0, 62.0), (-72.0, 62.0), (-85.0, 66.0), (-92.0, 70.5), (-91.0, 76.0)],
    [(-91.0, 62.0), (-63.0, 62.0), (-60.0, 74.5), (-78.0, 76.5), (-91.0, 73.0), (-91.0, 62.0)],
    [(-101.0, 67.0), (-90.0, 67.0), (-90.0, 71.0), (-101.0, 71.0), (-101.0, 67.0)],
    [(-126.0, 68.0), (-100.0, 68.0), (-94.0, 72.5), (-112.0, 76.5), (-126.0, 73.0), (-126.0, 68.0)],
    [(-126.0, 73.0), (-60.0, 73.0), (-60.0, 83.8), (-95.0, 83.8), (-126.0, 78.0), (-126.0, 73.0)],
    [(-125.0, 76.0), (-112.0, 72.0), (-102.0, 72.5), (-100.0, 76.0), (-112.0, 78.0), (-125.0, 76.0)],
    [(-101.0, 80.8), (-86.0, 78.0), (-75.0, 78.8), (-68.0, 81.0), (-78.0, 83.2), (-94.0, 83.0), (-101.0, 80.8)],
    [(-122.0, 73.5), (-114.0, 70.5), (-105.0, 70.0), (-108.0, 73.2), (-116.5, 75.0), (-122.0, 73.5)],
    *UNITED_STATES_POLYGONS,
    *MEXICO_POLYGONS,
    *WORLD_LAND_POLYGONS,
    *WORLD_LAND_COVERAGE_POLYGONS,
]

EXCLUDED_WATER_POLYGONS: list[list[tuple[float, float]]] = []

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
    "Rail + road": "major intercity rail corridors and nearby urban regions",
    "Road": "regional overland travel",
    "Direct flight + ground": "major airport-to-airport service",
    "Connecting flight + ground": "air travel through a hub",
    "Air + remote access": "remote, island, polar, and low-access areas",
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
    route_source: str = ""


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


def is_world_land(lat: float, lon: float) -> bool:
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
        for code in sorted(DIRECT_SERVICE_HUBS):
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
        "Atlanta Hartsfield-Jackson": "Atlanta",
        "Chicago O'Hare": "Chicago",
        "Chicago Midway": "Chicago",
        "Dallas-Fort Worth": "Dallas",
        "Dallas Love Field": "Dallas",
        "New York JFK": "New York",
        "New York LaGuardia": "New York",
        "Newark Liberty": "Newark",
        "Boston Logan": "Boston",
        "Washington National": "Washington",
        "Washington Dulles": "Washington",
        "Baltimore-Washington": "Baltimore",
        "Fort Lauderdale": "Fort Lauderdale",
        "Charlotte Douglas": "Charlotte",
        "Detroit Metro": "Detroit",
        "Minneapolis-Saint Paul": "Minneapolis",
        "Houston Intercontinental": "Houston",
        "Houston Hobby": "Houston",
        "Phoenix Sky Harbor": "Phoenix",
        "Seattle-Tacoma": "Seattle",
        "Felipe Angeles": "Mexico City",
        "Bajio": "Leon",
        "Ciudad Juarez": "Juarez",
        "Cleveland Hopkins": "Cleveland",
        "Cincinnati-Northern Kentucky": "Cincinnati",
        "Buffalo Niagara": "Buffalo",
        "Hartford Bradley": "Hartford",
        "Portland Maine": "Portland",
        "Greenville-Spartanburg": "Greenville-Spartanburg",
        "Reno-Tahoe": "Reno",
        "Burbank": "Los Angeles",
        "Long Beach": "Los Angeles",
        "Ontario California": "Ontario",
        "Orange County": "Orange County",
        "Northwest Arkansas": "Northwest Arkansas",
        "Ixtapa-Zihuatanejo": "Ixtapa-Zihuatanejo",
        "Puerto Escondido": "Puerto Escondido",
        "Tuxtla Gutierrez": "Tuxtla Gutierrez",
        "London Heathrow": "London",
        "London Gatwick": "London",
        "Paris Charles de Gaulle": "Paris",
        "Paris Orly": "Paris",
        "Amsterdam Schiphol": "Amsterdam",
        "Rome Fiumicino": "Rome",
        "Milan Malpensa": "Milan",
        "Berlin Brandenburg": "Berlin",
        "Stockholm Arlanda": "Stockholm",
        "Madrid Barajas": "Madrid",
        "Warsaw Chopin": "Warsaw",
        "Moscow Sheremetyevo": "Moscow",
        "Moscow Domodedovo": "Moscow",
        "Tel Aviv Ben Gurion": "Tel Aviv",
        "Delhi": "Delhi",
        "Bangkok Suvarnabhumi": "Bangkok",
        "Bangkok Don Mueang": "Bangkok",
        "Singapore Changi": "Singapore",
        "Kuala Lumpur": "Kuala Lumpur",
        "Taipei Taoyuan": "Taipei",
        "Seoul Incheon": "Seoul",
        "Seoul Gimpo": "Seoul",
        "Tokyo Narita": "Tokyo",
        "Tokyo Haneda": "Tokyo",
        "Osaka Kansai": "Osaka",
        "Sapporo New Chitose": "Sapporo",
        "Beijing Capital": "Beijing",
        "Beijing Daxing": "Beijing",
        "Shanghai Pudong": "Shanghai",
        "Shanghai Hongqiao": "Shanghai",
        "Chengdu Shuangliu": "Chengdu",
        "Chengdu Tianfu": "Chengdu",
        "Sao Paulo Guarulhos": "Sao Paulo",
        "Sao Paulo Congonhas": "Sao Paulo",
        "Rio de Janeiro Galeao": "Rio de Janeiro",
        "Rio de Janeiro Santos Dumont": "Rio de Janeiro",
        "Buenos Aires Ezeiza": "Buenos Aires",
        "Buenos Aires Aeroparque": "Buenos Aires",
        "Panama City Tocumen": "Panama City",
        "San Jose Costa Rica": "San Jose",
        "Reykjavik Keflavik": "Reykjavik",
    }
    name = str(airport["name"])
    return replacements.get(name, name)


def origin_location_options() -> dict[str, tuple[float, float]]:
    options: dict[str, tuple[float, float]] = {
        name.split(",")[0]: coordinates for name, coordinates in WORLD_LOCATIONS.items()
    }

    for airport in AIRPORTS.values():
        options.setdefault(airport_city_name(airport), (airport["lat"], airport["lon"]))

    return dict(sorted(options.items(), key=lambda item: item[0].casefold()))


def nearby_airport_label(lat: float, lon: float, threshold_km: float = 20) -> str | None:
    candidates = sorted_airport_access_candidates(round(lat, 4), round(lon, 4))
    if not candidates:
        return None

    code, distance_km = candidates[0]
    airport = AIRPORTS[code]
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


def openrouteservice_api_key() -> str:
    try:
        secret_key = st.secrets.get("OPENROUTESERVICE_API_KEY", "")
    except Exception:
        secret_key = ""
    return str(secret_key or os.getenv("OPENROUTESERVICE_API_KEY", "")).strip()


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def fetch_openrouteservice_drive_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    api_key: str,
) -> dict[str, object] | None:
    if not api_key:
        return None

    payload = json.dumps(
        {
            "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
            "instructions": False,
        }
    ).encode("utf-8")
    request = Request(
        "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
        data=payload,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, application/geo+json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    features = data.get("features") or []
    if not features:
        return None

    feature = features[0]
    geometry = feature.get("geometry", {})
    coordinates = geometry.get("coordinates", [])
    summary = feature.get("properties", {}).get("summary", {})
    if not coordinates or "duration" not in summary or "distance" not in summary:
        return None

    return {
        "path": coordinates,
        "hours": float(summary["duration"]) / 3600,
        "distance_km": float(summary["distance"]) / 1000,
    }


def path_distance_km(path: list[list[float]]) -> float:
    distance = 0.0
    for start, end in zip(path, path[1:]):
        distance += haversine_km(start[1], start[0], end[1], end[0])
    return distance


def alaska_highway_fallback_path(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> list[list[float]] | None:
    in_corridor = (
        58.0 <= start_lat <= 61.2
        and 58.0 <= end_lat <= 61.2
        and -136.0 <= start_lon <= -122.0
        and -136.0 <= end_lon <= -122.0
    )
    spans_corridor = abs(start_lon - end_lon) >= 3.0
    if not in_corridor or not spans_corridor:
        return None

    west_to_east = start_lon < end_lon
    low_lon = min(start_lon, end_lon)
    high_lon = max(start_lon, end_lon)
    waypoints = [
        [lon, lat]
        for lat, lon in ALASKA_HIGHWAY_CORRIDOR
        if low_lon < lon < high_lon
    ]
    if not west_to_east:
        waypoints.reverse()

    if not waypoints:
        return None

    return [[start_lon, start_lat], *waypoints, [end_lon, end_lat]]


def drive_route_details(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    fallback_hours: float,
    fallback_distance_km: float,
) -> tuple[list[list[float]], float, float, str]:
    ors_route = fetch_openrouteservice_drive_route(
        round(start_lat, 6),
        round(start_lon, 6),
        round(end_lat, 6),
        round(end_lon, 6),
        openrouteservice_api_key(),
    )
    if ors_route:
        return (
            ors_route["path"],
            float(ors_route["hours"]),
            float(ors_route["distance_km"]),
            "OpenRouteService",
        )

    fallback_path = alaska_highway_fallback_path(start_lat, start_lon, end_lat, end_lon)
    if fallback_path:
        fallback_path_distance = path_distance_km(fallback_path)
        return (
            fallback_path,
            max(fallback_hours, fallback_path_distance / 75),
            fallback_path_distance,
            "Modeled Alaska Highway corridor",
        )

    return (
        route_path(start_lat, start_lon, end_lat, end_lon),
        fallback_hours,
        fallback_distance_km,
        "Modeled straight-line fallback",
    )


def has_direct_service(origin_code: str, destination_code: str) -> bool:
    if origin_code == destination_code:
        return False
    return frozenset((origin_code, destination_code)) in DIRECT_FLIGHT_PAIRS


@lru_cache(maxsize=None)
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


@lru_cache(maxsize=None)
def best_connection_hub(origin_code: str, destination_code: str) -> tuple[str, dict[str, object], float] | None:
    candidates = []

    for hub_code in sorted(DIRECT_SERVICE_HUBS):
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


@lru_cache(maxsize=None)
def _compute_flight_itinerary_hours(origin_code: str, destination_code: str) -> tuple[bool, str | None, float]:
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


def compute_airport_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "code": code,
            "name": airport["name"],
            "lat": airport["lat"],
            "lon": airport["lon"],
            "remote": airport["remote"],
            "direct_airport": code in DIRECT_AIRPORTS,
            "direct_service_hub": code in DIRECT_SERVICE_HUBS,
        }
        for code, airport in sorted(AIRPORTS.items())
    )


def compute_flight_route_table() -> pd.DataFrame:
    rows = []

    for origin_code, origin_airport in AIRPORTS.items():
        for destination_code, destination_airport in AIRPORTS.items():
            direct_service, hub_code, flight_hours = _compute_flight_itinerary_hours(origin_code, destination_code)
            if not math.isfinite(flight_hours):
                continue

            rows.append(
                {
                    "origin_code": origin_code,
                    "origin_name": origin_airport["name"],
                    "destination_code": destination_code,
                    "destination_name": destination_airport["name"],
                    "direct_service": direct_service,
                    "hub_code": hub_code or "",
                    "flight_hours": flight_hours,
                    "airport_distance_km": 0
                    if origin_code == destination_code
                    else airport_distance_km(origin_code, destination_code),
                    "itinerary_type": "same airport"
                    if origin_code == destination_code
                    else "direct"
                    if direct_service
                    else "connecting",
                }
            )

    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def load_cached_flight_route_table(csv_path: str, routing_model_version: str) -> pd.DataFrame:
    _ = routing_model_version
    route_table = pd.read_csv(csv_path, keep_default_na=False)
    if route_table["direct_service"].dtype != bool:
        route_table["direct_service"] = route_table["direct_service"].map(
            lambda value: str(value).strip().casefold() == "true"
        )
    route_table["flight_hours"] = route_table["flight_hours"].astype(float)
    route_table["airport_distance_km"] = route_table["airport_distance_km"].astype(float)
    return route_table


@st.cache_data(show_spinner=False)
def build_flight_route_table(routing_model_version: str) -> pd.DataFrame:
    if FLIGHT_ROUTE_CACHE_CSV.exists():
        return load_cached_flight_route_table(str(FLIGHT_ROUTE_CACHE_CSV), routing_model_version)

    _ = routing_model_version
    return compute_flight_route_table()


@lru_cache(maxsize=8)
def flight_route_index(routing_model_version: str) -> dict[tuple[str, str], tuple[bool, str | None, float]]:
    route_table = build_flight_route_table(routing_model_version)
    return {
        (row.origin_code, row.destination_code): (
            bool(row.direct_service),
            str(row.hub_code) or None,
            float(row.flight_hours),
        )
        for row in route_table.itertuples(index=False)
    }


@lru_cache(maxsize=None)
def origin_airport_route_options(origin_code: str, routing_model_version: str) -> dict[str, tuple[bool, str | None, float]]:
    return {
        destination_code: route
        for (cached_origin_code, destination_code), route in flight_route_index(routing_model_version).items()
        if cached_origin_code == origin_code
    }


def flight_itinerary_hours(origin_code: str, destination_code: str) -> tuple[bool, str | None, float]:
    return flight_route_index(ROUTING_MODEL_VERSION).get(
        (origin_code, destination_code),
        (False, None, float("inf")),
    )


@lru_cache(maxsize=250000)
def sorted_airport_access_candidates(lat: float, lon: float) -> tuple[tuple[str, float], ...]:
    return tuple(
        sorted(
            (
                (
                    destination_code,
                    haversine_km(lat, lon, destination_airport["lat"], destination_airport["lon"]),
                )
                for destination_code, destination_airport in AIRPORTS.items()
            ),
            key=lambda item: item[1],
        )
    )


def destination_airport_candidates(
    lat: float,
    lon: float,
    direct_distance_km: float,
) -> list[tuple[str, dict[str, object], float]]:
    candidates = [
        (
            destination_code,
            AIRPORTS[destination_code],
            destination_access_km,
        )
        for destination_code, destination_access_km in sorted_airport_access_candidates(round(lat, 4), round(lon, 4))
    ]
    if direct_distance_km < 420:
        return [candidate for candidate in candidates if candidate[2] <= 140][:10]
    return candidates[:16 if lat >= 58 else 12]


def best_air_route(origin: Place, lat: float, lon: float, direct_distance_km: float) -> AirRouteCandidate | None:
    origin_code, origin_airport, origin_access_km = nearest_airport(origin.lat, origin.lon, prefer_hub=True)
    origin_access_hours = airport_access_hours(origin_access_km, origin.lat)
    origin_routes = origin_airport_route_options(origin_code, ROUTING_MODEL_VERSION)
    candidates: list[AirRouteCandidate] = []

    for destination_code, destination_airport, destination_access_km in destination_airport_candidates(
        lat,
        lon,
        direct_distance_km,
    ):
        if direct_distance_km < 420 and destination_access_km > 70:
            continue

        destination_access_hours = destination_ground_hours(destination_access_km, lat)
        direct_service, hub_code, flight_hours = origin_routes.get(destination_code, (False, None, float("inf")))
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

    in_corridor = (
        (42.0 <= lat <= 48.2 and -84.5 <= lon <= -69.5)
        or (38.0 <= lat <= 42.8 and -77.5 <= lon <= -71.0)
        or (32.0 <= lat <= 38.5 and -122.8 <= lon <= -117.0)
        or (45.0 <= lat <= 56.0 and -5.5 <= lon <= 16.5)
        or (35.0 <= lat <= 45.5 and 135.0 <= lon <= 141.5)
        or (28.0 <= lat <= 32.5 and 103.0 <= lon <= 122.5)
    )
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

    for name, coordinates in WORLD_LOCATIONS.items():
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
        origin_access_path, origin_access_hours, origin_access_km, origin_access_source = drive_route_details(
            origin.lat,
            origin.lon,
            origin_airport["lat"],
            origin_airport["lon"],
            origin_access_hours,
            origin_access_km,
        )
        destination_drive_path, destination_access_hours, destination_access_km, destination_drive_source = drive_route_details(
            destination_airport["lat"],
            destination_airport["lon"],
            destination.lat,
            destination.lon,
            destination_access_hours,
            destination_access_km,
        )
        legs = [
            RouteLeg(
                mode="Ground access",
                start_name=origin.name,
                end_name=f"{origin_airport['name']} ({origin_code})",
                hours=origin_access_hours,
                distance_km=origin_access_km,
                path=origin_access_path,
                color=[88, 88, 88, 230],
                route_source=origin_access_source,
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
                path=destination_drive_path,
                color=[213, 94, 0, 235],
                route_source=destination_drive_source,
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

    leg_path = route_path(origin.lat, origin.lon, destination.lat, destination.lon)
    leg_hours = estimate.hours
    leg_distance_km = direct_distance_km
    leg_source = ""
    if estimate.mode == "Road":
        leg_path, leg_hours, leg_distance_km, leg_source = drive_route_details(
            origin.lat,
            origin.lon,
            destination.lat,
            destination.lon,
            estimate.hours,
            direct_distance_km,
        )

    leg = RouteLeg(
        mode=estimate.mode,
        start_name=origin.name,
        end_name=destination.name,
        hours=leg_hours,
        distance_km=leg_distance_km,
        path=leg_path,
        color=[0, 150, 136, 235] if estimate.mode == "Rail + road" else [213, 94, 0, 235],
        route_source=leg_source,
    )
    return RoutePlan(
        destination=destination,
        total_hours=leg_hours,
        total_distance_km=leg_distance_km,
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
    lat = WORLD_BOUNDS["min_lat"]

    while lat <= WORLD_BOUNDS["max_lat"]:
        lon = WORLD_BOUNDS["min_lon"]
        while lon <= WORLD_BOUNDS["max_lon"]:
            if is_world_land(lat, lon):
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
    for name, (lat, lon) in WORLD_LOCATIONS.items():
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
    for name, (lat, lon) in WORLD_LOCATIONS.items():
        city = name.split(",")[0]
        rows.append(
            {
                "name": name,
                "label": city,
                "lat": lat,
                "lon": lon,
                "size": 15
                if name
                in {
                    "Toronto, ON",
                    "Montreal, QC",
                    "Vancouver, BC",
                    "Calgary, AB",
                    "New York, NY",
                    "Los Angeles, CA",
                    "Chicago, IL",
                    "Houston, TX",
                    "Mexico City, CMX",
                    "Guadalajara, JAL",
                    "Monterrey, NLE",
                    "London, UK",
                    "Paris, FR",
                    "Tokyo, JP",
                    "Singapore, SG",
                    "Dubai, AE",
                    "Sydney, AU",
                    "Sao Paulo, BR",
                    "Buenos Aires, AR",
                    "Johannesburg, ZA",
                }
                else 12,
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
            "route_source": leg.route_source,
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
        initial_view_state=pdk.ViewState(latitude=20.0, longitude=10.0, zoom=1.2, pitch=0),
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
            min_value=WORLD_BOUNDS["min_lat"],
            max_value=WORLD_BOUNDS["max_lat"],
            value=city_lat,
            format="%.6f",
        )
        lon = st.sidebar.number_input(
            "Longitude",
            min_value=WORLD_BOUNDS["min_lon"],
            max_value=WORLD_BOUNDS["max_lon"],
            value=city_lon,
            format="%.6f",
        )
        origin_name = "Custom origin"
    else:
        lat, lon = city_lat, city_lon
        origin_name = location_name

    st.sidebar.header("Destination")
    destination_name = st.sidebar.selectbox(
        "Destination city",
        options=[""] + list(origin_options),
        index=0,
        format_func=lambda option: "Select a destination..." if option == "" else option,
    )
    destination = None
    if destination_name:
        destination_lat, destination_lon = origin_options[destination_name]
        destination = Place(name=destination_name, lat=float(destination_lat), lon=float(destination_lon))

    return {
        "origin": Place(name=origin_name, lat=float(lat), lon=float(lon)),
        "destination": destination,
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
    st.set_page_config(page_title="Worldwide Isochronic Passage Chart", page_icon="W", layout="wide")
    st.title("Worldwide Isochronic Passage Chart")

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
    route_plan = (
        build_route_plan(origin, controls["destination"])
        if controls["destination"]
        else route_plan_from_selection(origin)
    )

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
