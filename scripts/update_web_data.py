#!/usr/bin/env python3
"""
Update web dashboard data by fetching from NASA APIs.
Saves data as JSON files for static GitHub Pages hosting.
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen, Request

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from artemis.state import SharedState
from artemis.fetchers.horizons import HorizonsFetcher
from artemis.fetchers.dsn import DSNFetcher
from artemis.fetchers.swpc import SWPCFetcher
from artemis.fetchers.donki import DONKIFetcher
from artemis.fetchers.nasa_images import NASAImagesFetcher
from artemis import config

# Output directory
WEB_DATA_DIR = Path(__file__).parent.parent / 'web' / 'data'
WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)


def serialize_data(data):
    """Convert data objects to JSON-serializable dicts"""
    if data is None:
        return None
    
    if hasattr(data, '__dict__'):
        return {
            k: serialize_data(v) for k, v in data.__dict__.items()
            if not k.startswith('_') and k != 'image_data'
        }
    elif isinstance(data, (list, tuple)):
        return [serialize_data(item) for item in data]
    elif isinstance(data, dict):
        return {k: serialize_data(v) for k, v in data.items()}
    else:
        return data


def save_json(filename, data):
    """Save data to JSON file with timestamp"""
    filepath = WEB_DATA_DIR / filename
    
    output = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'data': serialize_data(data),
    }
    
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"  Saved {filename}")


def fetch_photos(max_photos: int = 10) -> list[dict]:
    """Fetch multiple photos directly from NASA IOTD RSS feed."""
    print(f"\nFetching photos from RSS feed (max {max_photos})...")
    req = Request(config.NASA_IOTD_URL, headers={"User-Agent": "Artemis-II-Dashboard/1.0"})
    with urlopen(req, timeout=15) as resp:
        text = resp.read().decode()

    root = ET.fromstring(text)
    channel = root.find("channel")
    if channel is None:
        return []

    photos = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()

        img_url = _extract_image_url(item)
        if not img_url:
            continue

        photos.append({
            "title": title,
            "image_url": img_url,
            "url": link,
            "published": pub_date,
        })
        if len(photos) >= max_photos:
            break

    print(f"  Found {len(photos)} photos")
    return photos


def _extract_image_url(item: ET.Element) -> str | None:
    """Extract image URL from RSS item (same logic as NASAImagesFetcher)."""
    enc = item.find("enclosure")
    if enc is not None:
        url = enc.get("url", "")
        if url and any(url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png")):
            return url

    desc = item.findtext("description") or ""
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc)
    if match:
        return match.group(1)

    for tag in ("content:encoded", "{http://purl.org/rss/1.0/modules/content/}encoded"):
        content = item.findtext(tag) or ""
        if content:
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)

    return None


def main():
    print(f"Updating web dashboard data...")
    print(f"Output directory: {WEB_DATA_DIR}")

    state = SharedState()

    # Fetch telemetry data
    fetcher_configs = [
        ('spacecraft.json', HorizonsFetcher),
        ('dsn.json', DSNFetcher),
        ('weather.json', SWPCFetcher),
        ('alerts.json', DONKIFetcher),
    ]

    for filename, FetcherClass in fetcher_configs:
        try:
            print(f"\nFetching {filename}...")
            fetcher = FetcherClass(state)
            fetcher.fetch_and_update()

            sc, dsn_data, wx, donki_data, traj, photo_data, errors = state.snapshot()

            if filename == 'spacecraft.json':
                save_json(filename, sc)
            elif filename == 'dsn.json':
                save_json(filename, dsn_data)
            elif filename == 'weather.json':
                save_json(filename, wx)
            elif filename == 'alerts.json':
                save_json(filename, donki_data)

        except Exception as e:
            print(f"  ERROR fetching {filename}: {e}")
            import traceback
            traceback.print_exc()

    # Fetch photos directly from RSS (up to 10)
    try:
        photos = fetch_photos(max_photos=10)
        save_json('photos.json', photos)
    except Exception as e:
        print(f"  ERROR fetching photos: {e}")
        import traceback
        traceback.print_exc()

    print(f"\nData update complete")


if __name__ == '__main__':
    main()

