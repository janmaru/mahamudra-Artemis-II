import logging
from datetime import datetime, timezone, timedelta

from artemis import config
from artemis.cache import cache_donki
from artemis.fetchers.base import BaseFetcher
from artemis.models import SpaceEvent, DONKIData
from artemis.state import SharedState

logger = logging.getLogger(__name__)


def _parse_event_time(s: str) -> datetime:
    """Parse a DONKI event timestamp string to a datetime for sorting.

    Args:
        s: ISO-8601-ish timestamp string from DONKI (e.g. "2026-04-04T22:54Z").

    Returns:
        Parsed datetime, or datetime.min if parsing fails.
    """
    for fmt in ("%Y-%m-%dT%H:%MZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.min


class DONKIFetcher(BaseFetcher):
    """Fetcher for NASA DONKI API — solar flares, CMEs, and geomagnetic storms.

    Args:
        state: Shared state instance for publishing results.
    """

    def __init__(self, state: SharedState):
        super().__init__(state, config.DONKI_INTERVAL)

    def fetch_and_update(self) -> None:
        """Fetch FLR, CME, and GST events from the last 3 days and publish DONKIData."""
        now = datetime.now(timezone.utc)
        start = (now - timedelta(days=3)).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")

        events: list[SpaceEvent] = []
        events.extend(self._fetch_events("FLR", start, end))
        events.extend(self._fetch_events("CME", start, end))
        events.extend(self._fetch_events("GST", start, end))

        # Sort by start time descending (most recent first)
        events.sort(key=lambda e: _parse_event_time(e.start_time), reverse=True)

        donki_data = DONKIData(events=tuple(events), fetched_at=datetime.now(timezone.utc))
        self._state.update_donki(donki_data)
        cache_donki(donki_data)
        logger.info("DONKI: %d events in last 3 days", len(events))

    def _fetch_events(self, event_type: str, start: str, end: str) -> list[SpaceEvent]:
        """Fetch a specific event type from DONKI.

        Args:
            event_type: DONKI event code ("FLR", "CME", or "GST").
            start: Start date in YYYY-MM-DD format.
            end: End date in YYYY-MM-DD format.

        Returns:
            List of SpaceEvent instances; empty list on failure.
        """
        try:
            url = f"{config.DONKI_BASE_URL}{event_type}"
            data = self._get_json(url, params={"startDate": start, "endDate": end})
            if not isinstance(data, list):
                return []

            results: list[SpaceEvent] = []
            for item in data:
                start_time = ""
                class_type = None

                if event_type == "FLR":
                    start_time = item.get("beginTime", item.get("peakTime", ""))
                    class_type = item.get("classType")
                elif event_type == "CME":
                    start_time = item.get("startTime", "")
                    analyses = item.get("cmeAnalyses", [])
                    if analyses:
                        half_angle = analyses[0].get("halfAngle")
                        class_type = f"HA={half_angle}" if half_angle else None
                elif event_type == "GST":
                    start_time = item.get("startTime", "")
                    kp_values = item.get("allKpIndex", [])
                    if kp_values:
                        max_kp = max(
                            (k.get("kpIndex", 0) for k in kp_values), default=0
                        )
                        class_type = f"Kp={max_kp}"

                results.append(
                    SpaceEvent(
                        event_type=event_type,
                        start_time=start_time,
                        class_type=class_type,
                        link=item.get("link"),
                    )
                )
            return results

        except Exception as exc:
            logger.warning("Failed to fetch DONKI %s: %s", event_type, exc)
            return []
