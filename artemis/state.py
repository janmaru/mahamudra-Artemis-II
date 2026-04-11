import threading
from typing import Optional

from artemis.models import (
    SpacecraftData,
    DSNData,
    SpaceWeatherData,
    DONKIData,
    TrajectoryData,
    MissionPhoto,
)


class SharedState:
    """Thread-safe shared state bridging fetcher threads and the render loop.

    All public methods acquire a single Lock before reading or writing,
    ensuring consistent snapshots even under concurrent updates.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._spacecraft: Optional[SpacecraftData] = None
        self._dsn: Optional[DSNData] = None
        self._weather: Optional[SpaceWeatherData] = None
        self._donki: Optional[DONKIData] = None
        self._trajectory: Optional[TrajectoryData] = None
        self._photo: Optional[MissionPhoto] = None
        self._errors: dict[str, str] = {}

    def update_spacecraft(self, data: SpacecraftData) -> None:
        """Store new spacecraft data and clear any Horizons error.

        Args:
            data: Fresh SpacecraftData from HorizonsFetcher.
        """
        with self._lock:
            self._spacecraft = data
            self._errors.pop("HorizonsFetcher", None)

    def update_spacecraft_stale(self, data: SpacecraftData, error: str) -> None:
        """Store stale spacecraft data while preserving the error flag.

        Used when live Horizons data is unavailable and we fall back to
        cached data.  The error is kept so the UI can show a [stale] banner.

        Args:
            data: Stale SpacecraftData loaded from cache.
            error: Error message describing why fresh data is unavailable.
        """
        with self._lock:
            self._spacecraft = data
            self._errors["HorizonsFetcher"] = error

    def update_dsn(self, data: DSNData) -> None:
        """Store new DSN data and clear any DSN error.

        Args:
            data: Fresh DSNData from DSNFetcher.
        """
        with self._lock:
            self._dsn = data
            self._errors.pop("DSNFetcher", None)

    def update_weather(self, data: SpaceWeatherData) -> None:
        """Store new space weather data and clear any SWPC error.

        Args:
            data: Fresh SpaceWeatherData from SWPCFetcher.
        """
        with self._lock:
            self._weather = data
            self._errors.pop("SWPCFetcher", None)

    def update_donki(self, data: DONKIData) -> None:
        """Store new DONKI data and clear any DONKI error.

        Args:
            data: Fresh DONKIData from DONKIFetcher.
        """
        with self._lock:
            self._donki = data
            self._errors.pop("DONKIFetcher", None)

    def update_trajectory(self, data: TrajectoryData) -> None:
        """Store new trajectory data for the ASCII plot.

        Args:
            data: Fresh TrajectoryData from HorizonsFetcher.
        """
        with self._lock:
            self._trajectory = data

    def update_photo(self, data: MissionPhoto) -> None:
        """Store latest mission photo.

        Args:
            data: Fresh MissionPhoto from NASAImagesFetcher.
        """
        with self._lock:
            self._photo = data
            self._errors.pop("NASAImagesFetcher", None)

    def set_error(self, source: str, message: str) -> None:
        """Record a fetcher error to be displayed in the dashboard.

        Args:
            source: Fetcher class name (e.g. "HorizonsFetcher").
            message: Human-readable error description.
        """
        with self._lock:
            self._errors[source] = message

    def get_photo_url(self) -> Optional[str]:
        """Return the source URL of the current mission photo."""
        with self._lock:
            return self._photo.url if self._photo else None

    def snapshot(
        self,
    ) -> tuple[
        Optional[SpacecraftData],
        Optional[DSNData],
        Optional[SpaceWeatherData],
        Optional[DONKIData],
        Optional[TrajectoryData],
        Optional[MissionPhoto],
        dict[str, str],
    ]:
        """Return a consistent copy of all current state.

        Returns:
            Tuple of (spacecraft, dsn, weather, donki, trajectory, photo, errors).
        """
        with self._lock:
            return (
                self._spacecraft,
                self._dsn,
                self._weather,
                self._donki,
                self._trajectory,
                self._photo,
                dict(self._errors),
            )
