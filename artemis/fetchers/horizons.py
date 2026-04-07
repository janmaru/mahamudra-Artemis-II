import csv
import io
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from artemis import config
from artemis.cache import cache_spacecraft, cache_trajectory
from artemis.trajectory_storage import append_trajectory_points
from artemis.compute import distance_km, distance_between, speed_km_s
from artemis.fetchers.base import BaseFetcher
from artemis.models import (
    StateVector,
    SpacecraftData,
    TrajectoryPoint,
    TrajectoryData,
    TrajectorySample,
)
from artemis.state import SharedState

logger = logging.getLogger(__name__)


class HorizonsFetcher(BaseFetcher):
    """Fetcher for JPL Horizons API — retrieves Orion and Moon ephemerides.

    Args:
        state: Shared state instance for publishing results.
    """

    _TRAJECTORY_RETRY_DELAY = 120  # seconds between retries on failure

    def __init__(self, state: SharedState):
        super().__init__(state, config.HORIZONS_INTERVAL)
        self._last_trajectory_fetch: float = 0
        self._trajectory_next_delay: float = 5.0  # first attempt after 5s

    def fetch_and_update(self) -> None:
        """Fetch current Orion + Moon state vectors and publish SpacecraftData."""
        now = datetime.now(timezone.utc)
        orion_sv = self._fetch_state_vector(config.SPACECRAFT_ID, "500@399", now)
        moon_sv = self._fetch_state_vector("301", "500@399", now)
        
        # Fetch RA/Dec from Earth center
        ra, dec = self._fetch_observer_data(config.SPACECRAFT_ID, "500@399", now)

        data = SpacecraftData(
            orion=orion_sv,
            moon=moon_sv,
            distance_earth_km=distance_km(orion_sv.x, orion_sv.y, orion_sv.z),
            distance_moon_km=distance_between(orion_sv, moon_sv),
            speed_km_s=speed_km_s(orion_sv.vx, orion_sv.vy, orion_sv.vz),
            ra=ra,
            dec=dec,
            fetched_at=datetime.now(timezone.utc),
        )
        self._state.update_spacecraft(data)
        cache_spacecraft(data)
        logger.info(
            "Horizons: Earth=%.0f km, Moon=%.0f km, Speed=%.3f km/s, RA=%.2f, Dec=%.2f",
            data.distance_earth_km, data.distance_moon_km, data.speed_km_s,
            ra if ra is not None else 0, dec if dec is not None else 0
        )

        # Trajectory refresh — separated with delay to avoid API rate limiting
        now_ts = time.monotonic()
        if now_ts - self._last_trajectory_fetch >= self._trajectory_next_delay:
            self._stop_event.wait(3)  # interruptible cooldown
            self._last_trajectory_fetch = time.monotonic()
            try:
                self._fetch_trajectory()
                self._trajectory_next_delay = config.TRAJECTORY_REFRESH_INTERVAL
            except Exception as exc:
                logger.warning("Failed to load trajectory: %s", exc)
                self._trajectory_next_delay = self._TRAJECTORY_RETRY_DELAY

    def _fetch_state_vector(self, command: str, center: str, target_time: datetime) -> StateVector:
        """Query Horizons for a body's state vector closest to target_time.

        Args:
            command: JPL body identifier.
            center: Horizons centre code.
            target_time: The timestamp we want to match.

        Returns:
            Parsed StateVector from the row closest to target_time.
        """
        start = target_time - timedelta(minutes=5)
        stop = target_time + timedelta(minutes=5)
        params = {
            "format": "json",
            "COMMAND": f"'{command}'",
            "OBJ_DATA": "NO",
            "MAKE_EPHEM": "YES",
            "EPHEM_TYPE": "VECTORS",
            "CENTER": f"'{center}'",
            "START_TIME": f"'{start.strftime('%Y-%m-%d %H:%M')}'",
            "STOP_TIME": f"'{stop.strftime('%Y-%m-%d %H:%M')}'",
            "STEP_SIZE": "'1 min'",
            "OUT_UNITS": "KM-S",
            "REF_SYSTEM": "J2000",
            "CSV_FORMAT": "YES",
        }
        data = self._get_json(config.HORIZONS_URL, params)
        return self._parse_result(data["result"], target_time)

    def _fetch_observer_data(self, command: str, center: str, target_time: datetime) -> tuple[Optional[float], Optional[float]]:
        """Query Horizons for observer quantities (RA/Dec) closest to target_time."""
        start = target_time - timedelta(minutes=5)
        stop = target_time + timedelta(minutes=5)
        params = {
            "format": "json",
            "COMMAND": f"'{command}'",
            "OBJ_DATA": "NO",
            "MAKE_EPHEM": "YES",
            "EPHEM_TYPE": "OBSERVER",
            "CENTER": f"'{center}'",
            "START_TIME": f"'{start.strftime('%Y-%m-%d %H:%M')}'",
            "STOP_TIME": f"'{stop.strftime('%Y-%m-%d %H:%M')}'",
            "STEP_SIZE": "'1 min'",
            "QUANTITIES": "'1'",
            "REF_SYSTEM": "ICRF",
            "CSV_FORMAT": "YES",
        }
        try:
            data = self._get_json(config.HORIZONS_URL, params)
            return self._parse_observer_row(data["result"], target_time)
        except Exception as exc:
            logger.warning("Failed to fetch observer data: %s", exc)
            return None, None

    def _parse_observer_row(self, result_text: str, target_time: datetime) -> tuple[float, float]:
        """Parse RA/Dec from observer CSV output."""
        soe_idx = result_text.find("$$SOE")
        eoe_idx = result_text.find("$$EOE")
        if soe_idx == -1 or eoe_idx == -1:
            raise ValueError("No observer data in Horizons response")
        
        block = result_text[soe_idx + 5 : eoe_idx].strip()
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        
        best_row = None
        min_diff = float('inf')
        
        for line in lines:
            reader = csv.reader(io.StringIO(line))
            fields = [f.strip() for f in next(reader)]
            dt = self._parse_horizons_date(fields[1])
            diff = abs((dt - target_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                best_row = fields
        
        if not best_row:
            raise ValueError("No matching observer rows found")

        # Column 3 is RA, Column 4 is DEC in degrees (CSV_FORMAT='YES' + QUANTITIES='1')
        return float(best_row[3]), float(best_row[4])

    def _fetch_trajectory(self) -> None:
        """Fetch and sync mission trajectory for both Orion and Moon."""
        # Ensure we start from launch or slightly before to see the full path
        now = datetime.now(timezone.utc)
        start_time = config.LAUNCH_TIME - timedelta(hours=1)
        end_time = now + timedelta(hours=1)

        try:
            orion_rows = self._fetch_path(config.SPACECRAFT_ID, "500@399", start_time, end_time)
        except ValueError as e:
            if "no ephemeris data" in str(e).lower():
                # Fallback: request only the last 2 days if the full mission is unavailable
                logger.warning("Full mission trajectory unavailable, falling back to recent data")
                start_time = max(config.LAUNCH_TIME, now - timedelta(days=2))
                orion_rows = self._fetch_path(config.SPACECRAFT_ID, "500@399", start_time, end_time)
            else:
                raise

        moon_rows = self._fetch_path("301", "500@399", start_time, end_time)

        # Sync by timestamp using a dictionary to ensure we only pair matching times
        moon_map = {dt: (x, y, z) for x, y, z, dt in moon_rows}
        
        samples: list[TrajectorySample] = []
        for ox, oy, oz, odt in orion_rows:
            if odt in moon_map:
                mx, my, mz = moon_map[odt]
                samples.append(
                    TrajectorySample(
                        timestamp=odt,
                        orion=TrajectoryPoint(x=ox, y=oy, z=oz),
                        moon=TrajectoryPoint(x=mx, y=my, z=mz)
                    )
                )

        if not samples:
            raise ValueError("No synchronized trajectory points found")

        # Current index is the one closest to 'now'
        current_index = 0
        min_diff = float('inf')
        for i, s in enumerate(samples):
            diff = abs((s.timestamp - now).total_seconds())
            if diff < min_diff:
                min_diff = diff
                current_index = i

        self._state.update_trajectory(
            TrajectoryData(
                samples=tuple(samples),
                current_index=current_index,
                fetched_at=datetime.now(timezone.utc),
            )
        )
        trajectory_data = TrajectoryData(
            samples=tuple(samples),
            current_index=current_index,
            fetched_at=datetime.now(timezone.utc),
        )
        cache_trajectory(trajectory_data)
        
        # Store points incrementally (only new points added to storage)
        append_trajectory_points(samples)
        
        logger.info("Trajectory synced: %d samples, current_idx=%d", len(samples), current_index)

    def _fetch_path(
        self, command: str, center: str, start: datetime, end: datetime
    ) -> list[tuple[float, float, float, datetime]]:
        """Fetch a series of position vectors over a time range."""
        params = {
            "format": "json",
            "COMMAND": f"'{command}'",
            "OBJ_DATA": "NO",
            "MAKE_EPHEM": "YES",
            "EPHEM_TYPE": "VECTORS",
            "CENTER": f"'{center}'",
            "START_TIME": f"'{start.strftime('%Y-%m-%d %H:%M')}'",
            "STOP_TIME": f"'{end.strftime('%Y-%m-%d %H:%M')}'",
            "STEP_SIZE": "'5 min'",
            "OUT_UNITS": "KM-S",
            "REF_SYSTEM": "J2000",
            "CSV_FORMAT": "YES",
        }
        data = self._get_json(config.HORIZONS_URL, params)
        return self._parse_all_rows(data["result"])

    def _parse_all_rows(self, result_text: str) -> list[tuple[float, float, float, datetime]]:
        """Parse all CSV rows, returning (x, y, z, dt)."""
        soe_idx = result_text.find("$$SOE")
        eoe_idx = result_text.find("$$EOE")
        if soe_idx == -1 or eoe_idx == -1:
            raise ValueError(f"Horizons returned no ephemeris data")
        block = result_text[soe_idx + 5 : eoe_idx].strip()
        lines = [line.strip() for line in block.splitlines() if line.strip()]

        points: list[tuple[float, float, float, datetime]] = []
        for line in lines:
            reader = csv.reader(io.StringIO(line))
            fields = [f.strip() for f in next(reader)]
            if len(fields) < 5: continue
            dt = self._parse_horizons_date(fields[1])
            points.append((float(fields[2]), float(fields[3]), float(fields[4]), dt))
        return points

    def _parse_result(self, result_text: str, target_time: datetime) -> StateVector:
        """Parse the ephemeris row closest to target_time."""
        soe_idx = result_text.find("$$SOE")
        eoe_idx = result_text.find("$$EOE")
        if soe_idx == -1 or eoe_idx == -1:
            raise ValueError(f"Horizons returned no ephemeris data")
        block = result_text[soe_idx + 5 : eoe_idx].strip()
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        
        best_row = None
        min_diff = float('inf')
        
        for line in lines:
            reader = csv.reader(io.StringIO(line))
            fields = [f.strip() for f in next(reader)]
            dt = self._parse_horizons_date(fields[1])
            diff = abs((dt - target_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                best_row = fields
        
        if not best_row:
            raise ValueError("No matching rows found")

        return StateVector(
            epoch=self._parse_horizons_date(best_row[1]),
            x=float(best_row[2]),
            y=float(best_row[3]),
            z=float(best_row[4]),
            vx=float(best_row[5]),
            vy=float(best_row[6]),
            vz=float(best_row[7]),
        )

    @staticmethod
    def _parse_horizons_date(s: str) -> datetime:
        s = s.replace("A.D. ", "").strip()
        # Horizons sometimes uses '*' for inferred dates or different precisions
        s = s.replace("*", "").strip()
        
        # Common Horizons formats:
        # 1. 2026-Apr-07 01:00:00.0000
        # 2. 2026-Apr-07 01:00
        # 3. 2026-Apr-07 01:00:00
        
        for fmt in (
            "%Y-%b-%d %H:%M:%S.%f",
            "%Y-%b-%d %H:%M:%S",
            "%Y-%b-%d %H:%M",
        ):
            try:
                return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse Horizons date: '{s}'")
