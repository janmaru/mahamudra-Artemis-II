import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Any

from artemis import config
from artemis.models import (
    SpacecraftData,
    DSNData,
    SpaceWeatherData,
    DONKIData,
    TrajectoryData,
    MissionPhoto,
    StateVector,
    DSNDish,
    KpReading,
    SolarWind,
    NOAAScales,
    SpaceEvent,
    TrajectoryPoint,
    TrajectorySample,
)

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "cache"
TRAJECTORY_HISTORY_DIR = CACHE_DIR / "trajectory_history"


def ensure_cache_dir() -> Path:
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(exist_ok=True)
    return CACHE_DIR


def ensure_trajectory_history_dir() -> Path:
    """Create trajectory history directory if it doesn't exist."""
    TRAJECTORY_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    return TRAJECTORY_HISTORY_DIR


def is_cache_expired(cache_file: Path, cache_key: str) -> bool:
    """Check if a cache file has expired based on its modification time.
    
    Args:
        cache_file: Path to cache file
        cache_key: Key in config.CACHE_EXPIRATION dict (e.g., 'spacecraft')
    
    Returns:
        True if cache file doesn't exist, is empty, or has expired
    """
    if not cache_file.exists():
        return True
    
    try:
        mtime = cache_file.stat().st_mtime
        file_age = datetime.now(timezone.utc).timestamp() - mtime
        max_age = config.CACHE_EXPIRATION.get(cache_key, 3600)
        return file_age > max_age
    except Exception as exc:
        logger.warning("Error checking cache expiration for %s: %s", cache_key, exc)
        return True


def get_cache_age_seconds(cache_file: Path) -> Optional[float]:
    """Get the age of a cache file in seconds.
    
    Args:
        cache_file: Path to cache file
    
    Returns:
        Age in seconds, or None if file doesn't exist
    """
    if not cache_file.exists():
        return None
    
    try:
        mtime = cache_file.stat().st_mtime
        return datetime.now(timezone.utc).timestamp() - mtime
    except Exception:
        return None


def serialize_spacecraft(data: SpacecraftData) -> dict:
    """Convert SpacecraftData to JSON-serializable dict."""
    return {
        "orion": {
            "epoch": data.orion.epoch.isoformat(),
            "x": data.orion.x,
            "y": data.orion.y,
            "z": data.orion.z,
            "vx": data.orion.vx,
            "vy": data.orion.vy,
            "vz": data.orion.vz,
        },
        "moon": {
            "epoch": data.moon.epoch.isoformat(),
            "x": data.moon.x,
            "y": data.moon.y,
            "z": data.moon.z,
            "vx": data.moon.vx,
            "vy": data.moon.vy,
            "vz": data.moon.vz,
        },
        "distance_earth_km": data.distance_earth_km,
        "distance_moon_km": data.distance_moon_km,
        "speed_km_s": data.speed_km_s,
        "ra": data.ra,
        "dec": data.dec,
        "fetched_at": data.fetched_at.isoformat(),
    }


def serialize_dsn(data: DSNData) -> dict:
    """Convert DSNData to JSON-serializable dict."""
    return {
        "dishes": [
            {
                "station_name": dish.station_name,
                "station_code": dish.station_code,
                "dish_name": dish.dish_name,
                "size_m": dish.size_m,
                "azimuth": dish.azimuth,
                "elevation": dish.elevation,
                "downlink_freq_hz": dish.downlink_freq_hz,
                "downlink_data_rate_bps": dish.downlink_data_rate_bps,
                "uplink_freq_hz": dish.uplink_freq_hz,
                "uplink_data_rate_bps": dish.uplink_data_rate_bps,
                "rtlt_seconds": dish.rtlt_seconds,
                "downleg_range_km": dish.downleg_range_km,
            }
            for dish in data.dishes
        ],
        "fetched_at": data.fetched_at.isoformat(),
    }


