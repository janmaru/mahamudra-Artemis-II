from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class StateVector:
    """Cartesian state vector of a body in a J2000 reference frame.

    Args:
        epoch: UTC timestamp of the observation.
        x: X position component (km).
        y: Y position component (km).
        z: Z position component (km).
        vx: X velocity component (km/s).
        vy: Y velocity component (km/s).
        vz: Z velocity component (km/s).
    """

    epoch: datetime
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float


@dataclass(frozen=True)
class SpacecraftData:
    """Snapshot of Orion and Moon positions with derived metrics.

    Args:
        orion: Orion state vector (Earth-centered J2000).
        moon: Moon state vector (Earth-centered J2000).
        distance_earth_km: Orion distance from Earth centre (km).
        distance_moon_km: Orion distance from Moon centre (km).
        speed_km_s: Orion scalar speed relative to Earth (km/s).
        ra: Right Ascension (decimal degrees), or None.
        dec: Declination (decimal degrees), or None.
        fetched_at: UTC timestamp when this data was retrieved.
    """

    orion: StateVector
    moon: StateVector
    distance_earth_km: float
    distance_moon_km: float
    speed_km_s: float
    ra: Optional[float] = None
    dec: Optional[float] = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class DSNDish:
    """Single Deep Space Network dish actively tracking the spacecraft.

    Args:
        station_name: Human-readable station name (e.g. "Goldstone").
        station_code: DSN complex code (e.g. "gdscc").
        dish_name: Individual antenna identifier (e.g. "DSS14").
        size_m: Antenna diameter in meters.
        azimuth: Antenna azimuth angle (degrees).
        elevation: Antenna elevation angle (degrees).
        downlink_freq_hz: Downlink signal frequency (Hz), or None.
        downlink_data_rate_bps: Downlink data rate (bps), or None.
        uplink_freq_hz: Uplink signal frequency (Hz), or None.
        uplink_data_rate_bps: Uplink data rate (bps), or None.
        rtlt_seconds: Round-trip light time (seconds), or None.
        downleg_range_km: One-way downleg range (km), or None.
    """

    station_name: str
    station_code: str
    dish_name: str
    size_m: int
    azimuth: float
    elevation: float
    downlink_freq_hz: Optional[float] = None
    downlink_data_rate_bps: Optional[float] = None
    uplink_freq_hz: Optional[float] = None
    uplink_data_rate_bps: Optional[float] = None
    rtlt_seconds: Optional[float] = None
    downleg_range_km: Optional[float] = None


@dataclass(frozen=True)
class DSNData:
    """Collection of DSN dishes currently tracking the spacecraft.

    Args:
        dishes: Tuple of active DSNDish instances.
        fetched_at: UTC timestamp when this data was retrieved.
    """

    dishes: tuple[DSNDish, ...]
    fetched_at: datetime


@dataclass(frozen=True)
class KpReading:
    """Single planetary K-index measurement.

    Args:
        timestamp: Time tag string from NOAA.
        kp: Planetary K-index value (0-9 scale).
    """

    timestamp: str
    kp: float


@dataclass(frozen=True)
class SolarWind:
    """Real-time solar wind plasma and magnetic field conditions.

    Args:
        speed: Bulk solar wind speed (km/s), or None.
        density: Proton density (particles/cm³), or None.
        temperature: Proton temperature (Kelvin), or None.
        bz: Interplanetary magnetic field Bz component (nT), or None.
    """

    speed: Optional[float] = None
    density: Optional[float] = None
    temperature: Optional[float] = None
    bz: Optional[float] = None


@dataclass(frozen=True)
class NOAAScales:
    """NOAA Space Weather Scales (current conditions).

    Args:
        g: Geomagnetic storm level (G0-G5).
        s: Solar radiation storm level (S0-S5).
        r: Radio blackout level (R0-R5).
    """

    g: int = 0
    s: int = 0
    r: int = 0


@dataclass(frozen=True)
class SpaceWeatherData:
    """Aggregated space weather snapshot from NOAA/SWPC.

    Args:
        kp: Latest Kp index reading, or None.
        solar_wind: Latest solar wind conditions, or None.
        scales: Current NOAA Space Weather Scales, or None.
        fetched_at: UTC timestamp when this data was retrieved.
    """

    kp: Optional[KpReading] = None
    solar_wind: Optional[SolarWind] = None
    scales: Optional[NOAAScales] = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class SpaceEvent:
    """A single space weather event from NASA DONKI.

    Args:
        event_type: DONKI event code — "FLR" (flare), "CME", or "GST" (storm).
        start_time: ISO-8601 event start/peak time string.
        class_type: Event classification (e.g. "M1.0" for flares, "Kp=6" for storms).
        link: URL to the DONKI event detail page, or None.
    """

    event_type: str
    start_time: str
    class_type: Optional[str] = None
    link: Optional[str] = None


@dataclass(frozen=True)
class DONKIData:
    """Collection of recent space weather events from DONKI.

    Args:
        events: Tuple of SpaceEvent instances, sorted most-recent-first.
        fetched_at: UTC timestamp when this data was retrieved.
    """

    events: tuple[SpaceEvent, ...]
    fetched_at: datetime


@dataclass(frozen=True)
class MissionPhoto:
    """A photo from the mission, downloaded from NASA feeds.

    Args:
        title: Image title/caption.
        image_data: Raw image bytes (JPEG/PNG).
        image_url: Direct URL to the image file.
        url: Source URL of the page.
        published: Publication date string.
        fetched_at: UTC timestamp when this data was retrieved.
    """

    title: str
    image_data: bytes
    image_url: str
    url: str
    published: str
    fetched_at: datetime


@dataclass(frozen=True)
class TrajectoryPoint:
    """Single 3D position on the mission trajectory.

    Args:
        x: X position component (km).
        y: Y position component (km).
        z: Z position component (km).
    """

    x: float
    y: float
    z: float


@dataclass(frozen=True)
class TrajectorySample:
    """A synchronized sample of both Orion and Moon positions at a specific time."""
    timestamp: datetime
    orion: TrajectoryPoint
    moon: TrajectoryPoint


@dataclass(frozen=True)
class TrajectoryData:
    """Full mission trajectory for the ASCII plot.

    Args:
        samples: Ordered tuple of synchronized Orion and Moon positions.
        current_index: Index into samples closest to the current time.
        fetched_at: UTC timestamp when this data was retrieved.
    """

    samples: tuple[TrajectorySample, ...]
    current_index: int
    fetched_at: datetime
