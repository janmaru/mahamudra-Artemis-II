from rich.layout import Layout


def make_layout() -> Layout:
    """Build the Rich terminal layout.

    Returns:
        Layout with named regions: header, solar_map, photo, spacecraft, dsn,
        weather, alerts, status.
    """
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="upper", ratio=6),
        Layout(name="lower", ratio=2),
        Layout(name="status", size=3),
    )
    layout["upper"].split_row(
        Layout(name="left_stack", ratio=2),
        Layout(name="right_stack", ratio=2),
    )
    layout["left_stack"].split_row(
        Layout(name="solar_map", ratio=1),
        Layout(name="photo", ratio=1),
    )
    layout["right_stack"].split_column(
        Layout(name="spacecraft", ratio=1),
        Layout(name="dsn", ratio=1),
    )
    layout["lower"].split_row(
        Layout(name="weather", ratio=1),
        Layout(name="alerts", ratio=1),
    )
    return layout