def serialize_weather(data: SpaceWeatherData) -> dict:
    """Convert SpaceWeatherData to JSON-serializable dict."""
    return {
        "kp": {
            "timestamp": data.kp.timestamp,
            "kp": data.kp.kp,
        } if data.kp else None,
        "solar_wind": {
            "speed": data.solar_wind.speed,
            "density": data.solar_wind.density,
            "temperature": data.solar_wind.temperature,
            "bz": data.solar_wind.bz,
        } if data.solar_wind else None,
        "scales": {
            "g": data.scales.g,
            "s": data.scales.s,
            "r": data.scales.r,
        } if data.scales else None,
        "fetched_at": data.fetched_at.isoformat(),
    }


def serialize_donki(data: DONKIData) -> dict:
    """Convert DONKIData to JSON-serializable dict."""
    return {
        "events": [
            {
                "event_type": event.event_type,
                "start_time": event.start_time,
                "class_type": event.class_type,
                "link": event.link,
            }
            for event in data.events
        ],
        "fetched_at": data.fetched_at.isoformat(),
    }


def serialize_trajectory(data: TrajectoryData) -> dict:
    """Convert TrajectoryData to JSON-serializable dict."""
    return {
        "samples": [
            {
                "timestamp": sample.timestamp.isoformat(),
                "orion": {
                    "x": sample.orion.x,
                    "y": sample.orion.y,
                    "z": sample.orion.z,
                },
                "moon": {
                    "x": sample.moon.x,
                    "y": sample.moon.y,
                    "z": sample.moon.z,
                },
            }
            for sample in data.samples
        ],
        "current_index": data.current_index,
        "fetched_at": data.fetched_at.isoformat(),
    }


def cache_spacecraft(data: SpacecraftData) -> None:
    """Cache spacecraft data to JSON file."""
    ensure_cache_dir()
    cache_file = CACHE_DIR / "spacecraft.json"
    try:
        with open(cache_file, "w") as f:
            json.dump(serialize_spacecraft(data), f, indent=2)
        logger.debug("Cached spacecraft data to %s", cache_file)
    except Exception as exc:
        logger.warning("Failed to cache spacecraft data: %s", exc)


def cache_dsn(data: DSNData) -> None:
    """Cache DSN data to JSON file."""
    ensure_cache_dir()
    cache_file = CACHE_DIR / "dsn.json"
    try:
        with open(cache_file, "w") as f:
            json.dump(serialize_dsn(data), f, indent=2)
        logger.debug("Cached DSN data to %s", cache_file)
    except Exception as exc:
        logger.warning("Failed to cache DSN data: %s", exc)


def cache_weather(data: SpaceWeatherData) -> None:
    """Cache space weather data to JSON file."""
    ensure_cache_dir()
    cache_file = CACHE_DIR / "weather.json"
    try:
        with open(cache_file, "w") as f:
            json.dump(serialize_weather(data), f, indent=2)
        logger.debug("Cached weather data to %s", cache_file)
    except Exception as exc:
        logger.warning("Failed to cache weather data: %s", exc)


def cache_donki(data: DONKIData) -> None:
    """Cache DONKI events to JSON file."""
    ensure_cache_dir()
    cache_file = CACHE_DIR / "donki.json"
    try:
        with open(cache_file, "w") as f:
            json.dump(serialize_donki(data), f, indent=2)
        logger.debug("Cached DONKI data to %s", cache_file)
    except Exception as exc:
        logger.warning("Failed to cache DONKI data: %s", exc)


def cache_trajectory(data: TrajectoryData) -> None:
    """Cache trajectory data to JSON file."""
    ensure_cache_dir()
    cache_file = CACHE_DIR / "trajectory.json"
    try:
        with open(cache_file, "w") as f:
            json.dump(serialize_trajectory(data), f, indent=2)
        logger.debug("Cached trajectory data to %s", cache_file)
        
        # Also save to history
        cache_trajectory_history(data)
    except Exception as exc:
        logger.warning("Failed to cache trajectory data: %s", exc)


