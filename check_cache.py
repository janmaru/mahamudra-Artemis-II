#!/usr/bin/env python3
"""Test cache expiration times."""

from pathlib import Path
from artemis.cache import get_cache_age_seconds, is_cache_expired
from artemis import config

CACHE_DIR = Path("cache")

def main():
    """Display cache status and expiration times."""
    print("\n📦 ARTEMIS II - CACHE STATUS\n")
    print("=" * 70)
    
    if not CACHE_DIR.exists():
        print("❌ No cache directory found. Run the app first to generate cache.")
        return
    
    cache_files = {
        "spacecraft": ("Spacecraft", "spacecraft.json"),
        "dsn": ("DSN", "dsn.json"),
        "weather": ("Weather", "weather.json"),
        "donki": ("DONKI Events", "donki.json"),
        "trajectory": ("Trajectory", "trajectory.json"),
        "photo": ("Photo", "photo.bin"),
    }
    
    for key, (label, filename) in cache_files.items():
        cache_file = CACHE_DIR / filename
        if not cache_file.exists():
            print(f"⚠️  {label:20} - NOT FOUND")
            continue
        
        age = get_cache_age_seconds(cache_file)
        expiration = config.CACHE_EXPIRATION.get(key, 3600)
        is_expired = is_cache_expired(cache_file, key)
        
        age_str = f"{age:.0f}s" if age else "?"
        exp_str = f"{expiration}s"
        status = "🔴 EXPIRED" if is_expired else "🟢 FRESH"
        
        print(f"{label:20} {age_str:>6} / {exp_str:>6}  {status}")
    
    print("=" * 70)
    print("\nℹ️  Cache files are automatically updated when APIs are fetched.")
    print("📝 Edit artemis/config.py::CACHE_EXPIRATION to change TTL values.\n")

if __name__ == "__main__":
    main()
