# Artemis-II Python Viewer

A real-time Python terminal dashboard for NASA's **Artemis II** crewed mission to the Moon. Fetches live spacecraft telemetry, trajectory data, Deep Space Network communications, and space weather -- all from public NASA/JPL/NOAA APIs (no authentication required).

## Screenshot

```
 ARTEMIS II - ORION "INTEGRITY"
 MET: 05d 03h 48m 27s  |  Flight Day 6  |  Phase: Lunar Flyby

 ARTEMIS II TRAJECTORY                    SPACECRAFT
                                          Earth Distance  410,711 km (255,204 mi)
                                          Moon Distance    13,169 km (8,183 mi)
            · · · · · ·                   Speed           0.453 km/s (1,632 km/h)
          · · ·     · · · ·              Pos (x1000 km)  -128 / -388 / -36
                Moon    · · ·
                  Orion                   DSN COMMUNICATIONS
                                          Station   Dish    Down       Up   RTLT
                                          Canberra  DSS34   6.0 Mbps  -    2.71s
                                          Canberra  DSS43   -         -    2.71s
 MET 05d 03h 48m | Earth 410,711 km                 Range: 406,000 km
 Orion 13,169 km Moon | 0.453 km/s                        Updated 1s ago
 Updated 11s ago

 SPACE WEATHER                            ALERTS & EVENTS
 Kp Index       2.3 (Quiet)              [*] CME HA=16.0    2026-04-05 01:48
 NOAA Scales    G0  S0  R0               [!] Solar Flare M1.0  2026-04-04 22:54
 Wind Speed     518 km/s                 [!] Solar Flare M1.2  2026-04-04 11:58
 Wind Density   1.4 p/cm3               [*] CME HA=15.0    2026-04-04 07:53
 IMF Bz        -1.1 nT                  [S] Geomag. Storm Kp=6.67  2026-04-03
 Wind Temp      82,976 K
 Updated 11s ago

 Horizons: 11s | DSN: 1s | SWPC: 11s | DONKI: 11s | Traj: 5s
```

## Mission Overview

Artemis II is NASA's first crewed flight of the Orion spacecraft on the Space Launch System (SLS) rocket. The mission sends four astronauts on a ~10-day lunar flyby trajectory, looping around the Moon and returning to Earth.

- **Spacecraft**: Orion (callsign "Integrity")
- **JPL SPKID**: `-1024`
- **Designations**: Orion EM-2, 2026-069A

## Data Sources