def cache_trajectory_history(data: TrajectoryData) -> None:
    """Save trajectory snapshot to history directory with timestamp.
    
    Each file is named: trajectory_YYYY-MM-DD_HH-MM-SS.json
    This preserves historical trajectory data for analysis.
    """
    ensure_trajectory_history_dir()
    
    # Use fetched_at timestamp for filename
    timestamp_str = data.fetched_at.strftime("%Y-%m-%d_%H-%M-%S")
    history_file = TRAJECTORY_HISTORY_DIR / f"trajectory_{timestamp_str}.json"
    
    try:
        with open(history_file, "w") as f:
            json.dump(serialize_trajectory(data), f, indent=2)
        logger.debug("Saved trajectory history to %s", history_file)
    except Exception as exc:
        logger.warning("Failed to save trajectory history: %s", exc)


def cache_photo(data: MissionPhoto) -> None:
    """Cache mission photo to file."""
    ensure_cache_dir()
    cache_file = CACHE_DIR / "photo.bin"
    try:
        with open(cache_file, "wb") as f:
            f.write(data.image_data)
        
        # Also cache metadata as JSON
        meta_file = CACHE_DIR / "photo_meta.json"
        with open(meta_file, "w") as f:
            json.dump({
                "title": data.title,
                "image_url": data.image_url,
                "url": data.url,
                "published": data.published,
                "fetched_at": data.fetched_at.isoformat(),
            }, f, indent=2)
        logger.debug("Cached photo to %s", cache_file)
    except Exception as exc:
        logger.warning("Failed to cache photo data: %s", exc)


def load_spacecraft(allow_stale: bool = False) -> Optional[SpacecraftData]:
    """Load cached spacecraft data.

    Args:
        allow_stale: If True, return data even if the cache TTL has expired.
    """
    cache_file = CACHE_DIR / "spacecraft.json"
    if not allow_stale and is_cache_expired(cache_file, "spacecraft"):
        return None
    
    try:
        with open(cache_file, "r") as f:
            data = json.load(f)
        
        orion = StateVector(
            epoch=datetime.fromisoformat(data["orion"]["epoch"]),
            x=data["orion"]["x"],
            y=data["orion"]["y"],
            z=data["orion"]["z"],
            vx=data["orion"]["vx"],
            vy=data["orion"]["vy"],
            vz=data["orion"]["vz"],
        )
        moon = StateVector(
            epoch=datetime.fromisoformat(data["moon"]["epoch"]),
            x=data["moon"]["x"],
            y=data["moon"]["y"],
            z=data["moon"]["z"],
            vx=data["moon"]["vx"],
            vy=data["moon"]["vy"],
            vz=data["moon"]["vz"],
        )
        
        return SpacecraftData(
            orion=orion,
            moon=moon,
            distance_earth_km=data["distance_earth_km"],
            distance_moon_km=data["distance_moon_km"],
            speed_km_s=data["speed_km_s"],
            ra=data.get("ra"),
            dec=data.get("dec"),
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
        )
    except Exception as exc:
        logger.debug("Failed to load cached spacecraft data: %s", exc)
        return None


