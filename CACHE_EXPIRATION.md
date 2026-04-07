# Cache Expiration Guide

## Overview

Artemis II implements **Cache Expiration (TTL - Time-To-Live)** for all cached API data. This ensures data freshness while allowing offline operation.

## Configuration

Cache expiration times are defined in `artemis/config.py`:

```python
CACHE_EXPIRATION = {
    "spacecraft": 120,          # 2 minutes
    "dsn": 30,                  # 30 seconds  
    "weather": 600,             # 10 minutes
    "donki": 1800,              # 30 minutes
    "trajectory": 1200,         # 20 minutes
    "photo": 86400,             # 24 hours
}
```

## Expiration Times Explained

### Spacecraft (120 seconds = 2 minutes)
- **Why**: Critical real-time telemetry for mission-critical data
- **Polling interval**: Every 60 seconds
- **Impact**: Shows latest position, velocity, distance

### DSN (30 seconds)
- **Why**: Communications are high-priority and change frequently
- **Polling interval**: Every 10 seconds  
- **Impact**: Reflects active dish tracking in near real-time

### Weather (600 seconds = 10 minutes)
- **Why**: Solar wind and space weather is relatively stable
- **Polling interval**: Every 300 seconds
- **Impact**: Kp index, wind speed, aurora forecasts

### DONKI Events (1800 seconds = 30 minutes)
- **Why**: Space events (flares, CMEs) change slowly
- **Polling interval**: Every 900 seconds
- **Impact**: Solar flare alerts, CME predictions

### Trajectory (1200 seconds = 20 minutes)
- **Why**: Orbital mechanics are highly predictable
- **Polling interval**: Every 600 seconds
- **Impact**: Full mission path visualization

### Photo (86400 seconds = 24 hours)
- **Why**: Mission photos update infrequently
- **Polling interval**: Every 3600 seconds
- **Impact**: Latest mission photo display

## Checking Cache Status

Use the `check_cache.py` script to see which cache files are fresh or expired:

```bash
python check_cache.py
```

Output example:
```
📦 ARTEMIS II - CACHE STATUS

======================================================================
Spacecraft              45s /   120s  🟢 FRESH
DSN                      3s /    30s  🟢 FRESH
Weather                 45s /   600s  🟢 FRESH
DONKI Events            45s /  1800s  🟢 FRESH
Trajectory              38s /  1200s  🟢 FRESH
Photo                   46s / 86400s  🟢 FRESH
======================================================================
```

- **Column 1**: Data type name
- **Column 2**: Time since last cache write (seconds)
- **Column 3**: TTL (expiration time in seconds)
- **Column 4**: Status (🟢 FRESH = still valid, 🔴 EXPIRED = needs refresh)

## Behavior on Expiration

### With Network Available
1. Application detects cache is expired
2. Fetches fresh data from API
3. Updates cache files
4. Displays new data with current timestamp

### Without Network
1. Application detects cache is expired
2. Attempts to fetch from API (fails)
3. Falls back to cached data
4. Marks data as "stale" in UI status bar

## Customizing Expiration Times

To change cache TTL values:

1. Edit `artemis/config.py`
2. Modify the `CACHE_EXPIRATION` dictionary
3. Example: To keep spacecraft cache for 5 minutes instead of 2:
   ```python
   CACHE_EXPIRATION = {
       "spacecraft": 300,  # Changed from 120
       # ... other values ...
   }
   ```
4. Restart the application

## Clearing Cache

To clear all cached data and force fresh API fetches:

```bash
# Windows PowerShell
Remove-Item cache\*.json, cache\*.bin -Force

# Unix/Linux/macOS
rm cache/*.json cache/*.bin
```

## Implementation Details

### Cache Loading Functions
Located in `artemis/cache.py`:
- `is_cache_expired(cache_file, cache_key)` - Check if file has expired
- `get_cache_age_seconds(cache_file)` - Get current age
- `load_spacecraft()` - Load if not expired
- `load_dsn()` - Load if not expired
- `load_weather()` - Load if not expired
- `load_donki()` - Load if not expired
- `load_trajectory()` - Load if not expired
- `load_photo()` - Load if not expired

### Age Calculation
Cache age is calculated from file modification time:
```python
age = now.timestamp() - file_mtime.timestamp()
is_expired = age > CACHE_EXPIRATION[key]
```

### Persistence
- Cache files include `fetched_at` timestamp (when API data was retrieved)
- File modification time (when cache was written) determines expiration
- Different from API data timestamp

## Performance Impact

- **Spacecraft sync**: +45-50ms to check expiration (file stat)
- **All data types**: ~5-10ms per check
- **Negligible** compared to 1-second render interval

## Future Enhancements

Possible improvements:
- Adaptive expiration based on data quality
- Partial updates (update only expired sources)
- Cache warming on startup
- Compression for large trajectory data
- SQLite cache backend for better querying
