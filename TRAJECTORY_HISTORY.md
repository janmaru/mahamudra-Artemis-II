# Trajectory History Storage

## Overview

Artemis II automatically saves **historical trajectory data** in a dedicated directory to preserve mission data over time. Each trajectory fetch is saved with a timestamp for analysis and historical tracking.

## Storage Location

```
cache/
├── trajectory_history/
│   ├── trajectory_2026-04-07_11-43-23.json
│   ├── trajectory_2026-04-07_12-03-45.json
│   ├── trajectory_2026-04-07_12-24-12.json
│   └── ... more files
```

## File Naming

Files are named with the trajectory's fetch timestamp:
```
trajectory_YYYY-MM-DD_HH-MM-SS.json
```

Example: `trajectory_2026-04-07_11-43-23.json` was fetched on April 7, 2026 at 11:43:23 UTC

## File Size and Content

Each trajectory history file contains:
- **Samples**: 500-600+ position points for Orion and Moon
- **File size**: ~180-200 KB per file
- **Time coverage**: Typically 2 days of trajectory data
- **Metadata**: Fetch timestamp and current spacecraft index

Example structure:
```json
{
  "samples": [
    {
      "timestamp": "2026-04-05T11:43:00+00:00",
      "orion": {"x": ..., "y": ..., "z": ...},
      "moon": {"x": ..., "y": ..., "z": ...}
    },
    ...
  ],
  "current_index": 576,
  "fetched_at": "2026-04-07T11:43:23.204949+00:00"
}
```

## Checking History

Use `check_trajectory_history.py` to manage trajectory history:

### Show Statistics
```bash
python check_trajectory_history.py stats
```
Output:
```
📊 TRAJECTORY HISTORY STATISTICS

================================================================================
Total files:          1
Total size:           0.18 MB
Size per file:        0.18 MB
Newest file:          trajectory_2026-04-07_11-43-23.json
Oldest file:          trajectory_2026-04-07_11-43-23.json
================================================================================
```

### List Files
```bash
python check_trajectory_history.py list          # Show last 10 files
python check_trajectory_history.py list 20       # Show last 20 files
```

### Show Details
```bash
python check_trajectory_history.py show          # Show latest trajectory
python check_trajectory_history.py show 2026-04-07_11-43-23  # Show specific file
```

Output:
```
📋 TRAJECTORY SAMPLE: trajectory_2026-04-07_11-43-23.json

Fetched at:          2026-04-07T11:43:23.204949+00:00
Total samples:       589
Current index:       576

Current position (index 576):
  Orion:  x=   -127836, y=   -370460, z=    -37687 km
  Moon:   x=    -86781, y=   -393921, z=    -35893 km

Time range:
  Start: 2026-04-05T11:43:00+00:00
  End:   2026-04-07T12:43:00+00:00
```

## Automatic Generation

Trajectory history files are automatically created when:
- The application starts
- The HorizonsFetcher successfully fetches new trajectory data
- Every 20 minutes (TRAJECTORY_REFRESH_INTERVAL in config)

**Frequency**: One file every ~10 minutes during normal operation

## Managing Storage

### Cleanup Old Files
```bash
python check_trajectory_history.py cleanup       # Keep last 100 files (default)
python check_trajectory_history.py cleanup 50    # Keep last 50 files
```

### Manual Cleanup
```bash
# Windows PowerShell
Remove-Item cache\trajectory_history\*.json -Force

# Unix/Linux/macOS
rm cache/trajectory_history/*.json
```

## Storage Estimates

- **File size**: ~180 KB per trajectory
- **Update frequency**: Every 10-20 minutes
- **Daily generation**: ~72-144 files per day
- **Daily storage**: ~13-26 MB per day
- **Monthly storage**: ~390-780 MB per month

### Disk Usage Examples

| Files | Typical Duration | Size |
|-------|-----------------|------|
| 10 | ~1-2 hours | 1.8 MB |
| 100 | ~1-2 days | 18 MB |
| 500 | ~1 week | 90 MB |
| 1000 | ~1-2 weeks | 180 MB |
| 5000 | ~1-2 months | 900 MB |

## Use Cases

### 1. Historical Analysis
Compare trajectories over time to verify mission progress:
```python
from artemis.cache import load_trajectory_history_file, list_trajectory_history

files = list_trajectory_history()
for f in files:
    traj = load_trajectory_history_file(f)
    print(f"Distance at {traj.fetched_at}: {traj.current_index} samples")
```

### 2. Mission Tracking
Review how spacecraft moved between multiple fetches

### 3. Data Validation
Verify consistency of trajectory data across multiple snapshots

### 4. Performance Analysis
Check Horizons API response times and data quality over time

### 5. Offline Playback
Reconstruct mission timeline from historical data

## Implementation Details

### Saving
Located in `artemis/cache.py`:
```python
def cache_trajectory_history(data: TrajectoryData) -> None:
    """Save trajectory snapshot to history directory with timestamp."""
```

Called automatically when new trajectory is fetched:
```python
def cache_trajectory(data: TrajectoryData) -> None:
    """Cache trajectory and save to history."""
    ensure_cache_dir()
    # ... save to cache/trajectory.json ...
    cache_trajectory_history(data)  # Also save to history
```

### Loading
```python
def load_trajectory_history_file(history_file: Path) -> Optional[TrajectoryData]:
    """Load a specific trajectory history file."""

def list_trajectory_history() -> list[Path]:
    """List all saved trajectory history files (newest first)."""
```

### Cleanup
```python
def cleanup_trajectory_history(keep_count: int = 100) -> int:
    """Remove old trajectory history files, keeping only recent ones."""
```

## Future Enhancements

Possible improvements:
- Differential compression (store only changes between snapshots)
- SQLite database for better querying
- Automatic cleanup based on age and disk space
- Historical trajectory plotting/visualization
- Trajectory diff/delta analysis tool
- Export to CSV/XLSX for external analysis
- Archive old files to compressed format (.tar.gz)

## Troubleshooting

### History Directory Not Found
The directory is created automatically on first use. If missing:
```bash
mkdir -p cache/trajectory_history
```

### Files Too Large
Use cleanup to reduce storage:
```bash
python check_trajectory_history.py cleanup 50
```

### Restore Deleted Files
History files are permanent once saved. Consider backing up:
```bash
# Backup trajectory history
cp -r cache/trajectory_history cache/trajectory_history.backup
```
