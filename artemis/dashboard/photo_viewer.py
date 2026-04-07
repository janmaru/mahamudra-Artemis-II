"""Photo viewer for displaying full mission images."""

import io
import logging
import shutil
import tempfile
from pathlib import Path

from PIL import Image

from artemis.models import MissionPhoto

logger = logging.getLogger(__name__)


def save_and_open_photo(photo: MissionPhoto) -> None:
    """Open photo viewer window (native Tkinter).
    
    Args:
        photo: MissionPhoto object with image data
    """
    try:
        logger.info("Opening native photo viewer for: %s", photo.title)
        from artemis.dashboard.native_viewer import open_photo_viewer
        open_photo_viewer(current_photo=photo)
        logger.info("Photo viewer opened successfully")
    except Exception as e:
        logger.error("Failed to open photo viewer: %s", e, exc_info=True)


def save_and_open_photo_fallback(photo: MissionPhoto) -> None:
    """Fallback: Save photo to temp file and open with default image viewer.
    
    Args:
        photo: MissionPhoto object with image data
    """
    try:
        # Save to temporary file
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / f"artemis_photo_{photo.fetched_at.timestamp():.0f}.jpg"
        
        # Write image data
        with open(temp_file, "wb") as f:
            f.write(photo.image_data)
        
        # Open with default viewer
        import subprocess
        import platform
        
        if platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", str(temp_file)])
        elif platform.system() == "Windows":
            import os
            os.startfile(str(temp_file))
        else:  # Linux
            subprocess.Popen(["xdg-open", str(temp_file)])
            
    except Exception as e:
        logger.error("Failed to open photo: %s", e)


def display_photo_fullscreen(photo: MissionPhoto) -> None:
    """Display photo in terminal at maximum size using PIL Image.
    
    This attempts to show the image using PIL's default viewer.
    
    Args:
        photo: MissionPhoto object with image data
    """
    try:
        img = Image.open(io.BytesIO(photo.image_data))
        img.show()
    except Exception as e:
        print(f"Failed to display photo: {e}")


def get_photo_info(photo: MissionPhoto) -> dict:
    """Get information about a photo.
    
    Args:
        photo: MissionPhoto object
        
    Returns:
        Dict with photo metadata and image info
    """
    try:
        img = Image.open(io.BytesIO(photo.image_data))
        return {
            "title": photo.title,
            "url": photo.url,
            "published": photo.published,
            "size_bytes": len(photo.image_data),
            "image_format": img.format,
            "image_width": img.width,
            "image_height": img.height,
            "image_size_mb": len(photo.image_data) / (1024 * 1024),
        }
    except Exception as e:
        return {
            "error": str(e),
            "size_bytes": len(photo.image_data),
        }
