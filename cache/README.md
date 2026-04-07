# Artemis II Cache Directory

This directory contains cached API data to support offline operation and reduce API calls.

## Cache Files

- **spacecraft.json** - Current Orion and Moon position, distance, and velocity data
- **dsn.json** - Deep Space Network dish tracking information  
- **weather.json** - Space weather data (Kp index, solar wind, NOAA scales)
- **donki.json** - Space weather events (CMEs, solar flares, geomagnetic storms)
- **trajectory.json** - Full mission trajectory (Orion and Moon positions over time)
- **photo.bin** - Latest mission photo (binary image data)
- **photo_meta.json** - Mission photo metadata (title, URL, date)

## Cache Format

All cache files use JSON format (except photo.bin which is binary) for easy inspection and manual editing if needed.

Each cached data object includes a `fetched_at` timestamp indicating when the data was last retrieved from the API.

## Cache Expiration

Cache files have TTL (Time-To-Live) and are considered expired after:

| Data Type | Expiration | Reason |
|-----------|------------|--------|
| Spacecraft | 2 minutes (120s) | High-priority real-time telemetry |
| DSN | 30 seconds | Near real-time communications |
| Weather | 10 minutes (600s) | Solar wind is relatively stable |
| DONKI Events | 30 minutes (1800s) | Space events change slowly |
| Trajectory | 20 minutes (1200s) | Orbital mechanics stable over time |
| Photo | 24 hours (86400s) | Mission photos update infrequently |

**Behavior**: When cache expires, the application will fetch fresh data from APIs if available. If network is unavailable, old cached data is still used but marked as stale.

## Auto-Update

Cache files are automatically updated when the application fetches fresh data from the APIs:
- Spacecraft: every 60 seconds (HORIZONS_INTERVAL)
- DSN: every 10 seconds (DSN_INTERVAL)
- Weather: every 300 seconds (SWPC_INTERVAL)
- DONKI events: every 900 seconds (DONKI_INTERVAL)
- Trajectory: every 600 seconds (TRAJECTORY_REFRESH_INTERVAL)
- Photos: every 3600 seconds (NASA_IMAGES_INTERVAL)

## Trajectory History

Trajectory history files are automatically saved in `trajectory_history/` directory:

```
cache/trajectory_history/
├── trajectory_2026-04-07_11-43-23.json  (189 KB)
├── trajectory_2026-04-07_12-04-15.json  (189 KB)
└── trajectory_2026-04-07_12-24-42.json  (189 KB)
```

See **[TRAJECTORY_HISTORY.md](../TRAJECTORY_HISTORY.md)** for full documentation.

### Quick Commands
```bash
# Show statistics
python check_trajectory_history.py stats

# List recent files
python check_trajectory_history.py list

# Show trajectory details
python check_trajectory_history.py show

# Clean up old files (keep last 100)
python check_trajectory_history.py cleanup
```

## Manual Cache Management

To clear all cached data:
```bash
rm -r cache/*
```

To view a specific cache file:
```bash
cat cache/spacecraft.json
```
