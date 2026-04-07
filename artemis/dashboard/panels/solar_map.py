"""Mission trajectory panel — Simple and visible ASCII view."""

import logging
import math
import shutil
from typing import Optional

from rich.panel import Panel
from rich.text import Text

from artemis import config
from artemis.compute import (
    format_number, format_met, mission_elapsed_time,
    staleness_seconds, staleness_style, get_best_perspective,
    get_projection_axes
)
from artemis.models import TrajectoryData, SpacecraftData

logger = logging.getLogger(__name__)

_H = 16
_AXIS_NAMES = ["X", "Y", "Z"]

def _grid_width() -> int:
    cols = shutil.get_terminal_size().columns
    available = int(cols * 0.6) - 4
    return max(30, min(72, available))

def _build_view(sc: SpacecraftData, traj: Optional[TrajectoryData] = None) -> tuple[Text, str]:
    W = _grid_width()
    
    # Always use Earth-relative coordinates
    center_body, target_body = "🌍", "🌕"
    
    # Orion relative to Earth
    cur_3d = (sc.orion.x, sc.orion.y, sc.orion.z)
    
    # Moon relative to Earth (always recalculate as it moves)
    other_3d = (sc.moon.x, sc.moon.y, sc.moon.z)
    
    # No trajectory history - just show current position
    traj_3d = []
    _EXP = 0.55

    # 2. Determine best axes for projection
    all_points = [cur_3d, other_3d]
    ax1_idx, ax2_idx = get_projection_axes(all_points)
    plane_label = f"{_AXIS_NAMES[ax1_idx]}-{_AXIS_NAMES[ax2_idx]}"

    # 3. Project to 2D
    cur_p = (cur_3d[ax1_idx], cur_3d[ax2_idx])
    other_p = (other_3d[ax1_idx], other_3d[ax2_idx])

    # Calculate scale limit
    points_to_scale = [cur_p, other_p]
    scale_limit = max(math.hypot(x, y) for x, y in points_to_scale) if points_to_scale else 400000.0
    scale_limit *= 1.15

    def to_grid(x, y):
        dist = math.hypot(x, y)
        if dist < 1: return W//2, _H//2
        angle = math.atan2(y, x)
        c = (min(1.0, dist / scale_limit) ** _EXP)
        col = W//2 + int(c * math.cos(angle) * (W//2 - 3))
        row = _H//2 - int(c * math.sin(angle) * (_H//2 - 1))
        return max(0, min(W-1, col)), max(0, min(_H-1, row))

    grid = [[" " for _ in range(W)] for _ in range(_H)]
    styles = [["" for _ in range(W)] for _ in range(_H)]

    # Moon
    ec, er = to_grid(other_p[0], other_p[1])
    if 0 <= er < _H and 0 <= ec < W:
        grid[er][ec] = target_body

    # Earth (center)
    grid[_H//2][W//2] = center_body

    # Orion - magenta
    oc, orw = to_grid(cur_p[0], cur_p[1])
    if oc == W//2 and orw == _H//2: orw -= 1
    if 0 <= orw < _H and 0 <= oc < W:
        grid[orw][oc] = "◆"
        styles[orw][oc] = "bold bright_magenta"

    content = Text()
    for r in range(_H):
        for c in range(W):
            content.append(grid[r][c], style=styles[r][c])
        if r < _H - 1: content.append("\n")
    return content, plane_label

def render(trajectory: Optional[TrajectoryData], spacecraft: Optional[SpacecraftData], errors: dict[str, str]) -> Panel:
    plane_label = "X-Y"
    if spacecraft is not None:
        try:
            content, plane_label = _build_view(spacecraft, trajectory)
        except Exception:
            content = Text("Render error", style="red")
    else:
        content = Text("Awaiting data...", style="dim")
    
    content.append("\n")
    met = mission_elapsed_time()
    legend = Text(f" MET {format_met(met)} | {plane_label}", style="bright_green")
    if spacecraft:
        legend.append(f"  Earth {format_number(spacecraft.distance_earth_km)} km", style="bright_blue")
        legend.append(f"  Moon {format_number(spacecraft.distance_moon_km)} km", style="bright_yellow")
    
    legend.append(" | Press [T] to open", style="dim")
    content.append_text(legend)
    return Panel(content, title="[bold]ARTEMIS II TRAJECTORY[/bold]", border_style="bright_blue")
