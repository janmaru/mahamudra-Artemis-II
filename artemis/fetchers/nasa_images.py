"""Fetcher for NASA Image of the Day RSS feed — mission photos from Orion."""

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from artemis import config
from artemis.cache import cache_photo
from artemis.photo_carousel import add_photo_to_carousel, get_current_carousel_photo
from artemis.fetchers.base import BaseFetcher
from artemis.models import MissionPhoto
from artemis.state import SharedState

logger = logging.getLogger(__name__)


class NASAImagesFetcher(BaseFetcher):
    """Fetch the latest mission photo from NASA IOTD RSS feed."""

    def __init__(self, state: SharedState):
        super().__init__(state, config.NASA_IMAGES_INTERVAL)

    def fetch_and_update(self) -> None:
        text = self._get_text(config.NASA_IOTD_URL)
        root = ET.fromstring(text)
        channel = root.find("channel")
        if channel is None:
            return

        # Download all photos from feed (up to 10) and add to carousel
        added = 0
        for item in channel.findall("item"):
            if added >= 10:
                break

            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()

            img_url = self._extract_image_url(item)
            if not img_url:
                continue

            try:
                resp = self._session.get(img_url, timeout=config.REQUEST_TIMEOUT)
                resp.raise_for_status()
                img_data = resp.content
            except Exception as exc:
                logger.warning("Failed to fetch image %s: %s", img_url, exc)
                continue

            photo = MissionPhoto(
                title=title,
                image_data=img_data,
                image_url=img_url,
                url=link,
                published=pub_date,
                fetched_at=datetime.now(timezone.utc),
            )
            add_photo_to_carousel(photo)
            added += 1

        logger.info("Carousel: added %d photos", added)

        # Set initial photo from carousel
        carousel_photo = get_current_carousel_photo(rotation_seconds=6)
        if carousel_photo:
            self._state.update_photo(carousel_photo)
            cache_photo(carousel_photo)

    @staticmethod
    def _extract_image_url(item: ET.Element) -> str | None:
        """Extract an image URL from an RSS item."""
        # Try <enclosure>
        enc = item.find("enclosure")
        if enc is not None:
            url = enc.get("url", "")
            if url and any(url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png")):
                return url

        # Try extracting from description HTML
        desc = item.findtext("description") or ""
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc)
        if match:
            return match.group(1)

        # Try content:encoded
        for tag in ("content:encoded", "{http://purl.org/rss/1.0/modules/content/}encoded"):
            content = item.findtext(tag) or ""
            if content:
                match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)

        return None
