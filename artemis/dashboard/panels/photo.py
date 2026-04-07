"""Mission photo panel — renders NASA images using half-block characters."""

import io
import logging
import shutil
from typing import Optional

from PIL import Image
from rich.panel import Panel
from rich.text import Text

from artemis import config
from artemis.compute import staleness_seconds, staleness_style
from artemis.models import MissionPhoto

logger = logging.getLogger(__name__)


def _photo_size() -> tuple[int, int]:
    """Calculate available image size based on terminal dimensions."""
    cols = shutil.get_terminal_size().columns
    rows = shutil.get_terminal_size().lines
    # Photo panel ≈ 1/4 of terminal width, minus panel borders/padding
    w = max(20, int(cols * 0.25) - 4)
    # Upper section height, minus panel border, title, caption lines
    h = max(8, int(rows * 0.35) - 5)
    return w, h


def _image_to_text(data: bytes, width: int, height: int) -> Text:
    """Convert image bytes to Rich Text using half-block characters (▀).

    Each character cell renders 2 vertical pixels using foreground (top)
    and background (bottom) RGB colors.
    """
    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")

    # Fit image to target dimensions preserving aspect ratio
    img_w, img_h = img.size
    target_h = height * 2  # 2 pixels per character row
    scale = min(width / img_w, target_h / img_h)
    new_w = max(1, int(img_w * scale))
    new_h = max(2, int(img_h * scale))
    # Ensure even number of vertical pixels
    if new_h % 2:
        new_h += 1
    img = img.resize((new_w, new_h), Image.LANCZOS)

    text = Text()
    for row in range(new_h // 2):
        for col in range(new_w):
            tr, tg, tb = img.getpixel((col, row * 2))
            br, bg, bb = img.getpixel((col, row * 2 + 1))
            text.append("▀", style=f"rgb({tr},{tg},{tb}) on rgb({br},{bg},{bb})")
        if row < new_h // 2 - 1:
            text.append("\n")

    return text


def render(data: Optional[MissionPhoto], errors: dict[str, str]) -> Panel:
    if data is None:
        error_msg = errors.get("NASAImagesFetcher")
        if error_msg:
            content = Text(f"Error: {error_msg[:60]}", style="red")
        else:
            content = Text("Awaiting NASA photo...", style="dim italic")
        return Panel(content, title="[bold]MISSION PHOTO[/bold]", border_style="magenta")

    w, h = _photo_size()
    try:
        content = _image_to_text(data.image_data, w, h)
    except Exception as e:
        logger.exception("Photo render failed: %s", e)
        content = Text(f"Render error: {str(e)[:30]}", style="red")

    content.append("\n")
    caption = Text()
    caption.append(data.title[:w] if len(data.title) > w else data.title, style="bold white")
    content.append_text(caption)

    content.append("\n")
    footer = Text()
    try:
        stale = staleness_seconds(data.fetched_at)
        style = staleness_style(stale, config.NASA_IMAGES_INTERVAL)
        footer.append(f"Updated {int(stale)}s ago", style=style)
    except Exception as e:
        logger.warning("Staleness calculation failed: %s", e)
        footer.append("Date unavailable", style="dim")
    
    footer.append(" | Press [P] to open", style="dim")
    content.append_text(footer)

    return Panel(
        content,
        title="[bold]MISSION PHOTO[/bold]",
        border_style="magenta",
    )
