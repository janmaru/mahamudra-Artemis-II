from typing import Optional

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from artemis import config
from artemis.compute import (
    km_to_miles,
    format_number,
    format_ra_dec,
    staleness_seconds,
    staleness_style,
    get_best_perspective,
    mission_phase_from_telemetry,
)
from artemis.models import SpacecraftData


def _render_mission_complete(data: Optional[SpacecraftData]) -> Panel:
    """Render spacecraft panel after mission completion."""
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Label", style="dim", ratio=1)
    table.add_column("Value", ratio=2)

    table.add_row("", Text("Mission Complete — Orion recovered", style="bold bright_green"))
    table.add_row("", Text(""))

    if data is not None:
        table.add_row("", Text("Last tracked position:", style="dim italic"))
        table.add_row(
            "Earth Distance",
            Text(f"{format_number(data.distance_earth_km)} km", style="dim"),
        )
        table.add_row(
            "Speed",
            Text(f"{format_number(data.speed_km_s, 3)} km/s", style="dim"),
        )
        table.add_row(
            "Last Epoch",
            Text(data.orion.epoch.strftime("%Y-%m-%d %H:%M UTC"), style="dim"),
        )

    return Panel(table, title="[bold]SPACECRAFT[/bold]", border_style="blue")


def render(data: Optional[SpacecraftData], errors: dict[str, str]) -> Panel:
    """Render the spacecraft info panel with distances, speed, and position.

    Args:
        data: Current SpacecraftData snapshot, or None if not yet available.
        errors: Dict of fetcher-name to error-message for displaying failures.

    Returns:
        Rich Panel showing Orion telemetry or error/waiting state.
    """
    # After splashdown, show mission complete instead of stale telemetry
    if mission_phase_from_telemetry() == "Mission Complete":
        return _render_mission_complete(data)

    if data is None:
        error_msg = errors.get("HorizonsFetcher")
        if error_msg:
            content = Text(f"Error: {error_msg[:80]}", style="red")
        else:
            content = Text("Awaiting first data...", style="dim italic")
        return Panel(content, title="[bold]SPACECRAFT[/bold]", border_style="blue")

    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Label", style="dim", ratio=1)
    table.add_column("Value", ratio=2)

    # Show error banner when data is stale (from cache fallback)
    error_msg = errors.get("HorizonsFetcher")
    if error_msg:
        table.add_row("", Text(f"[stale] {error_msg[:60]}", style="yellow"))

    perspective = get_best_perspective(data)

    # Distance from Earth
    earth_km = format_number(data.distance_earth_km)
    earth_mi = format_number(km_to_miles(data.distance_earth_km))
    table.add_row(
        "Earth Distance",
        Text(f"{earth_km} km ({earth_mi} mi)", style="bright_white"),
    )

    # Distance from Moon
    moon_km = format_number(data.distance_moon_km)
    moon_mi = format_number(km_to_miles(data.distance_moon_km))
    table.add_row(
        "Moon Distance",
        Text(f"{moon_km} km ({moon_mi} mi)", style="bright_white"),
    )

    # Speed
    speed_kms = format_number(data.speed_km_s, 3)
    speed_kmh = format_number(data.speed_km_s * 3600)
    table.add_row(
        "Speed",
        Text(f"{speed_kms} km/s ({speed_kmh} km/h)", style="bright_white"),
    )

    # Sky Position
    sky_pos = format_ra_dec(data.ra, data.dec)
    table.add_row(
        "Sky Position",
        Text(sky_pos, style="bright_cyan"),
    )

    # Position vector (compact) — relative to current perspective
    if perspective == "Moon":
        x_k = (data.orion.x - data.moon.x) / 1000
        y_k = (data.orion.y - data.moon.y) / 1000
        z_k = (data.orion.z - data.moon.z) / 1000
        label = "Pos (Moon-rel)"
    else:
        x_k = data.orion.x / 1000
        y_k = data.orion.y / 1000
        z_k = data.orion.z / 1000
        label = "Pos (Earth-rel)"

    table.add_row(
        f"{label} x10³km",
        Text(f"{x_k:+.1f} / {y_k:+.1f} / {z_k:+.1f}", style="dim"),
    )

    # Epoch
    table.add_row(
        "Data Epoch",
        Text(data.orion.epoch.strftime("%Y-%m-%d %H:%M:%S UTC"), style="dim"),
    )

    # Staleness
    stale = staleness_seconds(data.fetched_at)
    style = staleness_style(stale, config.HORIZONS_INTERVAL)
    table.add_row("", Text(f"Updated {int(stale)}s ago", style=style))

    return Panel(table, title="[bold]SPACECRAFT[/bold]", border_style="blue")
