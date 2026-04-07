"""HTML-based image viewer for mission photos."""

import json
import logging
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

from artemis.models import MissionPhoto
from artemis.photo_carousel import get_carousel_photos

logger = logging.getLogger(__name__)


def generate_carousel_html(current_photo: Optional[MissionPhoto] = None) -> str:
    """Generate HTML for photo carousel viewer.
    
    Args:
        current_photo: Optional MissionPhoto to highlight
        
    Returns:
        HTML string
    """
    photos = get_carousel_photos()
    
    # Convert photos to JSON-safe format
    photo_list = []
    current_index = 0
    
    for i, (photo_file, meta) in enumerate(photos):
        size_kb = photo_file.stat().st_size / 1024
        photo_list.append({
            "index": i,
            "title": meta.get("title", "Unknown"),
            "url": meta.get("url", ""),
            "published": meta.get("published", ""),
            "added_at": meta.get("added_at", ""),
            "size_kb": round(size_kb, 1),
            "filename": photo_file.name,
        })
        
        # Find current photo index
        if current_photo and meta.get("title") == current_photo.title:
            current_index = i
    
    photos_json = json.dumps(photo_list)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artemis II - Mission Photos</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        header {{
            background: rgba(0, 0, 0, 0.5);
            border-bottom: 2px solid #00d4ff;
            padding: 20px;
            text-align: center;
        }}
        
        header h1 {{
            color: #00d4ff;
            margin-bottom: 5px;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }}
        
        header p {{
            color: #aaa;
            font-size: 14px;
        }}
        
        .container {{
            flex: 1;
            display: flex;
            padding: 20px;
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
        }}
        
        .viewer {{
            flex: 3;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #00d4ff;
            border-radius: 8px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 500px;
            position: relative;
            overflow: hidden;
        }}
        
        .viewer img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            border-radius: 4px;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        }}
        
        .controls {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
            justify-content: center;
        }}
        
        button {{
            background: #00d4ff;
            color: #000;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        
        button:hover {{
            background: #00ffff;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.7);
            transform: scale(1.05);
        }}
        
        button:disabled {{
            background: #666;
            cursor: not-allowed;
            opacity: 0.5;
        }}
        
        .info {{
            flex: 1;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #00d4ff;
            border-radius: 8px;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
            min-width: 300px;
        }}
        
        .photo-meta {{
            background: rgba(0, 212, 255, 0.1);
            padding: 15px;
            border-radius: 4px;
            border-left: 3px solid #00d4ff;
        }}
        
        .photo-meta h3 {{
            color: #00d4ff;
            margin-bottom: 10px;
            font-size: 16px;
        }}
        
        .meta-item {{
            margin: 8px 0;
            font-size: 13px;
        }}
        
        .meta-label {{
            color: #00d4ff;
            font-weight: bold;
        }}
        
        .meta-value {{
            color: #bbb;
            word-break: break-all;
        }}
        
        .carousel-list {{
            background: rgba(0, 212, 255, 0.05);
            border-radius: 4px;
            padding: 10px;
            max-height: 300px;
            overflow-y: auto;
        }}
        
        .carousel-list h4 {{
            color: #00d4ff;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        
        .photo-item {{
            padding: 8px;
            margin: 5px 0;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 3px;
            cursor: pointer;
            border-left: 2px solid transparent;
            transition: all 0.2s ease;
            font-size: 12px;
        }}
        
        .photo-item:hover {{
            background: rgba(0, 212, 255, 0.2);
            border-left-color: #00d4ff;
        }}
        
        .photo-item.active {{
            background: rgba(0, 212, 255, 0.3);
            border-left-color: #00ff00;
            color: #00ff00;
        }}
        
        .photo-item-title {{
            font-weight: bold;
            color: #fff;
        }}
        
        .photo-item-size {{
            color: #999;
            font-size: 11px;
        }}
        
        footer {{
            background: rgba(0, 0, 0, 0.5);
            border-top: 2px solid #00d4ff;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #888;
        }}
        
        .keyboard-hint {{
            color: #666;
            font-size: 11px;
            margin-top: 10px;
        }}
        
        @media (max-width: 1024px) {{
            .container {{
                flex-direction: column;
            }}
            
            .info {{
                min-width: 100%;
            }}
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.2);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #00d4ff;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #00ffff;
        }}
    </style>
</head>
<body>
    <header>
        <h1>🛰️ ARTEMIS II - MISSION PHOTOS</h1>
        <p>Interactive Photo Viewer & Carousel</p>
    </header>
    
    <div class="container">
        <div class="viewer">
            <img id="photoImage" src="" alt="Mission Photo" style="display:none;">
            <div id="loadingMessage" style="color: #00d4ff; font-size: 18px;">
                Loading carousel...
            </div>
            <div class="controls">
                <button id="prevBtn" onclick="prevPhoto()" title="Previous photo">← Previous</button>
                <button id="nextBtn" onclick="nextPhoto()" title="Next photo">Next →</button>
            </div>
            <div class="keyboard-hint">
                ← → Arrow keys | Click photos to view
            </div>
        </div>
        
        <div class="info">
            <div class="photo-meta">
                <h3 id="photoTitle">Select a photo</h3>
                <div id="photoMeta">
                    <div class="meta-item">
                        <span class="meta-label">Published:</span>
                        <span class="meta-value" id="metaPublished">—</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Added:</span>
                        <span class="meta-value" id="metaAdded">—</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Size:</span>
                        <span class="meta-value" id="metaSize">—</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">URL:</span>
                        <span class="meta-value" id="metaUrl" style="word-break: break-word;">—</span>
                    </div>
                </div>
            </div>
            
            <div class="carousel-list">
                <h4>📸 Carousel (<<<TOTAL_PHOTOS>>> photos)</h4>
                <div id="photosList"></div>
            </div>
        </div>
    </div>
    
    <footer>
        <p>Use arrow keys or buttons to navigate • Click photos to select • Press F11 for fullscreen</p>
    </footer>
    
    <script>
        const photos = <<<PHOTOS_JSON>>>;
        let currentIndex = <<<CURRENT_INDEX>>>;
        
        function showPhoto(index) {{
            if (index < 0 || index >= photos.length) return;
            
            currentIndex = index;
            const photo = photos[index];
            
            // Update image
            const img = document.getElementById('photoImage');
            img.src = `file:///${{photo.filename.replace(/\\\\/g, '/')}}`;
            img.style.display = 'block';
            
            // Update metadata
            document.getElementById('photoTitle').textContent = photo.title;
            document.getElementById('metaPublished').textContent = photo.published || '—';
            document.getElementById('metaAdded').textContent = photo.added_at.substring(0, 19) || '—';
            document.getElementById('metaSize').textContent = photo.size_kb + ' KB';
            document.getElementById('metaUrl').textContent = photo.url || '—';
            
            // Update carousel list
            const items = document.querySelectorAll('.photo-item');
            items.forEach((item, i) => {{
                item.classList.toggle('active', i === index);
            }});
            
            // Update button states
            document.getElementById('prevBtn').disabled = index === 0;
            document.getElementById('nextBtn').disabled = index === photos.length - 1;
            
            // Hide loading message
            document.getElementById('loadingMessage').style.display = 'none';
        }}
        
        function nextPhoto() {{
            if (currentIndex < photos.length - 1) {{
                showPhoto(currentIndex + 1);
            }}
        }}
        
        function prevPhoto() {{
            if (currentIndex > 0) {{
                showPhoto(currentIndex - 1);
            }}
        }}
        
        function initCarousel() {{
            const list = document.getElementById('photosList');
            
            photos.forEach((photo, index) => {{
                const item = document.createElement('div');
                item.className = 'photo-item';
                item.onclick = () => showPhoto(index);
                item.innerHTML = `
                    <div class="photo-item-title">#${{index + 1}} ${{photo.title}}</div>
                    <div class="photo-item-size">${{photo.size_kb}} KB • ${{photo.added_at.substring(0, 10)}}</div>
                `;
                list.appendChild(item);
            }});
            
            showPhoto(currentIndex);
        }}
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight') nextPhoto();
            if (e.key === 'ArrowLeft') prevPhoto();
        }});
        
        // Initialize on load
        window.addEventListener('load', initCarousel);
    </script>
</body>
</html>"""
    
    # Replace placeholders carefully to avoid f-string conflicts
    html = html.replace("<<<PHOTOS_JSON>>>", photos_json)
    html = html.replace("<<<CURRENT_INDEX>>>", str(current_index))
    html = html.replace("<<<TOTAL_PHOTOS>>>", str(len(photos)))
    return html


def open_carousel_viewer(current_photo: Optional[MissionPhoto] = None) -> None:
    """Generate and open HTML carousel viewer in default browser.
    
    Args:
        current_photo: Optional MissionPhoto to highlight
    """
    try:
        html_content = generate_carousel_html(current_photo)
        
        # Save to temp file
        temp_dir = Path(tempfile.gettempdir())
        html_file = temp_dir / "artemis_photo_viewer.html"
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Open in browser
        webbrowser.open(f"file:///{html_file}")
        logger.info("Opened photo viewer: %s", html_file)
        
    except Exception as exc:
        logger.error("Failed to open carousel viewer: %s", exc)
        raise