def load_dsn(allow_stale: bool = False) -> Optional[DSNData]:
    """Load cached DSN data.

    Args:
        allow_stale: If True, return data even if the cache TTL has expired.
    """
    cache_file = CACHE_DIR / "dsn.json"
    if not allow_stale and is_cache_expired(cache_file, "dsn"):
        return None
    
    try:
        with open(cache_file, "r") as f:
            data = json.load(f)
        
        dishes = [
            DSNDish(
                station_name=d["station_name"],
                station_code=d["station_code"],
                dish_name=d["dish_name"],
                size_m=d["size_m"],
                azimuth=d["azimuth"],
                elevation=d["elevation"],
                downlink_freq_hz=d.get("downlink_freq_hz"),
                downlink_data_rate_bps=d.get("downlink_data_rate_bps"),
                uplink_freq_hz=d.get("uplink_freq_hz"),
                uplink_data_rate_bps=d.get("uplink_data_rate_bps"),
                rtlt_seconds=d.get("rtlt_seconds"),
                downleg_range_km=d.get("downleg_range_km"),
            )
            for d in data["dishes"]
        ]
        
        return DSNData(
            dishes=tuple(dishes),
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
        )
    except Exception as exc:
        logger.debug("Failed to load cached DSN data: %s", exc)
        return None


def load_weather(allow_stale: bool = False) -> Optional[SpaceWeatherData]:
    """Load cached weather data.

    Args:
        allow_stale: If True, return data even if the cache TTL has expired.
    """
    cache_file = CACHE_DIR / "weather.json"
    if not allow_stale and is_cache_expired(cache_file, "weather"):
        return None
    
    try:
        with open(cache_file, "r") as f:
            data = json.load(f)
        
        kp = None
        if data.get("kp"):
            kp = KpReading(timestamp=data["kp"]["timestamp"], kp=data["kp"]["kp"])
        
        solar_wind = None
        if data.get("solar_wind"):
            solar_wind = SolarWind(
                speed=data["solar_wind"]["speed"],
                density=data["solar_wind"]["density"],
                temperature=data["solar_wind"]["temperature"],
                bz=data["solar_wind"]["bz"],
            )
        
        scales = None
        if data.get("scales"):
            scales = NOAAScales(
                g=data["scales"]["g"],
                s=data["scales"]["s"],
                r=data["scales"]["r"],
            )
        
        return SpaceWeatherData(
            kp=kp,
            solar_wind=solar_wind,
            scales=scales,
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
        )
    except Exception as exc:
        logger.debug("Failed to load cached weather data: %s", exc)
        return None


def load_donki(allow_stale: bool = False) -> Optional[DONKIData]:
    """Load cached DONKI data.

    Args:
        allow_stale: If True, return data even if the cache TTL has expired.
    """
    cache_file = CACHE_DIR / "donki.json"
    if not allow_stale and is_cache_expired(cache_file, "donki"):
        return None
    
    try:
        with open(cache_file, "r") as f:
            data = json.load(f)
        
        events = [
            SpaceEvent(
                event_type=e["event_type"],
                start_time=e["start_time"],
                class_type=e.get("class_type"),
                link=e.get("link"),
            )
            for e in data["events"]
        ]
        
        return DONKIData(
            events=tuple(events),
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
        )
    except Exception as exc:
        logger.debug("Failed to load cached DONKI data: %s", exc)
        return None


def load_trajectory(allow_stale: bool = False) -> Optional[TrajectoryData]:
    """Load cached trajectory data.

    Args:
        allow_stale: If True, return data even if the cache TTL has expired.
    """
    cache_file = CACHE_DIR / "trajectory.json"
    if not allow_stale and is_cache_expired(cache_file, "trajectory"):
        return None
    
    try:
        with open(cache_file, "r") as f:
            data = json.load(f)
        
        samples = [
            TrajectorySample(
                timestamp=datetime.fromisoformat(s["timestamp"]),
                orion=TrajectoryPoint(
                    x=s["orion"]["x"],
                    y=s["orion"]["y"],
                    z=s["orion"]["z"],
                ),
                moon=TrajectoryPoint(
                    x=s["moon"]["x"],
                    y=s["moon"]["y"],
                    z=s["moon"]["z"],
                ),
            )
            for s in data["samples"]
        ]
        
        return TrajectoryData(
            samples=tuple(samples),
            current_index=data["current_index"],
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
        )
    except Exception as exc:
        logger.debug("Failed to load cached trajectory data: %s", exc)
        return None


