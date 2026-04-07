import threading
import logging
import time

import requests

from artemis import config
from artemis.state import SharedState

logger = logging.getLogger(__name__)


class BaseFetcher:
    """Base class for all API fetcher threads.

    Provides a retry-capable HTTP client, a polling loop with configurable
    interval, and graceful stop via threading.Event.

    Args:
        state: Shared state instance for publishing results.
        interval: Polling interval in seconds between fetch cycles.
    """

    def __init__(self, state: SharedState, interval: float):
        self._state = state
        self._interval = interval
        self._stop_event = threading.Event()
        self._session = requests.Session()

    def fetch_and_update(self) -> None:
        """Fetch data from the API and update shared state. Subclasses must override."""
        raise NotImplementedError

    def _get_json(self, url: str, params: dict | None = None) -> dict | list:
        """Perform a GET request and return the parsed JSON response.

        Args:
            url: Target URL.
            params: Optional query-string parameters.

        Returns:
            Parsed JSON as dict or list.
        """
        return self._request(url, params, parse_json=True)

    def _get_text(self, url: str, params: dict | None = None) -> str:
        """Perform a GET request and return the raw response body.

        Args:
            url: Target URL.
            params: Optional query-string parameters.

        Returns:
            Response body as a string.
        """
        return self._request(url, params, parse_json=False)

    def _request(self, url: str, params: dict | None, parse_json: bool):
        """Internal HTTP GET with retry logic.

        Args:
            url: Target URL.
            params: Optional query-string parameters.
            parse_json: If True, parse response as JSON; otherwise return text.

        Returns:
            Parsed JSON (dict/list) or response text.

        Raises:
            requests.HTTPError: On non-retryable HTTP errors.
            requests.ConnectionError: After all retries exhausted.
        """
        last_exc = None
        for attempt in range(config.MAX_RETRIES):
            try:
                resp = self._session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
                if resp.status_code >= 500:
                    raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
                resp.raise_for_status()
                return resp.json() if parse_json else resp.text
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                logger.warning(
                    "%s attempt %d/%d failed: %s",
                    self.__class__.__name__, attempt + 1, config.MAX_RETRIES, exc,
                )
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code >= 500:
                    last_exc = exc
                    logger.warning(
                        "%s attempt %d/%d server error: %s",
                        self.__class__.__name__, attempt + 1, config.MAX_RETRIES, exc,
                    )
                    if attempt < config.MAX_RETRIES - 1:
                        time.sleep(2 ** attempt)
                else:
                    raise
        raise last_exc  # type: ignore[misc]

    def run(self) -> None:
        """Main polling loop — calls fetch_and_update() then sleeps for the interval."""
        while not self._stop_event.is_set():
            try:
                self.fetch_and_update()
            except Exception as exc:
                logger.exception("%s error: %s", self.__class__.__name__, exc)
                self._state.set_error(self.__class__.__name__, str(exc))
            self._stop_event.wait(self._interval)

    def start(self) -> threading.Thread:
        """Start the fetcher as a daemon thread.

        Returns:
            The started Thread instance.
        """
        t = threading.Thread(target=self.run, daemon=True, name=self.__class__.__name__)
        t.start()
        return t

    def stop(self) -> None:
        """Signal the polling loop to stop after the current cycle."""
        self._stop_event.set()
        try:
            self._session.close()
        except Exception:
            pass
