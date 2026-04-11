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

    After Splashdown, the MET is frozen at the final value and the phase
    shows "Mission Complete" instead of a countdown.

    Args:
        sc: Current spacecraft telemetry for phase detection, or None.

    Returns:
        Rich Panel displaying Artemis II mission status bar.
    """
    now = datetime.now(timezone.utc)
    phase = mission_phase_from_telemetry(sc)

    # After splashdown: freeze MET and flight day at final values
    timeline = {name: dt for name, dt in config.MISSION_TIMELINE}
    splashdown_time = timeline.get("Splashdown")
    mission_complete = splashdown_time is not None and now >= splashdown_time
    if mission_complete:
        met = mission_elapsed_time(splashdown_time)
        fd = flight_day(splashdown_time)
    else:
        met = mission_elapsed_time(now)
        fd = flight_day(now)

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

    if mission_complete:
        # Show elapsed time since splashdown
        since = now - splashdown_time
        hours = int(since.total_seconds() // 3600)
        minutes = int((since.total_seconds() % 3600) // 60)
        met_text.append("  |  ", style="dim")
        met_text.append(f"Splashdown +{hours}h {minutes:02d}m", style="bold bright_green")
    else:
        # Countdown to next major event
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
