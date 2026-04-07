from typing import Optional

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from artemis import config
from artemis.compute import staleness_seconds, staleness_style
from artemis.models import DSNData


def _format_freq(hz: float | None) -> str:
    """Format a frequency in Hz to a human-readable GHz/MHz string.

    Args:
        hz: Frequency in Hertz, or None.

    Returns:
        Formatted string (e.g. "8.43 GHz") or "-" if None/zero.
    """
    if hz is None or hz < 1:
        return "-"
    ghz = hz / 1e9
    if ghz >= 1:
        return f"{ghz:.2f} GHz"
    mhz = hz / 1e6
    return f"{mhz:.1f} MHz"


def _format_rate(bps: float | None) -> str:
    """Format a data rate in bps to a human-readable Mbps/kbps/bps string.

    Args:
        bps: Data rate in bits per second, or None.

    Returns:
        Formatted string (e.g. "1.2 Mbps") or "-" if None/zero.
    """
    if bps is None or bps < 1:
        return "-"
    if bps >= 1e6:
        return f"{bps / 1e6:.1f} Mbps"
    if bps >= 1e3:
        return f"{bps / 1e3:.0f} kbps"
    return f"{bps:.0f} bps"


def render(data: Optional[DSNData], errors: dict[str, str]) -> Panel:
    """Render the DSN communications panel with active dishes and signal info.

    Args:
        data: Current DSNData snapshot, or None if not yet available.
        errors: Dict of fetcher-name to error-message for displaying failures.

    Returns:
        Rich Panel showing DSN link status or error/waiting state.
    """
    if data is None:
        error_msg = errors.get("DSNFetcher")
        if error_msg:
            content = Text(f"Error: {error_msg[:80]}", style="red")
        else:
            content = Text("Awaiting DSN data...", style="dim italic")
        return Panel(content, title="[bold]DSN COMMUNICATIONS[/bold]", border_style="green")

    if not data.dishes:
        table = Table(show_header=False, box=None, expand=True)
        table.add_row(Text("No active DSN link to Orion", style="dim italic"))

        stale = staleness_seconds(data.fetched_at)
        style = staleness_style(stale, config.DSN_INTERVAL)
        table.add_row(Text(f"Updated {int(stale)}s ago", style=style))

        return Panel(table, title="[bold]DSN COMMUNICATIONS[/bold]", border_style="green")

    table = Table(box=None, expand=True, padding=(0, 1))
    table.add_column("Station", style="bold")
    table.add_column("Dish")
    table.add_column("Down")
    table.add_column("Up")
    table.add_column("RTLT")

    for dish in data.dishes:
        down_info = f"{_format_freq(dish.downlink_freq_hz)} {_format_rate(dish.downlink_data_rate_bps)}"
        up_info = f"{_format_freq(dish.uplink_freq_hz)} {_format_rate(dish.uplink_data_rate_bps)}"
        rtlt = f"{dish.rtlt_seconds:.2f}s" if dish.rtlt_seconds else "-"
        dish_display = f"{dish.dish_name} ({dish.size_m}m)"

        table.add_row(
            Text(dish.station_name, style="bright_green"),
            dish_display,
            down_info,
            up_info,
            rtlt,
        )

    # Range info from first dish
    if data.dishes[0].downleg_range_km:
        range_km = data.dishes[0].downleg_range_km
        table.add_row(
            "", "", "",
            Text(f"Range: {range_km:,.0f} km", style="dim"),
            "",
        )

    stale = staleness_seconds(data.fetched_at)
    style = staleness_style(stale, config.DSN_INTERVAL)
    table.add_row("", "", "", "", Text(f"Updated {int(stale)}s ago", style=style))

    return Panel(table, title="[bold]DSN COMMUNICATIONS[/bold]", border_style="green")
