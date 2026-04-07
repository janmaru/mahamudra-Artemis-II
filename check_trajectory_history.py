#!/usr/bin/env python3
"""View and manage trajectory history."""

import sys
from pathlib import Path
from artemis.cache import (
    list_trajectory_history,
    load_trajectory_history_file,
    get_trajectory_history_stats,
    cleanup_trajectory_history,
)

def show_stats():
    """Display trajectory history statistics."""
    print("\n📊 TRAJECTORY HISTORY STATISTICS\n")
    print("=" * 80)
    
    stats = get_trajectory_history_stats()
    
    if stats["total_files"] == 0:
        print("No trajectory history files found.")
        print("\nℹ️  Run the application to generate trajectory history:")
        print("    python main.py")
        return
    
    print(f"Total files:          {stats['total_files']}")
    print(f"Total size:           {stats['total_size_mb']} MB")
    print(f"Size per file:        {stats['size_per_file_mb']} MB")
    print(f"Newest file:          {stats['newest_file']}")
    print(f"Oldest file:          {stats['oldest_file']}")
    print("=" * 80)


def show_list(limit: int = 10):
    """List trajectory history files."""
    print("\n📁 TRAJECTORY HISTORY FILES\n")
    
    files = list_trajectory_history()
    
    if not files:
        print("No trajectory history files found.")
        return
    
    print(f"Showing {min(limit, len(files))} of {len(files)} files:\n")
    print(f"{'Filename':<50}  {'Size':<10}  {'Age'}")
    print("-" * 80)
    
    for i, f in enumerate(files[:limit]):
        if i >= limit:
            break
        
        size_kb = f.stat().st_size / 1024
        mtime = f.stat().st_mtime
        import time
        age_seconds = time.time() - mtime
        age_str = f"{int(age_seconds)}s" if age_seconds < 3600 else f"{int(age_seconds/60)}m"
        
        print(f"{f.name:<50}  {size_kb:>8.1f}K  {age_str:>5}")
    
    if len(files) > limit:
        print(f"\n... and {len(files) - limit} more files")


def show_sample(filename: str = None):
    """Show details of a trajectory sample."""
    files = list_trajectory_history()
    
    if not files:
        print("No trajectory history files found.")
        return
    
    # Use first (newest) file if not specified
    if filename is None:
        target_file = files[0]
    else:
        target_file = None
        for f in files:
            if filename in f.name:
                target_file = f
                break
        
        if not target_file:
            print(f"File matching '{filename}' not found.")
            return
    
    print(f"\n📋 TRAJECTORY SAMPLE: {target_file.name}\n")
    
    traj = load_trajectory_history_file(target_file)
    if not traj:
        print("Failed to load trajectory data.")
        return
    
    print(f"Fetched at:          {traj.fetched_at.isoformat()}")
    print(f"Total samples:       {len(traj.samples)}")
    print(f"Current index:       {traj.current_index}")
    print()
    
    if traj.samples:
        current = traj.samples[traj.current_index]
        print(f"Current position (index {traj.current_index}):")
        print(f"  Orion:  x={current.orion.x:>10.0f}, y={current.orion.y:>10.0f}, z={current.orion.z:>10.0f} km")
        print(f"  Moon:   x={current.moon.x:>10.0f}, y={current.moon.y:>10.0f}, z={current.moon.z:>10.0f} km")
        print()
        
        first = traj.samples[0]
        last = traj.samples[-1]
        print(f"Time range:")
        print(f"  Start: {first.timestamp.isoformat()}")
        print(f"  End:   {last.timestamp.isoformat()}")


def cleanup(keep_count: int = 100):
    """Clean up old trajectory history files."""
    print(f"\n🧹 CLEANING UP TRAJECTORY HISTORY\n")
    
    deleted = cleanup_trajectory_history(keep_count)
    
    if deleted == 0:
        print(f"✓ No cleanup needed (keeping last {keep_count} files)")
    else:
        print(f"✓ Deleted {deleted} old files")
    
    stats = get_trajectory_history_stats()
    print(f"✓ Now storing {stats['total_files']} files ({stats['total_size_mb']} MB)")


def main():
    """Main CLI."""
    if len(sys.argv) < 2:
        print("\n📍 TRAJECTORY HISTORY MANAGER\n")
        print("Usage:")
        print("  python check_trajectory_history.py stats     - Show statistics")
        print("  python check_trajectory_history.py list      - List history files")
        print("  python check_trajectory_history.py list N    - Show last N files")
        print("  python check_trajectory_history.py show      - Show latest sample")
        print("  python check_trajectory_history.py show NAME - Show specific file")
        print("  python check_trajectory_history.py cleanup   - Keep last 100 files")
        print("  python check_trajectory_history.py cleanup N - Keep last N files")
        print()
        return
    
    command = sys.argv[1]
    
    if command == "stats":
        show_stats()
    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        show_list(limit)
    elif command == "show":
        filename = sys.argv[2] if len(sys.argv) > 2 else None
        show_sample(filename)
    elif command == "cleanup":
        keep_count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        cleanup(keep_count)
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
