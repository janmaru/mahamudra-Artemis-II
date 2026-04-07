from typing import Optional

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from artemis import config
from artemis.compute import staleness_seconds, staleness_style
from artemis.models import SpaceWeatherData


def _kp_style(kp: float) -> tuple[str, str]:
    """Return Rich style and human label for a given Kp index.

    Args:
        kp: Planetary K-index value (0-9).

    Returns:
        Tuple of (rich_style, descriptive_label).
    """
    if kp < 4:
        return "green", "Quiet"
    elif kp < 5:
        return "yellow", "Unsettled"
    elif kp < 6:
        return "bold red", "STORM (G1)"
    elif kp < 7:
        return "bold red", "STORM (G2)"
    elif kp < 8:
        return "bold bright_red", "STORM (G3)"
    elif kp < 9:
        return "bold bright_red on dark_red", "SEVERE STORM (G4)"
    else:
        return "bold bright_white on red", "EXTREME STORM (G5)"


def _scale_style(level: int) -> str:
    """Return Rich style for a NOAA scale level.

    Args:
        level: NOAA scale level (0-5).

    Returns:
        Rich style string.
    """
    if level == 0:
        return "green"
    elif level <= 2:
        return "yellow"
    return "bold red"


def render(data: Optional[SpaceWeatherData], errors: dict[str, str]) -> Panel:
    """Render the space weather panel with Kp index, NOAA scales, and solar wind.

    Args:
        data: Current SpaceWeatherData snapshot, or None if not yet available.
        errors: Dict of fetcher-name to error-message for displaying failures.

    Returns:
        Rich Panel showing space weather conditions or error/waiting state.
    """
    if data is None:
        error_msg = errors.get("SWPCFetcher")
        if error_msg:
            content = Text(f"Error: {error_msg[:80]}", style="red")
        else:
            content = Text("Awaiting weather data...", style="dim italic")
        return Panel(content, title="[bold]SPACE WEATHER[/bold]", border_style="yellow")

    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Label", style="dim", ratio=1)
    table.add_column("Value", ratio=2)

    # Kp Index
    if data.kp:
        style, label = _kp_style(data.kp.kp)
        kp_text = Text()
        kp_text.append(f"{data.kp.kp:.1f}", style=style)
        kp_text.append(f" ({label})", style=style)
        table.add_row("Kp Index", kp_text)
    else:
        table.add_row("Kp Index", Text("N/A", style="dim"))

    # NOAA Scales
    if data.scales:
        scales_text = Text()
        scales_text.append(f"G{data.scales.g}", style=_scale_style(data.scales.g))
        scales_text.append("  ", style="dim")
        scales_text.append(f"S{data.scales.s}", style=_scale_style(data.scales.s))
        scales_text.append("  ", style="dim")
        scales_text.append(f"R{data.scales.r}", style=_scale_style(data.scales.r))
        table.add_row("NOAA Scales", scales_text)
    else:
        table.add_row("NOAA Scales", Text("N/A", style="dim"))

    # Solar Wind
    if data.solar_wind:
        sw = data.solar_wind
        if sw.speed is not None:
            table.add_row("Wind Speed", Text(f"{sw.speed:.0f} km/s", style="bright_white"))
        if sw.density is not None:
            table.add_row("Wind Density", Text(f"{sw.density:.1f} p/cm\u00b3", style="bright_white"))
        if sw.bz is not None:
            bz_style = "bold red" if sw.bz < -10 else ("yellow" if sw.bz < -5 else "bright_white")
            table.add_row("IMF Bz", Text(f"{sw.bz:+.1f} nT", style=bz_style))
        if sw.temperature is not None:
            temp_k = sw.temperature
            table.add_row("Wind Temp", Text(f"{temp_k:,.0f} K", style="dim"))
    else:
        table.add_row("Solar Wind", Text("N/A", style="dim"))

    # Staleness
    stale = staleness_seconds(data.fetched_at)
    style = staleness_style(stale, config.SWPC_INTERVAL)
    minutes = int(stale // 60)
    if minutes > 0:
        table.add_row("", Text(f"Updated {minutes}m ago", style=style))
    else:
        table.add_row("", Text(f"Updated {int(stale)}s ago", style=style))

    return Panel(table, title="[bold]SPACE WEATHER[/bold]", border_style="yellow")