def load_photo(allow_stale: bool = False) -> Optional[MissionPhoto]:
    """Load cached photo.

    Args:
        allow_stale: If True, return data even if the cache TTL has expired.
    """
    cache_file = CACHE_DIR / "photo.bin"
    meta_file = CACHE_DIR / "photo_meta.json"

    if not allow_stale and is_cache_expired(cache_file, "photo"):
        return None
    
    try:
        with open(cache_file, "rb") as f:
            image_data = f.read()
        
        with open(meta_file, "r") as f:
            meta = json.load(f)
        
        return MissionPhoto(
            title=meta["title"],
            image_data=image_data,
            image_url=meta.get("image_url", ""),
            url=meta["url"],
            published=meta["published"],
            fetched_at=datetime.fromisoformat(meta["fetched_at"]),
        )
    except Exception as exc:
        logger.debug("Failed to load cached photo data: %s", exc)
        return None


def list_trajectory_history() -> list[Path]:
    """List all saved trajectory history files, sorted by timestamp (newest first)."""
    ensure_trajectory_history_dir()
    
    history_files = sorted(
        TRAJECTORY_HISTORY_DIR.glob("trajectory_*.json"),
        reverse=True  # Newest first
    )
    return history_files


def load_trajectory_history_file(history_file: Path) -> Optional[TrajectoryData]:
    """Load a specific trajectory history file.
    
    Args:
        history_file: Path to trajectory_YYYY-MM-DD_HH-MM-SS.json file
    
    Returns:
        TrajectoryData if loaded successfully, None on error
    """
    try:
        with open(history_file, "r") as f:
            data = json.load(f)
        
        samples = [
            TrajectorySample(
                timestamp=datetime.fromisoformat(s["timestamp"]),
                orion=TrajectoryPoint(
                    x=s["orion"]["x"],
                    y=s["orion"]["y"],
                    z=s["orion"]["z"],
                ),
                moon=TrajectoryPoint(
                    x=s["moon"]["x"],
                    y=s["moon"]["y"],
                    z=s["moon"]["z"],
                ),
            )
            for s in data["samples"]
        ]
        
        return TrajectoryData(
            samples=tuple(samples),
            current_index=data["current_index"],
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
        )
    except Exception as exc:
        logger.debug("Failed to load trajectory history file %s: %s", history_file, exc)
        return None


def get_trajectory_history_stats() -> dict:
    """Get statistics about trajectory history files.
    
    Returns:
        Dict with counts, sizes, and age information
    """
    ensure_trajectory_history_dir()
    
    history_files = list_trajectory_history()
    
    if not history_files:
        return {
            "total_files": 0,
            "oldest_file": None,
            "newest_file": None,
            "total_size_mb": 0,
        }
    
    total_size = sum(f.stat().st_size for f in history_files)
    oldest_file = history_files[-1]  # Last in reversed list
    newest_file = history_files[0]   # First in reversed list
    
    return {
        "total_files": len(history_files),
        "oldest_file": oldest_file.name,
        "newest_file": newest_file.name,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "size_per_file_mb": round(total_size / len(history_files) / (1024 * 1024), 2) if history_files else 0,
    }


def cleanup_trajectory_history(keep_count: int = 100) -> int:
    """Remove old trajectory history files, keeping only the most recent ones.
    
    Args:
        keep_count: How many recent files to keep (default 100)
    
    Returns:
        Number of files deleted
    """
    ensure_trajectory_history_dir()
    
    history_files = list_trajectory_history()
    
    if len(history_files) <= keep_count:
        return 0
    
    files_to_delete = history_files[keep_count:]
    deleted = 0
    
    for f in files_to_delete:
        try:
            f.unlink()
            deleted += 1
            logger.info("Deleted old trajectory history: %s", f.name)
        except Exception as exc:
            logger.warning("Failed to delete trajectory history file %s: %s", f.name, exc)
    
    return deleted
