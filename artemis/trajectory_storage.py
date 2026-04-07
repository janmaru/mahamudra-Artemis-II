"""Incremental trajectory storage in JSON format.

Stores trajectory points incrementally to avoid re-downloading complete datasets.
New points are appended to existing data rather than replaced.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from artemis.models import TrajectoryData, TrajectorySample, TrajectoryPoint

logger = logging.getLogger(__name__)

TRAJECTORY_DATA_DIR = Path(__file__).parent.parent / "cache" / "trajectory_data"


def ensure_trajectory_data_dir() -> Path:
    """Create trajectory data directory if it doesn't exist."""
    TRAJECTORY_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return TRAJECTORY_DATA_DIR


def get_trajectory_index_file() -> Path:
    """Get path to trajectory index file."""
    return TRAJECTORY_DATA_DIR / "index.json"


def get_trajectory_points_file() -> Path:
    """Get path to trajectory points file."""
    return TRAJECTORY_DATA_DIR / "points.jsonl"


def _load_index() -> dict:
    """Load trajectory index metadata.
    
    Index structure:
    {
        "last_update": "2026-04-07T11:43:23.204949+00:00",
        "total_points": 589,
        "earliest_timestamp": "2026-04-05T11:43:00+00:00",
        "latest_timestamp": "2026-04-07T12:43:00+00:00",
        "current_index": 576
    }
    """
    ensure_trajectory_data_dir()
    index_file = get_trajectory_index_file()
    
    if not index_file.exists():
        return {
            "last_update": None,
            "total_points": 0,
            "earliest_timestamp": None,
            "latest_timestamp": None,
            "current_index": 0,
        }
    
    try:
        with open(index_file, "r") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to load trajectory index: %s", exc)
        return {}


def _save_index(index: dict) -> None:
    """Save trajectory index metadata."""
    ensure_trajectory_data_dir()
    index_file = get_trajectory_index_file()
    
    try:
        with open(index_file, "w") as f:
            json.dump(index, f, indent=2)
    except Exception as exc:
        logger.warning("Failed to save trajectory index: %s", exc)


def _load_all_points() -> list[TrajectorySample]:
    """Load all trajectory points from JSONL file."""
    ensure_trajectory_data_dir()
    points_file = get_trajectory_points_file()
    
    if not points_file.exists():
        return []
    
    points: list[TrajectorySample] = []
    try:
        with open(points_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                sample = TrajectorySample(
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    orion=TrajectoryPoint(
                        x=data["orion"]["x"],
                        y=data["orion"]["y"],
                        z=data["orion"]["z"],
                    ),
                    moon=TrajectoryPoint(
                        x=data["moon"]["x"],
                        y=data["moon"]["y"],
                        z=data["moon"]["z"],
                    ),
                )
                points.append(sample)
    except Exception as exc:
        logger.warning("Failed to load trajectory points: %s", exc)
    
    return points


def append_trajectory_points(new_samples: list[TrajectorySample]) -> None:
    """Append new trajectory points incrementally (JSONL format).
    
    Only adds new points that don't already exist (by timestamp).
    This avoids re-downloading the entire dataset.
    
    Args:
        new_samples: List of TrajectorySample to add
    """
    ensure_trajectory_data_dir()
    
    if not new_samples:
        return
    
    # Load existing points to avoid duplicates
    existing_points = _load_all_points()
    existing_timestamps = {p.timestamp for p in existing_points}
    
    # Find new points (those not already stored)
    points_to_add = [
        s for s in new_samples
        if s.timestamp not in existing_timestamps
    ]
    
    if not points_to_add:
        logger.debug("No new trajectory points to store")
        return
    
    # Append new points to JSONL file (one JSON object per line)
    points_file = get_trajectory_points_file()
    try:
        with open(points_file, "a") as f:
            for sample in points_to_add:
                line = json.dumps({
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
                })
                f.write(line + "\n")
        
        logger.info("Stored %d new trajectory points", len(points_to_add))
    except Exception as exc:
        logger.warning("Failed to append trajectory points: %s", exc)
    
    # Update index
    all_points = _load_all_points()
    if all_points:
        index = {
            "last_update": datetime.now(timezone.utc).isoformat(),
            "total_points": len(all_points),
            "earliest_timestamp": all_points[0].timestamp.isoformat(),
            "latest_timestamp": all_points[-1].timestamp.isoformat(),
        }
        _save_index(index)


def load_trajectory_data() -> Optional[TrajectoryData]:
    """Load all stored trajectory data.
    
    Returns:
        TrajectoryData with all stored points, or None if no data
    """
    ensure_trajectory_data_dir()
    
    points = _load_all_points()
    if not points:
        return None
    
    # Find current index (closest to now)
    now = datetime.now(timezone.utc)
    current_index = 0
    min_diff = float('inf')
    
    for i, sample in enumerate(points):
        diff = abs((sample.timestamp - now).total_seconds())
        if diff < min_diff:
            min_diff = diff
            current_index = i
    
    return TrajectoryData(
        samples=tuple(points),
        current_index=current_index,
        fetched_at=datetime.now(timezone.utc),
    )


def get_trajectory_stats() -> dict:
    """Get trajectory storage statistics.
    
    Returns:
        Dict with storage info
    """
    ensure_trajectory_data_dir()
    
    index = _load_index()
    points_file = get_trajectory_points_file()
    
    file_size_kb = 0
    if points_file.exists():
        file_size_kb = points_file.stat().st_size / 1024
    
    return {
        "total_points": index.get("total_points", 0),
        "file_size_kb": round(file_size_kb, 1),
        "earliest_timestamp": index.get("earliest_timestamp"),
        "latest_timestamp": index.get("latest_timestamp"),
        "last_update": index.get("last_update"),
    }


def clear_trajectory_data() -> None:
    """Clear all stored trajectory data."""
    ensure_trajectory_data_dir()
    
    index_file = get_trajectory_index_file()
    points_file = get_trajectory_points_file()
    
    try:
        if index_file.exists():
            index_file.unlink()
        if points_file.exists():
            points_file.unlink()
        logger.info("Cleared trajectory storage")
    except Exception as exc:
        logger.warning("Failed to clear trajectory data: %s", exc)
