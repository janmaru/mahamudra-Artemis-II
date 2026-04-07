#!/usr/bin/env python3
"""View and manage incremental trajectory storage."""

import sys
from artemis.trajectory_storage import (
    get_trajectory_stats,
    load_trajectory_data,
    clear_trajectory_data,
)

def show_stats():
    """Display trajectory storage statistics."""
    print("\n📊 TRAJECTORY STORAGE STATISTICS\n")
    print("=" * 80)
    
    stats = get_trajectory_stats()
    
    if stats["total_points"] == 0:
        print("No trajectory data stored yet.")
        print("\nℹ️  Run the application to generate trajectory data:")
        print("    python main.py")
        print("=" * 80)
        return
    
    print(f"Total points stored:     {stats['total_points']:,} points")
    print(f"Storage size:            {stats['file_size_kb']:.1f} KB")
    print(f"Size per point:          {stats['file_size_kb'] / stats['total_points']:.2f} KB/point" if stats["total_points"] > 0 else "N/A")
    print()
    print(f"Earliest data:           {stats['earliest_timestamp']}")
    print(f"Latest data:             {stats['latest_timestamp']}")
    print(f"Last update:             {stats['last_update']}")
    print("=" * 80)
    print()
    print("Format: JSONL (JSON Lines) - Incremental append-only storage")
    print("Location: cache/trajectory_data/")
    print("  • index.json - Metadata")
    print("  • points.jsonl - Individual trajectory points")


def show_data():
    """Show loaded trajectory data."""
    print("\n📋 LOADED TRAJECTORY DATA\n")
    print("=" * 80)
    
    traj = load_trajectory_data()
    
    if not traj:
        print("No trajectory data available.")
        return
    
    print(f"Total samples:           {len(traj.samples)}")
    print(f"Current index:           {traj.current_index}")
    print(f"Fetched at:              {traj.fetched_at.isoformat()}")
    print()
    
    if traj.samples:
        current = traj.samples[traj.current_index]
        print(f"Current position (index {traj.current_index}):")
        print(f"  Timestamp: {current.timestamp.isoformat()}")
        print(f"  Orion:  x={current.orion.x:>10.0f}, y={current.orion.y:>10.0f}, z={current.orion.z:>10.0f} km")
        print(f"  Moon:   x={current.moon.x:>10.0f}, y={current.moon.y:>10.0f}, z={current.moon.z:>10.0f} km")
        print()
        
        first = traj.samples[0]
        last = traj.samples[-1]
        time_span = (last.timestamp - first.timestamp).total_seconds() / 3600
        print(f"Time coverage:")
        print(f"  Start: {first.timestamp.isoformat()}")
        print(f"  End:   {last.timestamp.isoformat()}")
        print(f"  Span:  {time_span:.1f} hours ({time_span/24:.1f} days)")
    
    print("=" * 80)


def clear_data():
    """Clear all trajectory data."""
    print("\n🗑️  CLEARING TRAJECTORY DATA\n")
    
    response = input("Are you sure? This will delete all stored trajectory points. (yes/no): ")
    if response.lower() != "yes":
        print("Cancelled.")
        return
    
    clear_trajectory_data()
    print("✓ Trajectory data cleared")


def main():
    """Main CLI."""
    if len(sys.argv) < 2:
        print("\n📍 TRAJECTORY STORAGE MANAGER\n")
        print("Usage:")
        print("  python check_trajectory_storage.py stats   - Show storage statistics")
        print("  python check_trajectory_storage.py data    - Show loaded data")
        print("  python check_trajectory_storage.py clear   - Clear all data")
        print()
        return
    
    command = sys.argv[1]
    
    if command == "stats":
        show_stats()
    elif command == "data":
        show_data()
    elif command == "clear":
        clear_data()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
