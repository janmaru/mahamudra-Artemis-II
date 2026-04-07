from typing import Optional

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from artemis import config
from artemis.compute import staleness_seconds, staleness_style
from artemis.models import SpaceWeatherData, DONKIData


_EVENT_ICONS = {
    "FLR": ("[!]", "bright_yellow"),
    "CME": ("[*]", "bright_cyan"),
    "GST": ("[S]", "bright_red"),
}

_EVENT_LABELS = {
    "FLR": "Solar Flare",
    "CME": "CME",
    "GST": "Geomag. Storm",
}


def render(
    weather: Optional[SpaceWeatherData],
    donki: Optional[DONKIData],
    errors: dict[str, str],
) -> Panel:
    """Render the alerts & events panel with storm warnings and DONKI events.

    Args:
        weather: Current SpaceWeatherData for real-time storm alerts, or None.
        donki: Current DONKIData with recent space weather events, or None.
        errors: Dict of fetcher-name to error-message for displaying failures.

    Returns:
        Rich Panel showing active alerts and recent DONKI events.
    """
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Content", ratio=1)

    # Storm warnings from current space weather
    has_alert = False
    if weather and weather.kp and weather.kp.kp >= 5:
        alert = Text()
        alert.append(" GEOMAGNETIC STORM ", style="bold bright_white on red")
        alert.append(f"  Kp = {weather.kp.kp:.1f}", style="bold red")
        table.add_row(alert)
        has_alert = True

    if weather and weather.scales and weather.scales.s >= 2:
        alert = Text()
        alert.append(" SOLAR RADIATION ", style="bold bright_white on red")
        alert.append(f"  S{weather.scales.s}", style="bold red")
        table.add_row(alert)
        has_alert = True

    if weather and weather.solar_wind and weather.solar_wind.bz is not None:
        if weather.solar_wind.bz < -10:
            alert = Text()
            alert.append(" Bz STRONGLY SOUTH ", style="bold bright_white on dark_red")
            alert.append(f"  {weather.solar_wind.bz:+.1f} nT", style="bold red")
            table.add_row(alert)
            has_alert = True

    # DONKI events
    if donki is None:
        error_msg = errors.get("DONKIFetcher")
        if error_msg:
            table.add_row(Text(f"DONKI error: {error_msg[:60]}", style="red"))
        elif not has_alert:
            table.add_row(Text("Awaiting event data...", style="dim italic"))
    elif not donki.events and not has_alert:
        table.add_row(Text("No recent space weather events", style="green"))
    else:
        # Show up to 8 most recent events
        for event in donki.events[:8]:
            icon, icon_style = _EVENT_ICONS.get(event.event_type, ("[-]", "dim"))
            label = _EVENT_LABELS.get(event.event_type, event.event_type)

            row = Text()
            row.append(icon, style=icon_style)
            row.append(f" {label}", style="bright_white")
            if event.class_type:
                row.append(f" {event.class_type}", style="bold")
            if event.start_time:
                # Truncate to readable format
                time_str = event.start_time[:16].replace("T", " ")
                row.append(f"  {time_str}", style="dim")
            table.add_row(row)

    # Staleness
    if donki:
        stale = staleness_seconds(donki.fetched_at)
        style = staleness_style(stale, config.DONKI_INTERVAL)
        minutes = int(stale // 60)
        if minutes > 0:
            table.add_row(Text(f"Updated {minutes}m ago", style=style))
        else:
            table.add_row(Text(f"Updated {int(stale)}s ago", style=style))

    return Panel(table, title="[bold]ALERTS & EVENTS[/bold]", border_style="red")
