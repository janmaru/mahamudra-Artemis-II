#!/usr/bin/env python3
"""View and manage the photo carousel."""

import sys
from artemis.photo_carousel import (
    get_carousel_photos,
    get_carousel_stats,
    get_current_carousel_photo,
    clear_carousel,
)


def show_stats():
    """Display carousel statistics."""
    print("\n📸 PHOTO CAROUSEL STATISTICS\n")
    print("=" * 80)
    
    stats = get_carousel_stats()
    
    if stats["total_photos"] == 0:
        print("No photos in carousel.")
        print("\nℹ️  Run the application to collect photos:")
        print("    python main.py")
        print("=" * 80)
        return
    
    print(f"Total photos:            {stats['total_photos']}")
    print(f"Total storage:           {stats['total_size_mb']} MB")
    print(f"Size per photo:          {stats['size_per_photo_mb']} MB")
    print()
    print(f"Oldest:                  {stats['oldest_photo']}")
    print(f"Newest:                  {stats['newest_photo']}")
    print("=" * 80)
    print()
    print("Rotation: Photos change every 24 hours")


def show_list():
    """List all photos in carousel."""
    print("\n📁 CAROUSEL PHOTOS\n")
    print("=" * 80)
    
    photos = get_carousel_photos()
    
    if not photos:
        print("No photos in carousel.")
        return
    
    print(f"Total: {len(photos)} photos\n")
    print(f"{'#':<3} {'Title':<40} {'Size':<10} {'Added'}")
    print("-" * 80)
    
    for i, (photo_file, meta) in enumerate(photos, 1):
        title = meta.get("title", "Unknown")[:39]
        size_kb = photo_file.stat().st_size / 1024
        added = meta.get("added_at", "Unknown")[:19]
        print(f"{i:<3} {title:<40} {size_kb:>8.1f}K  {added}")


def show_current():
    """Show current carousel photo."""
    print("\n🎯 CURRENT CAROUSEL PHOTO\n")
    print("=" * 80)
    
    photo = get_current_carousel_photo(rotation_seconds=6)
    
    if not photo:
        print("No photo in carousel.")
        return
    
    print(f"Title:       {photo.title}")
    print(f"Published:   {photo.published}")
    print(f"URL:         {photo.url}")
    print(f"Size:        {len(photo.image_data) / 1024:.1f} KB")
    print(f"Fetched:     {photo.fetched_at.isoformat()}")
    print("=" * 80)


def clear_data():
    """Clear carousel."""
    print("\n🗑️  CLEARING CAROUSEL\n")
    
    response = input("Clear all carousel photos? (yes/no): ")
    if response.lower() != "yes":
        print("Cancelled.")
        return
    
    clear_carousel()
    print("✓ Carousel cleared")


def main():
    """Main CLI."""
    if len(sys.argv) < 2:
        print("\n📸 PHOTO CAROUSEL MANAGER\n")
        print("Usage:")
        print("  python check_carousel.py stats    - Show statistics")
        print("  python check_carousel.py list     - List all photos")
        print("  python check_carousel.py current  - Show current photo")
        print("  python check_carousel.py clear    - Clear all photos")
        print()
        return
    
    command = sys.argv[1]
    
    if command == "stats":
        show_stats()
    elif command == "list":
        show_list()
    elif command == "current":
        show_current()
    elif command == "clear":
        clear_data()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
