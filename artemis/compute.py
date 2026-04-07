import math
from datetime import datetime, timezone, timedelta
from typing import Optional

from artemis import config
from artemis.models import StateVector, SpacecraftData


def distance_km(x: float, y: float, z: float) -> float:
    """Euclidean distance from origin for a 3D position.

    Args:
        x: X component (km).
        y: Y component (km).
        z: Z component (km).

    Returns:
        Scalar distance (km).
    """
    return math.sqrt(x * x + y * y + z * z)


def distance_between(sv1: StateVector, sv2: StateVector) -> float:
    """Euclidean distance between two state vectors.

    Args:
        sv1: First body state vector.
        sv2: Second body state vector.

    Returns:
        Scalar distance (km).
    """
    return math.sqrt(
        (sv1.x - sv2.x) ** 2 + (sv1.y - sv2.y) ** 2 + (sv1.z - sv2.z) ** 2
    )


def speed_km_s(vx: float, vy: float, vz: float) -> float:
    """Scalar speed from a 3D velocity vector.

    Args:
        vx: X velocity component (km/s).
        vy: Y velocity component (km/s).
        vz: Z velocity component (km/s).

    Returns:
        Scalar speed (km/s).
    """
    return math.sqrt(vx * vx + vy * vy + vz * vz)


def km_to_miles(km: float) -> float:
    """Convert kilometres to statute miles.

    Args:
        km: Distance in kilometres.

    Returns:
        Distance in miles.
    """
    return km * config.KM_TO_MILES


def mission_elapsed_time(now: datetime | None = None) -> timedelta:
    """Compute Mission Elapsed Time from launch.

    Args:
        now: Reference UTC datetime; defaults to current UTC time.

    Returns:
        Timedelta since LAUNCH_TIME (negative if pre-launch).
    """
    if now is None:
        now = datetime.now(timezone.utc)
    return now - config.LAUNCH_TIME


def format_met(td: timedelta) -> str:
    """Format a timedelta as "DDd HHh MMm SSs".

    Args:
        td: Timedelta to format (may be negative).

    Returns:
        Human-readable MET string with leading sign if negative.
    """
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        sign = "-"
        total_seconds = abs(total_seconds)
    else:
        sign = ""
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{sign}{days:02d}d {hours:02d}h {minutes:02d}m {seconds:02d}s"


