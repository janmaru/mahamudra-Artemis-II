from datetime import datetime, timezone, timedelta

# Spacecraft
SPACECRAFT_ID = "-1024"
SPACECRAFT_NAME = "Orion"
SPACECRAFT_CALLSIGN = "Integrity"
DSN_SPACECRAFT_CODE = "EM2"

# Mission launch time (UTC) — used for MET, flight day, and phase detection
# Actual liftoff: April 1 2026 at 6:35 PM EDT = 22:35 UTC
LAUNCH_TIME = datetime(2026, 4, 1, 22, 35, 0, tzinfo=timezone.utc)

# API URLs
HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
DSN_URL = "https://eyes.nasa.gov/dsn/data/dsn.xml"
SWPC_KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
SWPC_PLASMA_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-5-minute.json"
SWPC_MAG_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-5-minute.json"
SWPC_SCALES_URL = "https://services.swpc.noaa.gov/products/noaa-scales.json"
DONKI_BASE_URL = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/"
NASA_IOTD_URL = "https://www.nasa.gov/feeds/iotd-feed/"

# Polling intervals (seconds)
HORIZONS_INTERVAL = 60
DSN_INTERVAL = 10
SWPC_INTERVAL = 300
DONKI_INTERVAL = 900
TRAJECTORY_REFRESH_INTERVAL = 600
NASA_IMAGES_INTERVAL = 3600

# Cache expiration times (seconds)
# Cache is considered fresh if last_fetch + EXPIRATION < now
# If cache expires, old data is still used but marked as stale
CACHE_EXPIRATION = {
    "spacecraft": 120,          # 2 minutes (more conservative than API call)
    "dsn": 30,                  # 30 seconds
    "weather": 600,             # 10 minutes
    "donki": 1800,              # 30 minutes
    "trajectory": 1200,         # 20 minutes
    "photo": 86400,             # 24 hours
}

# Network
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3

# Display
RENDER_INTERVAL = 1.0
KM_TO_MILES = 0.621371

# DSN station friendly names
DSN_STATIONS = {
    "gdscc": "Goldstone",
    "mdscc": "Madrid",
    "cdscc": "Canberra",
}

# DSN Dish sizes (m)
DSN_DISH_SIZES = {
    "DSS14": 70,
    "DSS43": 70,
    "DSS63": 70,
    "DSS35": 34,
    "DSS36": 34,
    "DSS34": 34,
    "DSS24": 34,
    "DSS25": 34,
    "DSS26": 34,
    "DSS54": 34,
    "DSS55": 34,
    "DSS65": 34,
    "DSS13": 26,
}

# Mission timeline — actual event times (UTC)
MISSION_TIMELINE = [
    ("TLI", datetime(2026, 4, 2, 23, 49, 0, tzinfo=timezone.utc)),
    ("Lunar Flyby", datetime(2026, 4, 6, 23, 0, 0, tzinfo=timezone.utc)),
    ("Entry Interface", datetime(2026, 4, 10, 23, 53, 0, tzinfo=timezone.utc)),
    ("Splashdown", datetime(2026, 4, 11, 0, 7, 0, tzinfo=timezone.utc)),
]
