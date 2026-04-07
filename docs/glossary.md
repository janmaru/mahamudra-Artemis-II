# Glossary — Artemis-II Python Viewer

Terms, abbreviations, and units displayed in the dashboard.

---

## Mission & Spacecraft

| Term | Description |
|------|-------------|
| Artemis II | NASA's first crewed lunar flyby mission using SLS/Orion |
| Orion | The crew vehicle; callsign **"Integrity"** |
| SLS | Space Launch System — the heavy-lift rocket |
| SPKID | JPL unique body identifier; Orion is `-1024` |
| EM2 | Exploration Mission 2 — DSN tracking designation for Orion |
| MET | Mission Elapsed Time — time since launch (T-0), displayed as `DDd HHh MMm SSs` |
| Flight Day | Sequential mission day count (Day 1 = launch day) |
| Phase | Current mission phase: Pre-Launch, Earth Orbit, TLI, Outbound, Lunar Flyby, Return, Re-Entry |
| TLI | Trans-Lunar Injection — engine burn that sends Orion toward the Moon |
| Free-Return Trajectory | Orbit using lunar gravity to return to Earth without additional burns |

---

## Spacecraft Telemetry

| Term | Description |
|------|-------------|
| Earth Distance | Distance from Orion to Earth's centre (km and mi) |
| Moon Distance | Distance from Orion to Moon's centre (km and mi) |
| Speed | Orion's velocity relative to Earth (km/s and km/h) |
| Pos (x1000 km) | Orion's X / Y / Z position in Earth-centred J2000, divided by 1000 |
| Data Epoch | UTC timestamp of the ephemeris data point from JPL Horizons |
| UTC | Coordinated Universal Time |

---

## Deep Space Network (DSN)

| Term | Description |
|------|-------------|
| DSN | Deep Space Network — NASA's global array of antennas for deep-space communication |
| Station | Ground station complex: Goldstone (California), Madrid (Spain), Canberra (Australia) |
| Dish | Individual antenna (e.g., DSS14, DSS34, DSS43) |
| Down | Downlink — signal from spacecraft to Earth: frequency (GHz/MHz) and data rate (Mbps/kbps/bps) |
| Up | Uplink — signal from Earth to spacecraft: frequency and data rate |
| RTLT | Round-Trip Light Time — signal travel time Earth → spacecraft → Earth, in seconds |
| Range | One-way distance from antenna to spacecraft (km) |
| GHz / MHz | Gigahertz / Megahertz — radio frequency units |
| Mbps / kbps / bps | Megabits / kilobits / bits per second — data rate units |

---

## Space Weather

| Term | Description |
|------|-------------|
| Kp Index | Planetary geomagnetic activity index (0–9 scale). Kp < 4 = Quiet/Unsettled; Kp >= 5 = Storm |
| NOAA Scales | Three-letter severity scale for space weather conditions |
| G0–G5 | Geomagnetic storm level (G0 = none, G5 = extreme) |
| S0–S5 | Solar radiation storm level (S0 = none, S5 = extreme) |
| R0–R5 | Radio blackout level (R0 = none, R5 = extreme) |
| Wind Speed | Solar wind bulk velocity (km/s); typical 300–800 km/s |
| Wind Density | Solar wind proton density (p/cm³ — particles per cubic centimetre) |
| Wind Temp | Solar wind proton temperature (K — Kelvin) |
| IMF Bz | Interplanetary Magnetic Field, north-south component (nT — nanotesla). Strongly negative Bz (< -10 nT) increases geomagnetic storm risk |
| nT | Nanotesla — unit of magnetic field strength |
| SWPC | Space Weather Prediction Center (NOAA) — source of Kp, solar wind, and NOAA Scales data |

---

## Alerts & Events

| Term | Description |
|------|-------------|
| CME | Coronal Mass Ejection — eruption of plasma and magnetic field from the Sun. Shown with `[*]` icon and half-angle (HA) in degrees |
| Solar Flare (FLR) | Sudden flash of electromagnetic radiation from the Sun. Shown with `[!]` icon and class (e.g., M1.0, X2.5) |
| Geomag. Storm (GST) | Geomagnetic storm event. Shown with `[S]` icon and Kp value |
| HA | Half-Angle — angular width of a CME in degrees |
| Flare Class | X-ray brightness classification: A, B, C, M, X (each 10x stronger). Number is multiplier (e.g., M1.0 = moderate) |
| DONKI | Database Of Notifications, Knowledge, Information — NASA's space weather event database |
| Bz Strongly South | Alert condition when IMF Bz is strongly negative, increasing storm probability |

---

## Trajectory Panel

| Term | Description |
|------|-------------|
| Moon-Centred Frame | Reference frame where Moon is at origin; `R(t) = Orion(t) - Moon(t)`. Shows Orion orbiting the Moon |
| 2D Projection | 3D Moon-relative vector projected onto the (x, y) plane of J2000 equatorial system |
| Distance Compression | Power-law scaling (`dist^0.3`) applied to radial distances. Compresses the ~384,000 km Earth-Moon range while expanding the ~2,000 km close-approach range for visibility |
| Trajectory Dots (`·`) | Green dots with dim-to-bright gradient showing temporal progression (early = dim, recent = bright) |
| 🌍 | Earth position (in Moon-relative frame, appears at edge of display) |
| 🌕 | Moon position (always at centre of display) |
| ◆ | Orion current position marker (bright green) |

---

## Coordinate System

| Property | Value |
|----------|-------|
| Frame | J2000 equatorial (ICRF) |
| Centre | Earth geocentre (`500@399`) |
| Units | km, km/s |
| Origin | `(0, 0, 0)` = centre of the Earth |

The Moon is fetched from the same centre, so `Orion - Moon` yields the Moon-relative vector directly.

---

## Status Bar

| Term | Description |
|------|-------------|
| Horizons | JPL Horizons API staleness (spacecraft ephemeris) |
| DSN | DSN Now feed staleness (antenna tracking data) |
| SWPC | NOAA Space Weather Prediction Center staleness |
| DONKI | NASA DONKI API staleness (space weather events) |
| Traj | Trajectory data staleness (historical Orion + Moon path) |
| Updated Xs ago | Staleness indicator — green (fresh), yellow (aging), red (stale) |
