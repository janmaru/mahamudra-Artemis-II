#!/usr/bin/env python3
"""Artemis II Real-Time Terminal Dashboard."""

import logging
import sys


def _setup_windows_identity():
    """Set up Windows taskbar identity so the app can be pinned with its own icon."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from pathlib import Path

        # Register as a separate app in the taskbar (not grouped with python.exe)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "nasa.artemis2.dashboard"
        )

        # Set console window title
        ctypes.windll.kernel32.SetConsoleTitleW("Artemis II")

        # Set console window icon
        icon_path = Path(__file__).parent / "artemis.ico"
        if icon_path.exists():
            import ctypes.wintypes
            LR_LOADFROMFILE = 0x10
            IMAGE_ICON = 1
            ICON_SMALL = 0
            ICON_BIG = 1
            WM_SETICON = 0x80

            h_icon = ctypes.windll.user32.LoadImageW(
                None, str(icon_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE
            )
            if h_icon:
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon)
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon)
    except Exception:
        pass  # Non-critical, dashboard works fine without it


def main():
    _setup_windows_identity()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        filename="artemis.log",
    )

    from artemis.dashboard.app import DashboardApp

    app = DashboardApp()
    app.run()


if __name__ == "__main__":
    main()