def flight_day(now: datetime | None = None) -> int:
    """Calculate the current flight day number (1-based).

    Args:
        now: Reference UTC datetime; defaults to current UTC time.

    Returns:
        Flight day number (0 if pre-launch).
    """
    met = mission_elapsed_time(now)
    if met.total_seconds() < 0:
        return 0
    return int(met.total_seconds() // 86400) + 1


# ---------------------------------------------------------------------------
# Telemetry-based phase & progress — derived from live Horizons data
# ---------------------------------------------------------------------------

_NEAR_EARTH_KM = 30_000
_NEAR_MOON_KM = 15_000
_LUNAR_SPHERE_OF_INFLUENCE_KM = 66_000


def earth_range_rate(sc: SpacecraftData) -> float:
    """Radial velocity relative to Earth (km/s). Positive = receding.

    Args:
        sc: Current spacecraft telemetry snapshot.

    Returns:
        Radial velocity (km/s). Positive means moving away from Earth.
    """
    o = sc.orion
    d = sc.distance_earth_km
    if d < 1.0:
        return 0.0
    return (o.x * o.vx + o.y * o.vy + o.z * o.vz) / d


def mission_phase_from_telemetry(sc: Optional[SpacecraftData] = None) -> str:
    """Determine current mission phase from live telemetry.

    Uses Earth/Moon distances and Earth range-rate to classify the phase
    without any hardcoded event times.

    Args:
        sc: Current spacecraft data, or None if not yet available.

    Returns:
        Phase name string.
    """
    if sc is None:
        met = mission_elapsed_time()
        if met.total_seconds() < 0:
            return "Pre-Launch"
        return "Awaiting Data"

    e_dist = sc.distance_earth_km
    m_dist = sc.distance_moon_km
    rr = earth_range_rate(sc)

    if m_dist < _NEAR_MOON_KM:
        return "Lunar Flyby"
    if rr >= 0:
        if e_dist < _NEAR_EARTH_KM:
            return "Earth Departure"
        return "Outbound Transit"
    else:
        if e_dist < _NEAR_EARTH_KM:
            return "Re-Entry"
        return "Return Transit"


def trajectory_progress(sc: Optional[SpacecraftData] = None) -> Optional[float]:
    """Compute trajectory progress 0.0–1.0 from live telemetry.

    Outbound leg: 0.0 (Earth) → 0.5 (lunar flyby).
    Return leg:   0.5 (lunar flyby) → 1.0 (Earth).

    Uses distance ratio earth/(earth+moon) and range-rate sign.

    Args:
        sc: Current spacecraft data, or None.

    Returns:
        Progress value in [0.0, 1.0], or None if no telemetry available.
    """
    if sc is None:
        return None

    e_dist = sc.distance_earth_km
    m_dist = sc.distance_moon_km
    total = e_dist + m_dist
    if total < 1.0:
        return 0.0

    ratio = e_dist / total  # 0 at Earth, ~1 at Moon
    rr = earth_range_rate(sc)

    if rr >= 0:
        # Outbound: 0.0 → 0.5
        return min(ratio * 0.5, 0.5)
    else:
        # Return: 0.5 → 1.0
        return 0.5 + (1.0 - ratio) * 0.5


def get_best_perspective(sc: SpacecraftData) -> str:
    """Determine the best display perspective (Earth or Moon).

    Returns:
        "Earth" or "Moon" based on proximity to the Moon.
    """
    if sc.distance_moon_km < _LUNAR_SPHERE_OF_INFLUENCE_KM:
        return "Moon"
    return "Earth"


def staleness_seconds(fetched_at: datetime) -> float:
    """Seconds elapsed since data was fetched.

    Args:
        fetched_at: UTC timestamp of the last fetch.

    Returns:
        Elapsed seconds as a float.
    """
    return (datetime.now(timezone.utc) - fetched_at).total_seconds()


def staleness_style(seconds: float, expected_interval: float) -> str:
    """Rich style colour based on data staleness relative to expected poll interval.

    Args:
        seconds: Seconds since last fetch.
        expected_interval: Normal polling interval (seconds).

    Returns:
        Rich style string ("green", "yellow", or "red").
    """
    if seconds < expected_interval * 2:
        return "green"
    elif seconds < expected_interval * 5:
        return "yellow"
    return "red"


def format_number(value: float, decimals: int = 0) -> str:
    """Format a number with thousand separators and fixed decimals.

    Args:
        value: Numeric value to format.
        decimals: Number of decimal places (default 0).

    Returns:
        Formatted string (e.g. "308,077" or "0.927").
    """
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


def get_projection_axes(samples: list[tuple[float, float, float]]) -> tuple[int, int]:
    """Identify the two axes (0=X, 1=Y, 2=Z) with the most variance.

    Args:
        samples: List of (x, y, z) coordinate tuples.

    Returns:
        Indices of the two most dominant axes (e.g. (0, 1) for X-Y).
    """
    if not samples:
        return 0, 1
    
    x_vals = [s[0] for s in samples]
    y_vals = [s[1] for s in samples]
    z_vals = [s[2] for s in samples]
    
    x_range = max(x_vals) - min(x_vals)
    y_range = max(y_vals) - min(y_vals)
    z_range = max(z_vals) - min(z_vals)
    
    ranges = [(0, x_range), (1, y_range), (2, z_range)]
    # Sort by range descending, pick top 2
    ranges.sort(key=lambda x: x[1], reverse=True)
    return ranges[0][0], ranges[1][0]


def format_ra_dec(ra: Optional[float], dec: Optional[float]) -> str:
    """Format RA/Dec degrees into HH:MM:SS and DD°MM'SS".

    Args:
        ra: Right Ascension (decimal degrees).
        dec: Declination (decimal degrees).

    Returns:
        Formatted string (e.g. "12h 34m 56s / +12° 34' 56\"").
    """
    if ra is None or dec is None:
        return "N/A"

    # RA: 360 degrees = 24 hours
    ra_h = ra / 15.0
    h = int(ra_h)
    m = int((ra_h - h) * 60)
    s = int((ra_h - h - m/60.0) * 3600)

    # Dec
    d = int(abs(dec))
    dm = int((abs(dec) - d) * 60)
    ds = int((abs(dec) - d - dm/60.0) * 3600)
    sign = "+" if dec >= 0 else "-"

    return f"{h:02d}h {m:02d}m {s:02d}s / {sign}{d:02d}° {dm:02d}' {ds:02d}\""
