"""Native photo viewer window using Tkinter."""

import logging
import threading
from pathlib import Path
from typing import Optional

try:
    import tkinter as tk
    from tkinter import ttk
    from PIL import Image, ImageTk
except ImportError:
    tk = None
    ImageTk = None

from artemis.models import MissionPhoto
from artemis.photo_carousel import get_carousel_photos

logger = logging.getLogger(__name__)

_viewer_window = None
_viewer_thread = None


class PhotoViewerWindow:
    """Native Tkinter window for viewing carousel photos."""
    
    def __init__(self, current_photo: Optional[MissionPhoto] = None):
        """Initialize viewer window.
        
        Args:
            current_photo: Current photo to display
        """
        self.root = tk.Tk()
        self.root.title("Artemis II - Mission Photos")
        self.root.geometry("1000x700")
        
        # Style
        self.root.configure(bg="#1a1a2e")
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        self.bg_color = "#1a1a2e"
        self.fg_color = "#e0e0e0"
        self.accent_color = "#00d4ff"
        
        # Load photos from carousel
        self.photos = get_carousel_photos()
        self.current_index = 0
        
        # Find current photo index
        if current_photo and self.photos:
            for i, (_, meta) in enumerate(self.photos):
                if meta.get("title") == current_photo.title:
                    self.current_index = i
                    break
        
        self.current_image_tk = None
        
        self._build_ui()
        self._show_photo(self.current_index)
    
    def _build_ui(self) -> None:
        """Build the UI layout."""
        # Header
        header = tk.Frame(self.root, bg="#000000", height=60)
        header.pack(side=tk.TOP, fill=tk.X)
        
        title = tk.Label(
            header,
            text="🛰️ ARTEMIS II - MISSION PHOTOS",
            font=("Arial", 16, "bold"),
            bg="#000000",
            fg=self.accent_color
        )
        title.pack(pady=10)
        
        # Main container
        container = tk.Frame(self.root, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: Image viewer
        left_frame = tk.Frame(container, bg=self.bg_color)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.image_label = tk.Label(
            left_frame,
            bg="#000000",
            fg=self.accent_color,
            font=("Arial", 12),
            text="Loading carousel...",
            width=50,
            height=20
        )
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Controls
        controls = tk.Frame(left_frame, bg=self.bg_color)
        controls.pack(fill=tk.X, pady=10)
        
        self.prev_btn = tk.Button(
            controls,
            text="← Previous",
            command=self._prev_photo,
            bg=self.accent_color,
            fg="#000000",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=5
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(
            controls,
            text="Next →",
            command=self._next_photo,
            bg=self.accent_color,
            fg="#000000",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=5
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        self.counter_label = tk.Label(
            controls,
            text="0/0",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 10)
        )
        self.counter_label.pack(side=tk.RIGHT, padx=5)
        
        # Right: Info panel
        right_frame = tk.Frame(container, bg=self.bg_color, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # Photo metadata
        info_label = tk.Label(
            right_frame,
            text="📸 PHOTO INFO",
            bg=self.bg_color,
            fg=self.accent_color,
            font=("Arial", 11, "bold")
        )
        info_label.pack(pady=10)
        
        self.title_label = tk.Label(
            right_frame,
            text="—",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 10, "bold"),
            wraplength=280,
            justify=tk.LEFT
        )
        self.title_label.pack(fill=tk.X, padx=5, pady=5)
        
        self.meta_text = tk.Text(
            right_frame,
            bg="#000000",
            fg=self.fg_color,
            font=("Courier", 9),
            height=15,
            width=35,
            state=tk.DISABLED,
            relief=tk.FLAT,
            borderwidth=1
        )
        self.meta_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Carousel list
        carousel_label = tk.Label(
            right_frame,
            text="📷 CAROUSEL",
            bg=self.bg_color,
            fg=self.accent_color,
            font=("Arial", 11, "bold")
        )
        carousel_label.pack(pady=(15, 5))
        
        # Listbox with scrollbar
        list_frame = tk.Frame(right_frame, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.list_box = tk.Listbox(
            list_frame,
            bg="#000000",
            fg=self.fg_color,
            font=("Arial", 9),
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            borderwidth=1,
            height=10
        )
        self.list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.list_box.bind("<<ListboxSelect>>", self._on_list_select)
        scrollbar.config(command=self.list_box.yview)
        
        # Bind keyboard
        self.root.bind("<Left>", lambda e: self._prev_photo())
        self.root.bind("<Right>", lambda e: self._next_photo())
        self.root.bind("<Escape>", lambda e: self.root.quit())
    
    def _show_photo(self, index: int) -> None:
        """Show photo at given index."""
        if index < 0 or index >= len(self.photos):
            return
        
        self.current_index = index
        photo_file, meta = self.photos[index]
        
        try:
            # Load and display image
            img = Image.open(photo_file)
            
            # Resize to fit
            max_width = 600
            max_height = 500
            img.thumbnail((max_width, max_height), Image.LANCZOS)
            
            self.current_image_tk = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.current_image_tk, text="")
            
            # Update metadata
            self.title_label.config(text=meta.get("title", "Unknown"))
            
            meta_text = (
                f"Published:\n{meta.get('published', '—')}\n\n"
                f"Added:\n{meta.get('added_at', '—')}\n\n"
                f"Size:\n{photo_file.stat().st_size / 1024:.1f} KB\n\n"
                f"URL:\n{meta.get('url', '—')}"
            )
            self.meta_text.config(state=tk.NORMAL)
            self.meta_text.delete(1.0, tk.END)
            self.meta_text.insert(tk.END, meta_text)
            self.meta_text.config(state=tk.DISABLED)
            
            # Update counter
            self.counter_label.config(text=f"{index+1}/{len(self.photos)}")
            
            # Update button states
            self.prev_btn.config(state=tk.NORMAL if index > 0 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if index < len(self.photos)-1 else tk.DISABLED)
            
            # Update list selection
            self.list_box.selection_clear(0, tk.END)
            self.list_box.selection_set(index)
            self.list_box.see(index)
            
        except Exception as e:
            logger.error("Failed to show photo %d: %s", index, e)
            self.image_label.config(
                image="",
                text=f"Error loading photo:\n{str(e)[:50]}"
            )
    
    def _prev_photo(self) -> None:
        """Show previous photo."""
        if self.current_index > 0:
            self._show_photo(self.current_index - 1)
    
    def _next_photo(self) -> None:
        """Show next photo."""
        if self.current_index < len(self.photos) - 1:
            self._show_photo(self.current_index + 1)
    
    def _on_list_select(self, event) -> None:
        """Handle list selection."""
        selection = self.list_box.curselection()
        if selection:
            self._show_photo(selection[0])
    
    def _populate_list(self) -> None:
        """Populate carousel list."""
        self.list_box.delete(0, tk.END)
        for i, (_, meta) in enumerate(self.photos):
            title = meta.get("title", "Unknown")[:40]
            self.list_box.insert(tk.END, f"#{i+1} {title}")
    
    def show(self) -> None:
        """Show the window."""
        self._populate_list()
        self.root.mainloop()


def open_photo_viewer(current_photo: Optional[MissionPhoto] = None) -> None:
    """Open native photo viewer window.
    
    Args:
        current_photo: Optional current photo to display
    """
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
            _viewer_window = PhotoViewerWindow(current_photo)
            _viewer_window.show()
        except Exception as e:
            logger.error("Failed to open photo viewer: %s", e, exc_info=True)
    
    _viewer_thread = threading.Thread(target=show_window, daemon=True)
    _viewer_thread.start()
