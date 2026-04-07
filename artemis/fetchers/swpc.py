import logging
from datetime import datetime, timezone

from artemis import config
from artemis.cache import cache_weather
from artemis.fetchers.base import BaseFetcher
from artemis.models import KpReading, SolarWind, NOAAScales, SpaceWeatherData
from artemis.state import SharedState

logger = logging.getLogger(__name__)


def _safe_float(value) -> float | None:
    """Attempt to parse a value as float, returning None on failure.

    Args:
        value: Any value (typically a string from JSON).

    Returns:
        Parsed float, or None if the value is empty, "null", or unparseable.
    """
    if value is None or value == "" or value == "null":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class SWPCFetcher(BaseFetcher):
    """Fetcher for NOAA/SWPC space weather APIs — Kp index, solar wind, and NOAA scales.

    Args:
        state: Shared state instance for publishing results.
    """

    def __init__(self, state: SharedState):
        super().__init__(state, config.SWPC_INTERVAL)

    def fetch_and_update(self) -> None:
        """Fetch Kp, solar wind, and NOAA scales, then publish SpaceWeatherData."""
        kp = self._fetch_kp()
        solar_wind = self._fetch_solar_wind()
        scales = self._fetch_scales()
        weather_data = SpaceWeatherData(
            kp=kp,
            solar_wind=solar_wind,
            scales=scales,
            fetched_at=datetime.now(timezone.utc),
        )
        self._state.update_weather(weather_data)
        cache_weather(weather_data)
        kp_val = kp.kp if kp else "N/A"
        logger.info("SWPC: Kp=%s", kp_val)

    def _fetch_kp(self) -> KpReading | None:
        """Fetch the latest planetary K-index from SWPC.

        Returns:
            Most recent KpReading, or None on failure.
        """
        try:
            data = self._get_json(config.SWPC_KP_URL)
            if not data:
                return None
            last = data[-1]
            if isinstance(last, dict):
                return KpReading(
                    timestamp=str(last.get("time_tag", "")),
                    kp=float(last.get("Kp", 0)),
                )
            return KpReading(timestamp=str(last[0]), kp=float(last[1]))
        except Exception as exc:
            logger.warning("Failed to fetch Kp: %s", exc)
            return None

    def _fetch_solar_wind(self) -> SolarWind | None:
        """Fetch real-time solar wind plasma and IMF data from SWPC.

        Returns:
            SolarWind with speed, density, temperature, and Bz; or None on failure.
        """
        try:
            plasma = self._get_json(config.SWPC_PLASMA_URL)
            mag = self._get_json(config.SWPC_MAG_URL)

            sw_speed = None
            sw_density = None
            sw_temp = None
            sw_bz = None

            if len(plasma) >= 2:
                last_p = plasma[-1]
                # [time_tag, density, speed, temperature]
                sw_density = _safe_float(last_p[1])
                sw_speed = _safe_float(last_p[2])
                sw_temp = _safe_float(last_p[3])

            if len(mag) >= 2:
                last_m = mag[-1]
                # [time_tag, bx_gsm, by_gsm, bz_gsm, lon_gsm, lat_gsm, bt]
                sw_bz = _safe_float(last_m[3])

            return SolarWind(
                speed=sw_speed,
                density=sw_density,
                temperature=sw_temp,
                bz=sw_bz,
            )
        except Exception as exc:
            logger.warning("Failed to fetch solar wind: %s", exc)
            return None

    def _fetch_scales(self) -> NOAAScales | None:
        """Fetch current NOAA Space Weather Scales (G/S/R levels).

        Returns:
            NOAAScales with geomagnetic, radiation, and radio blackout levels; or None.
        """
        try:
            data = self._get_json(config.SWPC_SCALES_URL)
            current = data.get("0", {})

            def get_scale(key: str) -> int:
                entry = current.get(key, {})
                val = entry.get("Scale", None) if isinstance(entry, dict) else None
                if val is None:
                    return 0
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0

            return NOAAScales(
                g=get_scale("G"),
                s=get_scale("S"),
                r=get_scale("R"),
            )
        except Exception as exc:
            logger.warning("Failed to fetch NOAA scales: %s", exc)
            return None
