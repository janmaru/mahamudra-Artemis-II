"""Image carousel - stores and rotates through multiple cached photos."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from artemis.models import MissionPhoto

logger = logging.getLogger(__name__)

PHOTO_CAROUSEL_DIR = Path(__file__).parent.parent / "cache" / "photos"


def ensure_carousel_dir() -> Path:
    """Create photo carousel directory if it doesn't exist."""
    PHOTO_CAROUSEL_DIR.mkdir(parents=True, exist_ok=True)
    return PHOTO_CAROUSEL_DIR


def add_photo_to_carousel(photo: MissionPhoto) -> None:
    """Add a photo to the carousel (avoids duplicates by title).
    
    Args:
        photo: MissionPhoto to add
    """
    ensure_carousel_dir()
    
    # Use title as unique identifier (slugified)
    slug = photo.title.lower().replace(" ", "_")[:30]
    timestamp = str(int(datetime.now(timezone.utc).timestamp()))
    filename = f"{slug}_{timestamp}.bin"
    
    photo_file = PHOTO_CAROUSEL_DIR / filename
    meta_file = PHOTO_CAROUSEL_DIR / f"{slug}_{timestamp}.json"
    
    try:
        # Check if this title already exists (avoid duplicates)
        existing = list(PHOTO_CAROUSEL_DIR.glob(f"{slug}_*.json"))
        if existing:
            # Compare with most recent
            existing.sort(reverse=True)
            try:
                with open(existing[0], "r") as f:
                    existing_meta = json.load(f)
                if existing_meta.get("title") == photo.title:
                    logger.debug("Photo already in carousel: %s", photo.title)
                    return
            except Exception:
                pass
        
        # Save new photo
        with open(photo_file, "wb") as f:
            f.write(photo.image_data)
        
        with open(meta_file, "w") as f:
            json.dump({
                "title": photo.title,
                "image_url": photo.image_url,
                "url": photo.url,
                "published": photo.published,
                "size_bytes": len(photo.image_data),
                "added_at": datetime.now(timezone.utc).isoformat(),
                "fetched_at": photo.fetched_at.isoformat(),
            }, f, indent=2)
        
        logger.info("Added photo to carousel: %s", photo.title)
    except Exception as exc:
        logger.warning("Failed to add photo to carousel: %s", exc)


def get_carousel_photos() -> list[tuple[Path, dict]]:
    """Get all photos in carousel, sorted by newest first.
    
    Returns:
        List of (photo_file, metadata) tuples
    """
    ensure_carousel_dir()
    
    photos = []
    for meta_file in sorted(PHOTO_CAROUSEL_DIR.glob("*.json"), reverse=True):
        try:
            with open(meta_file, "r") as f:
                meta = json.load(f)
            
            # Find corresponding photo file
            photo_file = meta_file.with_suffix(".bin")
            if photo_file.exists():
                photos.append((photo_file, meta))
        except Exception as exc:
            logger.warning("Failed to load photo metadata %s: %s", meta_file, exc)
    
    return photos


def get_current_carousel_photo(rotation_seconds: int = 6) -> Optional[MissionPhoto]:
    """Get current photo from carousel based on rotation schedule.

    Rotates through photos every `rotation_seconds` seconds.

    Args:
        rotation_seconds: Seconds between photo rotations (default: 6)

    Returns:
        MissionPhoto or None if carousel is empty
    """
    try:
        photos = get_carousel_photos()
        if not photos:
            logger.debug("Carousel is empty")
            return None

        # Calculate which photo to show based on time
        now = datetime.now(timezone.utc)
        photo_index = int(now.timestamp() / rotation_seconds) % len(photos)
        
        photo_file, meta = photos[photo_index]
        
        with open(photo_file, "rb") as f:
            image_data = f.read()
        
        # Safely parse the fetched_at datetime
        fetched_at_str = meta.get("fetched_at")
        if fetched_at_str:
            try:
                fetched_at = datetime.fromisoformat(fetched_at_str)
            except (ValueError, TypeError) as e:
                logger.warning("Failed to parse datetime %s: %s", fetched_at_str, e)
                fetched_at = datetime.now(timezone.utc)
        else:
            fetched_at = datetime.now(timezone.utc)
        
        return MissionPhoto(
            title=meta.get("title", "Unknown"),
            image_data=image_data,
            image_url=meta.get("image_url", ""),
            url=meta.get("url", ""),
            published=meta.get("published", ""),
            fetched_at=fetched_at,
        )
    except Exception as exc:
        logger.warning("Failed to load carousel photo: %s", exc)
        return None


def get_carousel_stats() -> dict:
    """Get statistics about the photo carousel.
    
    Returns:
        Dict with carousel info
    """
    ensure_carousel_dir()
    
    photos = get_carousel_photos()
    total_size = sum(pf.stat().st_size for pf, _ in photos)
    
    return {
        "total_photos": len(photos),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "size_per_photo_mb": round(total_size / len(photos) / (1024 * 1024), 2) if photos else 0,
        "oldest_photo": photos[-1][1].get("added_at") if photos else None,
        "newest_photo": photos[0][1].get("added_at") if photos else None,
    }


def clear_carousel() -> None:
    """Clear all carousel photos."""
    ensure_carousel_dir()
    
    try:
        for f in PHOTO_CAROUSEL_DIR.glob("*"):
            f.unlink()
        logger.info("Cleared photo carousel")
    except Exception as exc:
        logger.warning("Failed to clear carousel: %s", exc)