| Source | Purpose | Format | Auth |
|--------|---------|--------|------|
| [JPL Horizons API](https://ssd.jpl.nasa.gov/api/horizons.api) | Orion position & velocity vectors | JSON | None |
| [DSN Now](https://eyes.nasa.gov/dsn/data/dsn.xml) | Deep Space Network live comms | XML | None |
| [NOAA SWPC](https://services.swpc.noaa.gov/) | Space weather (Kp, solar wind, aurora) | JSON | None |
| [NASA DONKI](https://kauai.ccmc.gsfc.nasa.gov/DONKI/) | Solar flares, CMEs, geomagnetic storms | JSON | None |

## Caching

All fetched data is automatically cached to JSON and binary files in the `cache/` directory:

- **Automatic updates** - Cache files are refreshed when fetchers retrieve fresh data from APIs
- **Cache expiration (TTL)** - Each data type has a configurable Time-To-Live:
  - Spacecraft: 2 minutes (real-time telemetry priority)
  - DSN: 30 seconds (near real-time comms)
  - Weather: 10 minutes (stable data)
  - DONKI events: 30 minutes
  - Trajectory: 20 minutes
  - Photos: 6 seconds rotation (carousel of up to 10 images)
- **Offline browsing** - View cached data without active network connections
- **Manual inspection** - Cache files are human-readable JSON for debugging
- **Graceful degradation** - Uses stale cache if network unavailable

See `cache/README.md` for detailed cache format, expiration times, and management instructions.

## Project Structure

```
mahamudra-Artemis-II/
├── main.py                        # Entry point
├── check_cache.py                 # Cache status checker
├── check_trajectory_storage.py    # Incremental storage manager
├── requirements.txt               # rich, requests
├── cache/                         # API cache and trajectory data
│   ├── spacecraft.json
│   ├── dsn.json
│   ├── weather.json
│   ├── donki.json
│   ├── trajectory.json
│   ├── photo.bin
│   ├── photos/                    # Photo carousel (binary + metadata)
│   ├── trajectory_history/        # Historical snapshots (legacy)
│   │   ├── trajectory_*.json
│   │   └── ...
│   ├── trajectory_data/           # Incremental JSONL storage
│   │   ├── index.json             # Metadata
│   │   └── points.jsonl           # Append-only points
│   └── README.md
├── web/                           # Web dashboard (GitHub Pages)
│   ├── index.html                 # Dashboard layout
│   ├── dashboard.js               # UI controller, canvas map, photo carousel
│   ├── api-client.js              # Reads cached JSON from data/
│   ├── styles.css                 # Terminal-inspired styling
│   ├── server.py                  # Local dev server (port 8000)
│   └── data/                      # JSON cache (auto-generated)
│       ├── spacecraft.json
│       ├── dsn.json
│       ├── weather.json
│       ├── alerts.json
│       └── photos.json            # Array of up to 10 NASA IOTD photos
├── scripts/
│   └── update_web_data.py         # Fetches NASA data for web (GitHub Actions)
├── .github/workflows/
│   └── update-web-data.yml        # GitHub Action (every 10 min)
├── docs/
│   ├── technical-analysis.md
│   ├── functional-analysis.md
│   └── plans/trajectory.md
├── CACHE_EXPIRATION.md            # Cache TTL guide
├── INCREMENTAL_STORAGE.md         # Trajectory storage guide
├── TRAJECTORY_HISTORY.md          # Legacy history (optional)
└── artemis/
    ├── config.py
    ├── models.py
    ├── state.py
    ├── compute.py
    ├── cache.py                   # Cache serialization
    ├── photo_carousel.py          # Photo carousel (6s rotation)
    ├── trajectory_storage.py      # Incremental storage
    ├── fetchers/
    │   ├── base.py
    │   ├── horizons.py            # Uses append_trajectory_points()
    │   ├── dsn.py
    │   ├── swpc.py
    │   ├── donki.py
    │   └── nasa_images.py         # Fetches up to 10 photos from RSS
    └── dashboard/
        ├── app.py                 # Render loop with carousel rotation
        ├── layout.py
        └── panels/
            ├── header.py
            ├── solar_map.py       # Trajectory map (text labels, no emoji)
            ├── spacecraft.py
            ├── dsn.py
            ├── weather.py
            ├── alerts.py
            ├── photo.py
            └── status.py

```

## Quick Start

```bash
# Install dependencies (Python >= 3.10)
pip install -r requirements.txt

# Run the viewer
python main.py

# Exit with Ctrl+C
```

## Architecture

**Poll-and-render** with daemon threads:

- **5 fetcher threads** poll APIs at independent intervals (10s-900s)
- **1 main thread** renders the Rich terminal dashboard at 1 Hz
- **SharedState** (single Lock) bridges fetchers and renderer with frozen dataclasses
- Graceful degradation: API failures show last known data + staleness indicator

## Documentation

- **[Technical Analysis](docs/technical-analysis.md)** -- Architecture, APIs, protocols, data flows, verified response formats
- **[Functional Analysis](docs/functional-analysis.md)** -- Requirements, domain rules, use cases, implementation status
- **[Cache Expiration Guide](CACHE_EXPIRATION.md)** -- TTL configuration, cache status checking, customization
- **[Incremental Storage](INCREMENTAL_STORAGE.md)** -- Background trajectory storage, JSONL format, deduplication
- **[Glossary](docs/glossary.md)** -- Key concepts: Moon-centred frame, distance compression, coordinate systems, mission terminology

## Cache & Storage Tools

Check cache status:
```bash
python check_cache.py
```

Manage incremental trajectory storage:
```bash
python check_trajectory_storage.py stats    # Storage statistics
python check_trajectory_storage.py data     # Show loaded data
python check_trajectory_storage.py clear    # Clear stored data
```

## License

MIT
