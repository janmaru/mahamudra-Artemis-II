"""Native trajectory viewer window - 2D map + history list."""

import logging
import math
import threading
from typing import Optional

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    tk = None

from artemis.compute import get_projection_axes
from artemis.trajectory_storage import load_trajectory_data, get_trajectory_stats

logger = logging.getLogger(__name__)

_AXIS_NAMES = ["X", "Y", "Z"]
_viewer_window = None
_viewer_thread = None


class TrajectoryViewerWindow:
    """Native Tkinter window showing 2D trajectory map and history."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Artemis II - Trajectory Viewer")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a2e")

        try:
            traj_data_obj = load_trajectory_data()
            self.stats = get_trajectory_stats()
            self.traj_samples = traj_data_obj.samples if traj_data_obj else []
        except Exception as e:
            logger.error("Failed to load trajectory data: %s", e)
            self.traj_samples = []
            self.stats = {}

        self._build_ui()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg="#000000", height=40)
        header.pack(side=tk.TOP, fill=tk.X)

        tk.Label(
            header, text="ARTEMIS II - TRAJECTORY HISTORY",
            font=("Arial", 14, "bold"), bg="#000000", fg="#00d4ff"
        ).pack(pady=8)

        paned = tk.PanedWindow(self.root, orient=tk.VERTICAL, bg="#1a1a2e", sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        map_frame = tk.Frame(paned, bg="#1a1a2e", height=500)
        paned.add(map_frame, height=500)

        self.map_canvas = tk.Canvas(
            map_frame, bg="#000000",
            highlightthickness=1, highlightbackground="#00d4ff",
        )
        self.map_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.map_canvas.bind("<Configure>", lambda e: self._draw_trajectory())

        # History list
        list_frame = tk.Frame(paned, bg="#1a1a2e")
        paned.add(list_frame)

        tk.Label(
            list_frame, text="TRAJECTORY HISTORY",
            font=("Arial", 10, "bold"), bg="#1a1a2e", fg="#00d4ff"
        ).pack(anchor="w", padx=10, pady=(5, 2))

        list_canvas = tk.Canvas(list_frame, bg="#1a1a2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=list_canvas.yview)
        scrollable_frame = tk.Frame(list_canvas, bg="#1a1a2e")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all"))
        )

        list_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        list_canvas.configure(yscrollcommand=scrollbar.set)

        # Show every Nth sample to avoid creating thousands of widgets
        step = max(1, len(self.traj_samples) // 200)
        for i, sample in enumerate(reversed(self.traj_samples)):
            if i % step != 0:
                continue
            try:
                orion = sample.orion
                moon = sample.moon
                dist_earth = math.hypot(orion.x, orion.y, orion.z)
                dist_moon = math.hypot(orion.x - moon.x, orion.y - moon.y, orion.z - moon.z)

                item = tk.Frame(scrollable_frame, bg="#000000", height=30)
                item.pack(fill=tk.X, padx=2, pady=1)

                time_text = sample.timestamp.strftime("%Y-%m-%d %H:%M")
                info_text = f"{time_text}  |  Earth {dist_earth:>10,.0f} km  |  Moon {dist_moon:>10,.0f} km"

                tk.Label(
                    item, text=info_text, font=("Courier", 9),
                    bg="#000000", fg="#e0e0e0", anchor="w", justify=tk.LEFT
                ).pack(fill=tk.X, padx=8, pady=4)
            except Exception:
                continue

        list_canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

        footer = tk.Frame(self.root, bg="#1a1a2e", height=30)
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(
            footer, text=f"Total samples: {len(self.traj_samples)} | ESC to close",
            font=("Arial", 9), bg="#1a1a2e", fg="#e0e0e0"
        ).pack(pady=5)

        self.root.bind("<Escape>", lambda e: self.root.quit())

    def _draw_trajectory(self) -> None:
        """Draw 2D trajectory on canvas with automatic axis selection."""
        self.map_canvas.delete("all")

        if not self.traj_samples:
            self.map_canvas.create_text(
                500, 175, text="No trajectory data",
                font=("Arial", 12), fill="#999"
            )
            return

        width = self.map_canvas.winfo_width()
        height = self.map_canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        # Collect all 3D points for axis selection
        orion_3d = []
        moon_3d = []
        for s in self.traj_samples:
            orion_3d.append((s.orion.x, s.orion.y, s.orion.z))
            moon_3d.append((s.moon.x, s.moon.y, s.moon.z))

        # Pick the two axes with the most spread across ALL bodies
        all_3d = orion_3d + moon_3d + [(0.0, 0.0, 0.0)]
        ax1, ax2 = get_projection_axes(all_3d)
        plane_label = f"{_AXIS_NAMES[ax1]}-{_AXIS_NAMES[ax2]}"

        # Project to 2D
        orion_2d = [(p[ax1], p[ax2]) for p in orion_3d]
        moon_2d = [(p[ax1], p[ax2]) for p in moon_3d]

        # Scale based on Orion trajectory + Earth at origin + Moon positions
        all_2d = orion_2d + moon_2d + [(0.0, 0.0)]
        all_u = [p[0] for p in all_2d]
        all_v = [p[1] for p in all_2d]

        u_min, u_max = min(all_u), max(all_u)
        v_min, v_max = min(all_v), max(all_v)

        u_range = u_max - u_min if u_max != u_min else 1.0
        v_range = v_max - v_min if v_max != v_min else 1.0

        # Uniform scale to preserve aspect ratio
        margin = 60
        usable_w = width - 2 * margin
        usable_h = height - 2 * margin
        scale = min(usable_w / u_range, usable_h / v_range)

        u_mid = (u_min + u_max) / 2
        v_mid = (v_min + v_max) / 2
        cx = width / 2
        cy = height / 2

        def to_px(u: float, v: float) -> tuple[float, float]:
            px = cx + (u - u_mid) * scale
            py = cy - (v - v_mid) * scale  # Y inverted
            return px, py

        # Grid
        grid_color = "#1a3a3a"
        for i in range(0, width, 50):
            self.map_canvas.create_line(i, 0, i, height, fill=grid_color)
        for i in range(0, height, 50):
            self.map_canvas.create_line(0, i, width, i, fill=grid_color)

        # Moon trajectory (dashed gray)
        moon_px = [to_px(u, v) for u, v in moon_2d]
        for i in range(1, len(moon_px)):
            self.map_canvas.create_line(
                moon_px[i-1][0], moon_px[i-1][1],
                moon_px[i][0], moon_px[i][1],
                fill="#555555", width=1, dash=(4, 4)
            )

        # Orion trajectory (cyan)
        orion_px = [to_px(u, v) for u, v in orion_2d]
        for i in range(1, len(orion_px)):
            # Color gradient: cyan → magenta along the path
            t = i / len(orion_px)
            r = int(0 + t * 255)
            g = int(212 - t * 212)
            b = 255
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.map_canvas.create_line(
                orion_px[i-1][0], orion_px[i-1][1],
                orion_px[i][0], orion_px[i][1],
                fill=color, width=2
            )

        # Earth at origin
        ex, ey = to_px(0, 0)
        r = 7
        self.map_canvas.create_oval(ex - r, ey - r, ex + r, ey + r,
                                     fill="#2222ff", outline="#4444ff", width=2)
        self.map_canvas.create_text(ex, ey - 15, text="Earth",
                                     font=("Arial", 9, "bold"), fill="#4488ff")

        # Moon at closest-approach time (where Orion was nearest the Moon)
        min_dist = float('inf')
        flyby_idx = 0
        for i, s in enumerate(self.traj_samples):
            d = math.hypot(s.orion.x - s.moon.x, s.orion.y - s.moon.y, s.orion.z - s.moon.z)
            if d < min_dist:
                min_dist = d
                flyby_idx = i

        # Draw Moon at flyby position
        fm = self.traj_samples[flyby_idx].moon
        fm_3d = (fm.x, fm.y, fm.z)
        fmx, fmy = to_px(fm_3d[ax1], fm_3d[ax2])
        self.map_canvas.create_oval(fmx - r, fmy - r, fmx + r, fmy + r,
                                     fill="#cccc00", outline="#ffff00", width=2)
        self.map_canvas.create_text(fmx, fmy - 15, text="Moon (flyby)",
                                     font=("Arial", 9, "bold"), fill="#ffff00")

        # Moon at last position
        lm = self.traj_samples[-1].moon
        lm_3d = (lm.x, lm.y, lm.z)
        lmx, lmy = to_px(lm_3d[ax1], lm_3d[ax2])
        self.map_canvas.create_oval(lmx - 5, lmy - 5, lmx + 5, lmy + 5,
                                     fill="#666600", outline="#aaaa00", width=1)
        self.map_canvas.create_text(lmx, lmy - 12, text="Moon (now)",
                                     font=("Arial", 8), fill="#aaaa00")

        # Start marker
        if orion_px:
            sx, sy = orion_px[0]
            self.map_canvas.create_oval(sx - 5, sy - 5, sx + 5, sy + 5,
                                         fill="#00ff00", outline="#00ff00", width=2)
            self.map_canvas.create_text(sx, sy - 15, text="First Signal",
                                         font=("Arial", 8, "bold"), fill="#00ff00")

        # Current/End marker
        if orion_px:
            ex2, ey2 = orion_px[-1]
            self.map_canvas.create_oval(ex2 - 5, ey2 - 5, ex2 + 5, ey2 + 5,
                                         fill="#ff00ff", outline="#ff00ff", width=2)
            self.map_canvas.create_text(ex2, ey2 + 15, text="Last Signal",
                                         font=("Arial", 8, "bold"), fill="#ff00ff")

        # Flyby marker on Orion path
        if orion_px:
            fbx, fby = orion_px[flyby_idx]
            self.map_canvas.create_oval(fbx - 4, fby - 4, fbx + 4, fby + 4,
                                         fill="#ff4444", outline="#ff0000", width=2)
            flyby_time = self.traj_samples[flyby_idx].timestamp.strftime("%m-%d %H:%M")
            self.map_canvas.create_text(fbx, fby + 15,
                                         text=f"Flyby {min_dist:,.0f} km ({flyby_time})",
                                         font=("Arial", 8), fill="#ff4444")

        # Labels
        self.map_canvas.create_text(
            width - 50, height - 15,
            text=f"Plane: {plane_label} | Samples: {len(self.traj_samples)}",
            font=("Arial", 9), fill="#666"
        )
        self.map_canvas.create_text(
            width - 20, cy, text=f"{_AXIS_NAMES[ax1]} \u2192",
            font=("Arial", 9), fill="#666"
        )
        self.map_canvas.create_text(
            cx, 15, text=f"\u2191 {_AXIS_NAMES[ax2]}",
            font=("Arial", 9), fill="#666"
        )

    def show(self) -> None:
        self.root.mainloop()


def open_trajectory_viewer() -> None:
    """Open native trajectory viewer window."""
    if not tk:
        logger.error("Tkinter not available")
        return

    global _viewer_window, _viewer_thread

    if _viewer_window and _viewer_window.root.winfo_exists():
        try:
            _viewer_window.root.lift()
            _viewer_window.root.focus()
            return
        except Exception:
            pass

    def show_window():
        global _viewer_window
        try:
            _viewer_window = TrajectoryViewerWindow()
            _viewer_window.show()
        except Exception as e:
            logger.error("Failed to open trajectory viewer: %s", e, exc_info=True)

    _viewer_thread = threading.Thread(target=show_window, daemon=True)
    _viewer_thread.start()
