# Functional Analysis — Artemis-II Python Viewer

## Table of Contents

- [1. Purpose](#1-purpose)
- [2. Target Users](#2-target-users)
- [3. Functional Requirements](#3-functional-requirements)
  - [3.1 Spacecraft Tracking](#31-spacecraft-tracking)
  - [3.2 Deep Space Network Status](#32-deep-space-network-status)
  - [3.3 Space Weather Monitoring](#33-space-weather-monitoring)
  - [3.4 Trajectory Visualization](#34-trajectory-visualization)
  - [3.5 Mission Timeline](#35-mission-timeline)
- [4. Domain Model](#4-domain-model)
- [5. Use Cases](#5-use-cases)
- [6. Business Rules and Constraints](#6-business-rules-and-constraints)
- [7. Non-Functional Requirements](#7-non-functional-requirements)
- [8. Glossary](#8-glossary)

---

## 1. Purpose

The Artemis-II Python Viewer provides a real-time monitoring dashboard for NASA's Artemis II crewed lunar flyby mission. It aggregates publicly available data from multiple NASA/JPL/NOAA sources into a unified view, enabling users to track the Orion spacecraft's position, communication links, and space weather conditions throughout the ~10-day mission.

---

## 2. Target Users

| User Type | Needs |
|-----------|-------|
| Space enthusiasts | Easy-to-read dashboard with distance, speed, and mission phase |
| Developers / students | Clean Python codebase to learn from; extensible architecture |
| Educators | Visual tool for teaching orbital mechanics and mission operations |
| Amateur astronomers | Sky coordinates (RA/Dec) to point telescopes at Orion |

---

## 3. Functional Requirements

### 3.1 Spacecraft Tracking

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| ST-01 | Display Orion's current distance from Earth in km and miles | Must | Done |
| ST-02 | Display Orion's current distance from the Moon in km and miles | Must | Done |
| ST-03 | Display Orion's current velocity (magnitude) in km/s and km/h | Must | Done |
| ST-04 | Display Orion's 3D position vector (X, Y, Z) in J2000 frame | Should | Done |
| ST-05 | Display current Right Ascension and Declination (sky position) | Could | -- |
| ST-06 | Show time since launch (Mission Elapsed Time, MET) | Must | Done |
| ST-07 | Show current Flight Day number | Must | Done |
| ST-08 | Auto-refresh spacecraft data at a configurable interval (default: 60s) | Must | Done |
| ST-09 | Display data staleness indicator (time since last successful fetch) | Should | Done |

### 3.2 Deep Space Network Status

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| DSN-01 | Show which DSN station(s) are currently tracking Orion | Must | Done |
| DSN-02 | Display active dish name and antenna size | Should | Done (name) |
| DSN-03 | Show uplink/downlink signal status (frequency, data rate) | Should | Done |
| DSN-04 | Show round-trip light time (RTLT) from DSN data | Could | Done |
| DSN-05 | Indicate when no DSN antenna is actively tracking Orion | Must | Done |

### 3.3 Space Weather Monitoring

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| SW-01 | Display current planetary Kp index | Must | Done |
| SW-02 | Display NOAA Space Weather Scales (G, S, R levels) | Should | Done |
| SW-03 | Show solar wind speed and density | Should | Done |
| SW-04 | Show recent solar flare events (last 3 days) | Could | Done |
| SW-05 | Show recent CME events with half-angle info | Could | Done |
| SW-06 | Visual alert when Kp >= 5 (geomagnetic storm) | Must | Done |
| SW-07 | Visual alert when S scale >= S2 (solar radiation storm) | Should | Done |

### 3.4 Trajectory Visualization

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| TV-01 | Display current Orion position on 2D map (Earth-relative, X-Y plane) | Should | Done |
| TV-02 | Mark Orion position in magenta (◆) on the main dashboard | Should | Done |
| TV-03 | Show current Moon position (🌕) relative to Earth (🌍) | Should | Done |
| TV-04 | Display Earth distance and Moon distance for Orion | Must | Done |
| TV-05 | Adaptive grid width based on terminal size | Should | Done |
| TV-06 | Open native Tkinter viewer (Press [T]) showing full trajectory history with 2D map + timeline | Should | Done |
| TV-07 | History list shows timestamp, Earth distance, Moon distance for each sample | Should | Done |
| TV-08 | Trajectory map shows START (green) and CURRENT (magenta) markers | Should | Done |

### 3.5 Mission Timeline

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| MT-01 | Display key mission events with timestamps (TLI, lunar flyby, entry interface, splashdown) | Should | Done (header) |
| MT-02 | Highlight current mission phase | Should | Done |
| MT-03 | Show countdown to next major event | Could | Done |

### 3.6 Mission Photo Viewer

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| MP-01 | Display NASA IOTD images rotating in carousel | Should | Done |
| MP-02 | Open native Tkinter viewer (Press [P]) showing full-resolution photos | Should | Done |
| MP-03 | Navigate between photos with arrow keys (Left/Right) | Should | Done |
| MP-04 | List sidebar showing all cached photos with index | Should | Done |
| MP-05 | Display photo metadata (title, date) | Should | Done |
| MP-06 | Prevent duplicate windows - bring existing window to focus on repeated key press | Should | Done |

---

## 4. Domain Model

```
Mission
  ├── Spacecraft (Orion / "Integrity")
  │     ├── StateVector {position, velocity, epoch}
  │     ├── OrbitalElements (derived)
  │     └── SkyPosition {ra, dec} (derived)
  │
  ├── DSNLink
  │     ├── Station {name, location}
  │     ├── Dish {name, azimuth, elevation}
  │     └── Signal {direction, frequency, dataRate, power}
  │
  ├── SpaceWeather
  │     ├── KpIndex {value, timestamp}
  │     ├── SolarWind {speed, density, temperature, Bz}
  │     ├── NOAAScales {G, S, R}
  │     └── Events[] {flares, cmes, storms}
  │
  └── Timeline
        └── MissionEvent[] {name, timestamp, T+offset, phase}
```

### Key Derived Values

| Value | Formula | Source |
|-------|---------|--------|
| Distance from Earth | `sqrt(X^2 + Y^2 + Z^2)` | Horizons state vector |
| Distance from Moon | `sqrt((X-Xm)^2 + (Y-Ym)^2 + (Z-Zm)^2)` | Horizons (Orion + Moon vectors) |
| Speed | `sqrt(VX^2 + VY^2 + VZ^2)` | Horizons state vector |
| Mission Elapsed Time | `now - launch_time` | Known launch datetime |
| Flight Day | `floor(MET / 24h) + 1` | Derived from MET |

---

## 5. Use Cases

### UC-01: Monitor Spacecraft Status

**Actor**: User  
**Precondition**: Mission is active (between launch and splashdown)  
**Flow**:
1. User launches the viewer
2. System fetches current state vectors from Horizons API
3. System computes distances and speed
4. System displays dashboard with all spacecraft metrics
5. System auto-refreshes every 60 seconds

**Postcondition**: User sees up-to-date spacecraft telemetry

### UC-02: Check DSN Communications

**Actor**: User  
**Flow**:
1. System fetches DSN Now XML feed
2. System filters for dishes tracking spacecraft `EM2`
3. System displays active station, dish, and signal info
4. If no dish is tracking EM2, system displays "No active DSN link"

### UC-03: Assess Space Weather Risk

**Actor**: User  
**Flow**:
1. System fetches Kp index and NOAA scales
2. If Kp >= 5, system shows storm warning with visual alert
3. System fetches recent flare and CME events from DONKI
4. User reviews conditions to assess radiation environment

### UC-04: Visualize Trajectory

**Actor**: User  
**Flow**:
1. System fetches Orion + Moon positions from Horizons (launch to now, 10-min steps)
2. System computes Moon-relative positions: `R(t) = Orion(t) - Moon(t)`
3. System renders 2D projection with non-linear distance compression
4. Moon at centre, Earth at edge, Orion marker with trajectory trail

### UC-05: Track Mission Progress

**Actor**: User  
**Flow**:
1. System displays mission timeline with key events
2. System highlights current phase based on MET
3. System shows countdown to next major event

---

## 6. Business Rules and Constraints

| ID | Rule |
|----|------|
| BR-01 | All times must be displayed in UTC. Local time may be shown as secondary. |
| BR-02 | Distances must be shown in both km and miles (1 mile = 1.60934 km). |
| BR-03 | Speed must be shown in km/s with km/h as secondary. |
| BR-04 | When API data is unavailable, show last known values with a staleness warning — never show blank or zero. |
| BR-05 | The viewer must not crash on any API failure. Graceful degradation is mandatory. |
| BR-06 | Space weather alerts (Kp >= 5, S >= S2) must be visually distinct (color/icon). |
| BR-07 | DSN station names must be displayed as friendly names (e.g., "Goldstone"), not codes. |
| BR-08 | Mission Elapsed Time format: `DDd HHh MMm SSs` (e.g., `03d 14h 22m 07s`). |
| BR-09 | Flight Day numbering starts at 1 (Flight Day 1 = launch day). |
| BR-10 | The Horizons API spacecraft ID for Artemis II is `-1024`. This must not be hardcoded in display logic but defined as a configuration constant. |

---

## 7. Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NF-01 | Startup time | < 5 seconds to first data display |
| NF-02 | Memory usage | < 200 MB during normal operation |
| NF-03 | Python version | >= 3.10 |
| NF-04 | Cross-platform | Windows, macOS, Linux |
| NF-05 | Dependencies | Minimize; prefer standard library where feasible |
| NF-06 | Offline resilience | Continue displaying cached data for at least 10 minutes |
| NF-07 | Terminal mode | Must work in 80x24 terminal minimum |
| NF-08 | Native viewers | Photo and Trajectory viewers must open in native Tkinter windows (not browser) |
| NF-09 | Window management | No duplicate viewer windows; repeated key presses bring window to focus |
| NF-10 | Incremental storage | Trajectory history stored incrementally in cache (JSONL format) |

---

## 8. Glossary

See [glossary.md](glossary.md) for the full glossary of terms, abbreviations, and units displayed in the dashboard.
