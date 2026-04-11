import logging
import signal
import threading
import time
import webbrowser
import sys

logger = logging.getLogger(__name__)

from rich.console import Console
from rich.live import Live

from artemis import config
from artemis.cache import load_spacecraft, load_dsn, load_weather, load_donki, load_trajectory, load_photo
from artemis.state import SharedState
from artemis.fetchers.horizons import HorizonsFetcher
from artemis.fetchers.dsn import DSNFetcher
from artemis.fetchers.swpc import SWPCFetcher
from artemis.fetchers.donki import DONKIFetcher
from artemis.fetchers.nasa_images import NASAImagesFetcher
from artemis.dashboard.layout import make_layout
from artemis.dashboard.panels import header, spacecraft, dsn, weather, alerts, status, solar_map, photo
from artemis.dashboard.photo_viewer import save_and_open_photo
from artemis.photo_carousel import get_current_carousel_photo


class DashboardApp:
    """Main application — starts fetcher threads and runs the Rich terminal dashboard."""

    def __init__(self):
        self.state = SharedState()
        self._load_cached_state()
        self.console = Console()
        self.fetchers = [
            HorizonsFetcher(self.state),
            DSNFetcher(self.state),
            SWPCFetcher(self.state),
            DONKIFetcher(self.state),
            NASAImagesFetcher(self.state),
        ]
        self._stop_event = threading.Event()
        self._last_photo_url: str = ""

    def _load_cached_state(self) -> None:
        """Pre-populate SharedState from disk cache so panels are never empty on startup."""
        loaders = [
            ("spacecraft", load_spacecraft, self.state.update_spacecraft),
            ("dsn", load_dsn, self.state.update_dsn),
            ("weather", load_weather, self.state.update_weather),
            ("donki", load_donki, self.state.update_donki),
            ("trajectory", load_trajectory, self.state.update_trajectory),
            ("photo", load_photo, self.state.update_photo),
        ]
        for name, loader, updater in loaders:
            try:
                data = loader(allow_stale=True)
                if data is not None:
                    updater(data)
                    logger.info("Loaded cached %s data", name)
            except Exception as exc:
                logger.warning("Failed to load cached %s data: %s", name, exc)

    def _key_listener(self) -> None:
        """Listen for keyboard input in a separate thread."""
        try:
            import readchar
        except ImportError:
            logger.warning("readchar not available - key input disabled")
            return
        
        while not self._stop_event.is_set():
            try:
                key = readchar.readkey()
                if key.lower() == 'p':
                    # Get current photo and open it
                    _, _, _, _, _, photo_data, _ = self.state.snapshot()
                    if photo_data:
                        save_and_open_photo(photo_data)
                        logger.info("Opened photo: %s", photo_data.title)
                elif key.lower() == 't':
                    # Open trajectory viewer
                    try:
                        from artemis.dashboard.trajectory_native_viewer import open_trajectory_viewer
                        open_trajectory_viewer()
                        logger.info("Opened trajectory viewer")
                    except Exception as e:
                        logger.error("Failed to open trajectory viewer: %s", e)
                elif key.lower() == 'q':
                    self._stop_event.set()
            except (readchar.exceptions.NonBlockingIOError, Exception):
                pass
            time.sleep(0.1)  # Prevent busy loop

    def run(self) -> None:
        """Start all fetcher threads and enter the 1 Hz render loop."""
        signal.signal(signal.SIGINT, self._handle_signal)

        for f in self.fetchers:
            f.start()
        
        # Start key listener thread
        key_thread = threading.Thread(target=self._key_listener, daemon=True)
        key_thread.start()

        layout = make_layout()

        try:
            with Live(
                layout,
                console=self.console,
                refresh_per_second=1,
                screen=True,
            ) as live:
                while not self._stop_event.is_set():
                    try:
                        sc, dsn_data, wx, donki_data, traj, photo_data, errors = self.state.snapshot()
                        # Rotate carousel photo every cycle
                        carousel_photo = get_current_carousel_photo(rotation_seconds=6)
                        current_photo = carousel_photo or photo_data
                        layout["header"].update(header.render(sc))
                        layout["solar_map"].update(
                            solar_map.render(traj, sc, errors)
                        )
                        layout["photo"].update(
                            photo.render(current_photo, errors)
                        )
                        layout["spacecraft"].update(
                            spacecraft.render(sc, errors)
                        )
                        layout["dsn"].update(dsn.render(dsn_data, errors))
                        layout["weather"].update(weather.render(wx, errors))
                        layout["alerts"].update(
                            alerts.render(wx, donki_data, errors)
                        )
                        layout["status"].update(
                            status.render(sc, dsn_data, wx, donki_data, traj, errors)
                        )
                    except Exception:
                        logger.exception("Render loop error")
                    time.sleep(config.RENDER_INTERVAL)
        except KeyboardInterrupt:
            pass
        finally:
            for f in self.fetchers:
                f.stop()

    def _handle_signal(self, signum, frame):
        """Handle SIGINT by setting the stop flag."""
        self._stop_event.set()
