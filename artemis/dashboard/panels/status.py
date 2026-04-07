from typing import Optional, Union

from rich.panel import Panel
from rich.text import Text

from artemis import config
from artemis.compute import staleness_seconds, staleness_style
from artemis.models import SpacecraftData, DSNData, SpaceWeatherData, DONKIData, TrajectoryData

_FetchedModel = Union[SpacecraftData, DSNData, SpaceWeatherData, DONKIData]

_FETCHERS = [
    ("Horizons", "HorizonsFetcher", config.HORIZONS_INTERVAL),
    ("DSN", "DSNFetcher", config.DSN_INTERVAL),
    ("SWPC", "SWPCFetcher", config.SWPC_INTERVAL),
    ("DONKI", "DONKIFetcher", config.DONKI_INTERVAL),
]


def render(
    spacecraft: Optional[SpacecraftData],
    dsn_data: Optional[DSNData],
    weather: Optional[SpaceWeatherData],
    donki: Optional[DONKIData],
    trajectory: Optional[TrajectoryData],
    errors: dict[str, str],
) -> Panel:
    """Render a compact status bar showing each fetcher and trajectory health.

    Args:
        spacecraft: Current spacecraft data, or None.
        dsn_data: Current DSN data, or None.
        weather: Current weather data, or None.
        donki: Current DONKI data, or None.
        trajectory: Current trajectory data, or None.
        errors: Dict of fetcher-name to error-message.

    Returns:
        Rich Panel with fetcher staleness and trajectory status.
    """
    data_map: dict[str, Optional[_FetchedModel]] = {
        "HorizonsFetcher": spacecraft,
        "DSNFetcher": dsn_data,
        "SWPCFetcher": weather,
        "DONKIFetcher": donki,
    }

    content = Text()

    for i, (label, fetcher_key, interval) in enumerate(_FETCHERS):
        if i > 0:
            content.append("  |  ", style="dim")

        data = data_map[fetcher_key]
        error = errors.get(fetcher_key)

        content.append(f"{label}: ", style="dim")

        if error:
            content.append("ERR", style="bold red")
        elif data is None:
            content.append("...", style="dim italic")
        else:
            stale = staleness_seconds(data.fetched_at)
            style = staleness_style(stale, interval)
            content.append(f"{int(stale)}s", style=style)

    # Trajectory status (refreshed periodically via Horizons)
    content.append("  |  ", style="dim")
    content.append("Traj: ", style="dim")
    if trajectory is None:
        content.append("...", style="dim italic")
    else:
        stale = staleness_seconds(trajectory.fetched_at)
        style = staleness_style(stale, config.TRAJECTORY_REFRESH_INTERVAL)
        content.append(f"{int(stale)}s", style=style)

    return Panel(content, border_style="dim", height=3)
