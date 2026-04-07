import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from artemis import config
from artemis.cache import cache_dsn
from artemis.fetchers.base import BaseFetcher
from artemis.models import DSNDish, DSNData
from artemis.state import SharedState

logger = logging.getLogger(__name__)


def _safe_float(value: str | None) -> float | None:
    """Attempt to parse a string as float, returning None on failure.

    Args:
        value: String value from XML attribute, or None.

    Returns:
        Parsed float, or None if parsing fails or value is empty.
    """
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class DSNFetcher(BaseFetcher):
    """Fetcher for NASA DSN Now XML feed — tracks active dishes communicating with Orion.

    Args:
        state: Shared state instance for publishing results.
    """

    def __init__(self, state: SharedState):
        super().__init__(state, config.DSN_INTERVAL)

    def fetch_and_update(self) -> None:
        """Fetch DSN XML, filter for Orion dishes, and publish DSNData."""
        xml_text = self._get_text(config.DSN_URL)
        dishes = self._parse_dsn_xml(xml_text)
        dsn_data = DSNData(dishes=tuple(dishes), fetched_at=datetime.now(timezone.utc))
        self._state.update_dsn(dsn_data)
        cache_dsn(dsn_data)
        logger.info("DSN: %d dish(es) tracking %s", len(dishes), config.DSN_SPACECRAFT_CODE)

    def _parse_dsn_xml(self, xml_text: str) -> list[DSNDish]:
        """Parse DSN Now XML and extract dishes tracking our spacecraft."""
        root = ET.fromstring(xml_text)
        results: list[DSNDish] = []

        # Walk children of <dsn> in order, tracking the current station
        current_station_code = ""
        current_station_name = ""

        for child in root:
            if child.tag == "station":
                current_station_code = child.get("name", "")
                current_station_name = config.DSN_STATIONS.get(
                    current_station_code, current_station_code
                )
                continue

            if child.tag != "dish":
                continue

            dish = child
            dish_name = dish.get("name", "").upper()

            # Check if any target references our spacecraft
            tracking_us = False
            rtlt = None
            downleg_range = None
            for target in dish.findall("target"):
                if target.get("name") == config.DSN_SPACECRAFT_CODE:
                    tracking_us = True
                    rtlt = _safe_float(target.get("rtlt"))
                    downleg_range = _safe_float(target.get("downlegRange"))
                    break

            if not tracking_us:
                # Also check signal elements
                for sig in dish.findall("downSignal") + dish.findall("upSignal"):
                    if sig.get("spacecraft") == config.DSN_SPACECRAFT_CODE:
                        tracking_us = True
                        break

            if not tracking_us:
                continue

            # Extract signal info
            down_freq = None
            down_rate = None
            up_freq = None
            up_rate = None

            for sig in dish.findall("downSignal"):
                if sig.get("spacecraft") == config.DSN_SPACECRAFT_CODE:
                    down_freq = _safe_float(sig.get("frequency"))
                    down_rate = _safe_float(sig.get("dataRate"))
                    break

            for sig in dish.findall("upSignal"):
                if sig.get("spacecraft") == config.DSN_SPACECRAFT_CODE:
                    up_freq = _safe_float(sig.get("frequency"))
                    up_rate = _safe_float(sig.get("dataRate"))
                    break

            results.append(
                DSNDish(
                    station_name=current_station_name,
                    station_code=current_station_code,
                    dish_name=dish_name,
                    size_m=config.DSN_DISH_SIZES.get(dish_name, 34),
                    azimuth=float(dish.get("azimuthAngle", "0")),
                    elevation=float(dish.get("elevationAngle", "0")),
                    downlink_freq_hz=down_freq,
                    downlink_data_rate_bps=down_rate,
                    uplink_freq_hz=up_freq,
                    uplink_data_rate_bps=up_rate,
                    rtlt_seconds=rtlt,
                    downleg_range_km=downleg_range,
                )
            )

        return results
