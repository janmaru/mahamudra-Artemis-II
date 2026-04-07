"""Native trajectory viewer window - 2D map + history list."""

import logging
import threading
from typing import Optional

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    tk = None

from artemis.trajectory_storage import load_trajectory_data, get_trajectory_stats

logger = logging.getLogger(__name__)

_viewer_window = None
_viewer_thread = None


class TrajectoryViewerWindow:
    """Native Tkinter window showing 2D trajectory map and history."""
    
    def __init__(self):
        """Initialize viewer window."""
        self.root = tk.Tk()
        self.root.title("Artemis II - Trajectory Viewer")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a2e")
        
        # Load data
        try:
            traj_data_obj = load_trajectory_data()
            self.stats = get_trajectory_stats()
            self.traj_samples = traj_data_obj.samples if traj_data_obj else []
        except Exception as e:
            logger.error("Failed to load trajectory data: %s", e)
            self.traj_samples = []
            self.stats = {}
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Build the UI layout."""
        # Header
        header = tk.Frame(self.root, bg="#000000", height=40)
        header.pack(side=tk.TOP, fill=tk.X)
        
        title = tk.Label(
            header,
            text="🚀 ARTEMIS II - TRAJECTORY HISTORY",
            font=("Arial", 14, "bold"),
            bg="#000000",
            fg="#00d4ff"
        )
        title.pack(pady=8)
        
        # Main container - split: map on top, history below
        paned = tk.PanedWindow(self.root, orient=tk.VERTICAL, bg="#1a1a2e", sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top: 2D trajectory map
        map_frame = tk.Frame(paned, bg="#1a1a2e", height=400)
        paned.add(map_frame, height=400)
        
        self.map_canvas = tk.Canvas(
            map_frame,
            bg="#000000",
            highlightthickness=1,
            highlightbackground="#00d4ff",
            width=1000,
            height=350
        )
        self.map_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Draw trajectory on map
        self._draw_trajectory()
        
        # Bottom: History list
        list_frame = tk.Frame(paned, bg="#1a1a2e")
        paned.add(list_frame)
        
        list_label = tk.Label(
            list_frame,
            text="📍 TRAJECTORY HISTORY",
            font=("Arial", 10, "bold"),
            bg="#1a1a2e",
            fg="#00d4ff"
        )
        list_label.pack(anchor="w", padx=10, pady=(5, 2))
        
        # Scrollable list
        list_canvas = tk.Canvas(list_frame, bg="#1a1a2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=list_canvas.yview)
        scrollable_frame = tk.Frame(list_canvas, bg="#1a1a2e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all"))
        )
        
        list_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        list_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add history items (reverse order - newest first)
        for sample in reversed(self.traj_samples):
            try:
                orion = sample.orion
                moon = sample.moon
                
                dist_earth = (orion.x**2 + orion.y**2 + orion.z**2) ** 0.5
                dx = orion.x - moon.x
                dy = orion.y - moon.y
                dz = orion.z - moon.z
                dist_moon = (dx**2 + dy**2 + dz**2) ** 0.5
                
                item = tk.Frame(scrollable_frame, bg="#000000", height=30)
                item.pack(fill=tk.X, padx=2, pady=1)
                
                time_text = sample.timestamp.strftime("%Y-%m-%d %H:%M")
                info_text = f"{time_text}  |  🌍 {dist_earth:>10,.0f} km  |  🌙 {dist_moon:>10,.0f} km"
                
                lbl = tk.Label(
                    item,
                    text=info_text,
                    font=("Courier", 9),
                    bg="#000000",
                    fg="#e0e0e0",
                    anchor="w",
                    justify=tk.LEFT
                )
                lbl.pack(fill=tk.X, padx=8, pady=5)
            except Exception:
                continue
        
        list_canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Footer
        footer = tk.Frame(self.root, bg="#1a1a2e", height=30)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        
        info = tk.Label(
            footer,
            text=f"Total samples: {len(self.traj_samples)} | ESC to close",
            font=("Arial", 9),
            bg="#1a1a2e",
            fg="#e0e0e0"
        )
        info.pack(pady=5)
        
        # Bind keyboard
        self.root.bind("<Escape>", lambda e: self.root.quit())
    
    def _draw_trajectory(self) -> None:
        """Draw 2D trajectory map on canvas."""
        if not self.traj_samples:
            text = tk.Label(
                self.map_canvas,
                text="No trajectory data",
                font=("Arial", 12),
                bg="#000000",
                fg="#999"
            )
            return
        
        # Get canvas dimensions
        width = self.map_canvas.winfo_width()
        height = self.map_canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            width = 1000
            height = 350
        
        center_x = width / 2
        center_y = height / 2
        
        # Calculate data range (X-Y plane, Earth-relative)
        x_coords = []
        y_coords = []
        
        for sample in self.traj_samples:
            try:
                orion = sample.orion
                x_coords.append(orion.x)
                y_coords.append(orion.y)
            except Exception:
                continue
        
        if not x_coords or not y_coords:
            return
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Add padding
        x_range = x_max - x_min if x_max != x_min else 1
        y_range = y_max - y_min if y_max != y_min else 1
        x_min -= x_range * 0.1
        x_max += x_range * 0.1
        y_min -= y_range * 0.1
        y_max += y_range * 0.1
        
        x_range = x_max - x_min
        y_range = y_max - y_min
        
        # Scaling factors
        scale_x = (width - 100) / x_range if x_range > 0 else 1
        scale_y = (height - 100) / y_range if y_range > 0 else 1
        
        # Draw grid
        grid_color = "#1a3a3a"
        for i in range(0, width, 50):
            self.map_canvas.create_line(i, 0, i, height, fill=grid_color, width=1)
        for i in range(0, height, 50):
            self.map_canvas.create_line(0, i, width, i, fill=grid_color, width=1)
        
        # Draw trajectory line
        prev_px, prev_py = None, None
        for sample in self.traj_samples:
            try:
                orion = sample.orion
                px = center_x + (orion.x - (x_min + x_range/2)) * scale_x
                py = center_y + (orion.y - (y_min + y_range/2)) * scale_y
                
                if prev_px is not None:
                    self.map_canvas.create_line(
                        prev_px, prev_py, px, py,
                        fill="#00d4ff", width=1
                    )
                
                prev_px, prev_py = px, py
            except Exception:
                continue
        
        # Draw points (sample every Nth point to avoid cluttering)
        step = max(1, len(self.traj_samples) // 100)
        for i, sample in enumerate(self.traj_samples):
            if i % step != 0:
                continue
            try:
                orion = sample.orion
                px = center_x + (orion.x - (x_min + x_range/2)) * scale_x
                py = center_y + (orion.y - (y_min + y_range/2)) * scale_y
                
                # Draw point
                radius = 3
                self.map_canvas.create_oval(
                    px - radius, py - radius,
                    px + radius, py + radius,
                    fill="#00ff00", outline="#00d4ff", width=1
                )
            except Exception:
                continue
        
        # Draw start (green) and end (red) points
        if self.traj_samples:
            # Start
            try:
                orion = self.traj_samples[0].orion
                px = center_x + (orion.x - (x_min + x_range/2)) * scale_x
                py = center_y + (orion.y - (y_min + y_range/2)) * scale_y
                radius = 5
                self.map_canvas.create_oval(
                    px - radius, py - radius,
                    px + radius, py + radius,
                    fill="#00ff00", outline="#00ff00", width=2
                )
                self.map_canvas.create_text(
                    px, py - 15,
                    text="START",
                    font=("Arial", 8, "bold"),
                    fill="#00ff00"
                )
            except Exception:
                pass
            
            # Current position
            try:
                orion = self.traj_samples[-1].orion
                px = center_x + (orion.x - (x_min + x_range/2)) * scale_x
                py = center_y + (orion.y - (y_min + y_range/2)) * scale_y
                radius = 5
                self.map_canvas.create_oval(
                    px - radius, py - radius,
                    px + radius, py + radius,
                    fill="#ff00ff", outline="#ff00ff", width=2
                )
                self.map_canvas.create_text(
                    px, py + 15,
                    text="CURRENT",
                    font=("Arial", 8, "bold"),
                    fill="#ff00ff"
                )
            except Exception:
                pass
        
        # Draw axes labels
        self.map_canvas.create_text(
            width - 20, center_y,
            text="X →",
            font=("Arial", 9),
            fill="#666"
        )
        self.map_canvas.create_text(
            center_x, 20,
            text="↑ Y",
            font=("Arial", 9),
            fill="#666"
        )
    
    def show(self) -> None:
        """Show the window."""
        self.root.mainloop()


def open_trajectory_viewer() -> None:
    """Open native trajectory viewer window."""
    if not tk:
        logger.error("Tkinter not available")
        return
    
    global _viewer_window, _viewer_thread
    
    # If window already exists and is running, bring to focus
    if _viewer_window and _viewer_window.root.winfo_exists():
        try:
            _viewer_window.root.lift()
            _viewer_window.root.focus()
            return
        except Exception:
            pass
    
    # Create and show new window in separate thread
    def show_window():
        try:
            _viewer_window = TrajectoryViewerWindow()
            _viewer_window.show()
        except Exception as e:
            logger.error("Failed to open trajectory viewer: %s", e, exc_info=True)
    
    _viewer_thread = threading.Thread(target=show_window, daemon=True)
    _viewer_thread.start()
