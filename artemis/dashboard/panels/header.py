from datetime import datetime, timezone
from typing import Optional

from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from artemis import config
from artemis.compute import (
    mission_elapsed_time,
    format_met,
    flight_day,
    mission_phase_from_telemetry,
)
from artemis.models import SpacecraftData


def render(sc: Optional[SpacecraftData] = None) -> Panel:
    """Render the mission header panel with title, MET, flight day, and phase.

    Args:
        sc: Current spacecraft telemetry for phase detection, or None.

    Returns:
        Rich Panel displaying Artemis II mission status bar.
    """
    now = datetime.now(timezone.utc)
    met = mission_elapsed_time(now)
    fd = flight_day(now)
    phase = mission_phase_from_telemetry(sc)

    title = Text("ARTEMIS II", style="bold bright_white")
    title.append(" - ORION ", style="bold white")
    title.append('"INTEGRITY"', style="bold cyan")

    met_text = Text()
    met_text.append("MET: ", style="dim")
    met_text.append(format_met(met), style="bold bright_green")
    met_text.append("  |  ", style="dim")
    met_text.append(f"Flight Day {fd}", style="bold yellow")
    met_text.append("  |  ", style="dim")
    met_text.append(f"Phase: {phase}", style="bold magenta")

    # Countdown to next major event (MT-03)
    next_event = None
    for name, ts in config.MISSION_TIMELINE:
        if ts > now:
            next_event = (name, ts - now)
            break
    
    if next_event:
        name, remaining = next_event
        met_text.append("  |  ", style="dim")
        met_text.append(f"Next: {name} in ", style="dim")
        met_text.append(format_met(remaining), style="bold orange1")

    content = Text()
    content.append_text(title)
    content.append("\n")
    content.append_text(met_text)

    return Panel(
        Align.center(content),
        style="bright_blue",
        border_style="bright_blue",
    )
