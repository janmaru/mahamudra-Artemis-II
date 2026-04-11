"""HTML Trajectory Visualization with 3D/2D interactive map."""

import json
import logging
import math
import threading
import webbrowser
from pathlib import Path
from typing import Optional

from artemis.compute import get_projection_axes
from artemis.trajectory_storage import load_trajectory_data, get_trajectory_stats

logger = logging.getLogger(__name__)


def generate_trajectory_html() -> str:
    """Generate interactive HTML trajectory visualization.
    
    Returns:
        HTML string with embedded Chart.js for visualization
    """
    # Load trajectory data
    try:
        traj_data_obj = load_trajectory_data()
        stats = get_trajectory_stats()
        traj_samples = traj_data_obj.samples if traj_data_obj else []
    except Exception as e:
        logger.error("Failed to load trajectory data: %s", e)
        traj_samples = []
        stats = {"total_points": 0}
    
    # Determine best projection axes from all 3D data
    axis_names = ["X", "Y", "Z"]
    all_3d = [(s.orion.x, s.orion.y, s.orion.z) for s in traj_samples]
    all_3d += [(s.moon.x, s.moon.y, s.moon.z) for s in traj_samples]
    all_3d += [(0.0, 0.0, 0.0)]
    ax1, ax2 = get_projection_axes(all_3d) if traj_samples else (0, 1)
    plane_label = f"{axis_names[ax1]}-{axis_names[ax2]}"

    # Prepare data for charts
    timestamps = []
    orion_u = []  # projected axis 1
    orion_v = []  # projected axis 2
    moon_u = []
    moon_v = []
    orion_dist_earth = []
    orion_dist_moon = []
    orion_speed = []

    # Find flyby index (closest approach to Moon)
    min_moon_dist = float('inf')
    flyby_idx = 0
    for i, s in enumerate(traj_samples):
        d = math.hypot(s.orion.x - s.moon.x, s.orion.y - s.moon.y, s.orion.z - s.moon.z)
        if d < min_moon_dist:
            min_moon_dist = d
            flyby_idx = i

    prev_orion = None
    prev_ts = None
    for sample in traj_samples:
        try:
            orion = sample.orion
            moon = sample.moon

            dist_earth = math.hypot(orion.x, orion.y, orion.z)
            dist_moon = math.hypot(orion.x - moon.x, orion.y - moon.y, orion.z - moon.z)

            speed = 0.0
            if prev_orion is not None and prev_ts is not None:
                dt_sec = (sample.timestamp - prev_ts).total_seconds()
                if dt_sec > 0:
                    speed = math.hypot(
                        orion.x - prev_orion.x,
                        orion.y - prev_orion.y,
                        orion.z - prev_orion.z,
                    ) / dt_sec

            orion_3d = (orion.x, orion.y, orion.z)
            moon_3d = (moon.x, moon.y, moon.z)

            timestamps.append(sample.timestamp.isoformat()[:16])
            orion_u.append(orion_3d[ax1] / 1000)
            orion_v.append(orion_3d[ax2] / 1000)
            moon_u.append(moon_3d[ax1] / 1000)
            moon_v.append(moon_3d[ax2] / 1000)
            orion_dist_earth.append(dist_earth)
            orion_dist_moon.append(dist_moon)
            orion_speed.append(max(0.1, speed))
            prev_orion = orion
            prev_ts = sample.timestamp
        except Exception as e:
            logger.warning("Error parsing trajectory sample: %s", e)
            continue

    # Flyby Moon position for marker
    flyby_moon_u = 0.0
    flyby_moon_v = 0.0
    if traj_samples:
        fm = traj_samples[flyby_idx].moon
        flyby_moon_u = (fm.x, fm.y, fm.z)[ax1] / 1000
        flyby_moon_v = (fm.x, fm.y, fm.z)[ax2] / 1000

    # Convert to JSON
    timestamps_json = json.dumps(timestamps)
    orion_u_json = json.dumps(orion_u)
    orion_v_json = json.dumps(orion_v)
    dist_earth_json = json.dumps(orion_dist_earth)
    dist_moon_json = json.dumps(orion_dist_moon)
    speed_json = json.dumps(orion_speed)
    moon_u_json = json.dumps(moon_u)
    moon_v_json = json.dumps(moon_v)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artemis II - Trajectory Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@2.0.0/dist/chartjs-adapter-date-fns.min.js"></script>
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
            background: rgba(0, 0, 0, 0.7);
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
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 20px;
            max-width: 1600px;
            margin: 0 auto;
            width: 100%;
        }}
        
        .chart-container {{
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #00d4ff;
            border-radius: 8px;
            padding: 15px;
            position: relative;
            height: 400px;
        }}
        
        .chart-title {{
            color: #00d4ff;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        
        canvas {{
            max-height: 350px !important;
        }}
        
        .stats {{
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #00d4ff;
            border-radius: 8px;
            padding: 20px;
            grid-column: 1 / -1;
        }}
        
        .stats h2 {{
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 16px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .stat-item {{
            background: rgba(0, 212, 255, 0.1);
            padding: 15px;
            border-radius: 4px;
            border-left: 3px solid #00d4ff;
        }}
        
        .stat-label {{
            color: #00d4ff;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
        }}
        
        .stat-value {{
            color: #00ff00;
            font-size: 20px;
            font-weight: bold;
            margin-top: 5px;
        }}
        
        .stat-unit {{
            color: #999;
            font-size: 12px;
            margin-top: 2px;
        }}
        
        footer {{
            background: rgba(0, 0, 0, 0.7);
            border-top: 2px solid #00d4ff;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #888;
        }}
        
        .info-box {{
            background: rgba(0, 212, 255, 0.1);
            border-left: 3px solid #00d4ff;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        
        @media (max-width: 1200px) {{
            .container {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>🚀 ARTEMIS II - TRAJECTORY ANALYSIS</h1>
        <p>Interactive mission trajectory visualization from stored history</p>
    </header>
    
    <div class="container">
        <div class="chart-container">
            <div class="chart-title">📍 Distance from Earth (Historical)</div>
            <canvas id="distanceEarthChart"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">🌙 Distance from Moon (Historical)</div>
            <canvas id="distanceMoonChart"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">⚡ Spacecraft Speed (Historical)</div>
            <canvas id="speedChart"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">📊 Position {plane_label} plane (Earth-Relative)</div>
            <canvas id="xyChart"></canvas>
        </div>
        
        <div class="stats">
            <h2>📈 TRAJECTORY STATISTICS</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Total Points Recorded</div>
                    <div class="stat-value">{stats.get('total_points', 0)}</div>
                    <div class="stat-unit">trajectory samples</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Mission Duration</div>
                    <div class="stat-value" id="missionDays">—</div>
                    <div class="stat-unit">days tracked</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Latest Earth Distance</div>
                    <div class="stat-value" id="latestEarthDist">—</div>
                    <div class="stat-unit">kilometers</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Latest Moon Distance</div>
                    <div class="stat-value" id="latestMoonDist">—</div>
                    <div class="stat-unit">kilometers</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Latest Speed</div>
                    <div class="stat-value" id="latestSpeed">—</div>
                    <div class="stat-unit">km/s</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Storage Used</div>
                    <div class="stat-value">{stats.get('file_size_kb', 0) / 1024:.1f}</div>
                    <div class="stat-unit">MB</div>
                </div>
            </div>
            
            <div class="info-box">
                <strong>ℹ️ Data Source:</strong> Incremental trajectory storage (cache/trajectory_data/)
                <br/>
                <strong>Update Frequency:</strong> Every 10-20 minutes via JPL Horizons
                <br/>
                <strong>Total History:</strong> Last {stats.get('total_points', 0)} trajectory samples
            </div>
        </div>
    </div>
    
    <footer>
        <p>Artemis II Mission Trajectory Analysis • Real-time data from JPL Horizons API</p>
    </footer>
    
    <script>
        // Data from Python
        const timestamps = <<<TIMESTAMPS_JSON>>>;
        const orionU = <<<ORION_U_JSON>>>;
        const orionV = <<<ORION_V_JSON>>>;
        const distEarth = <<<DIST_EARTH_JSON>>>;
        const distMoon = <<<DIST_MOON_JSON>>>;
        const speed = <<<SPEED_JSON>>>;
        const moonU = <<<MOON_U_JSON>>>;
        const moonV = <<<MOON_V_JSON>>>;
        const flybyMoonU = {flyby_moon_u};
        const flybyMoonV = {flyby_moon_v};

        // Chart config
        const chartConfig = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    display: true,
                    labels: {{ color: '#e0e0e0' }}
                }}
            }},
            scales: {{
                x: {{
                    ticks: {{ color: '#e0e0e0' }},
                    grid: {{ color: 'rgba(0, 212, 255, 0.1)' }}
                }},
                y: {{
                    ticks: {{ color: '#e0e0e0' }},
                    grid: {{ color: 'rgba(0, 212, 255, 0.1)' }}
                }}
            }}
        }};
        
        // Distance from Earth Chart
        new Chart(document.getElementById('distanceEarthChart'), {{
            type: 'line',
            data: {{
                labels: timestamps,
                datasets: [{{
                    label: 'Distance (km)',
                    data: distEarth,
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    tension: 0.1,
                    fill: true
                }}]
            }},
            options: chartConfig
        }});
        
        // Distance from Moon Chart
        new Chart(document.getElementById('distanceMoonChart'), {{
            type: 'line',
            data: {{
                labels: timestamps,
                datasets: [{{
                    label: 'Distance (km)',
                    data: distMoon,
                    borderColor: '#ffaa00',
                    backgroundColor: 'rgba(255, 170, 0, 0.1)',
                    tension: 0.1,
                    fill: true
                }}]
            }},
            options: chartConfig
        }});
        
        // Speed Chart
        new Chart(document.getElementById('speedChart'), {{
            type: 'line',
            data: {{
                labels: timestamps,
                datasets: [{{
                    label: 'Speed (km/s)',
                    data: speed,
                    borderColor: '#00ff00',
                    backgroundColor: 'rgba(0, 255, 0, 0.1)',
                    tension: 0.1,
                    fill: true
                }}]
            }},
            options: chartConfig
        }});
        
        // Position Chart (best projection plane, Earth-relative)
        new Chart(document.getElementById('xyChart'), {{
            type: 'scatter',
            data: {{
                datasets: [
                    {{
                        label: 'Orion',
                        data: orionU.map((u, i) => ({{ x: u, y: orionV[i] }})),
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0, 212, 255, 0.5)',
                        showLine: true,
                        borderWidth: 2,
                        pointRadius: 0
                    }},
                    {{
                        label: 'Moon',
                        data: moonU.map((u, i) => ({{ x: u, y: moonV[i] }})),
                        borderColor: '#ffaa00',
                        backgroundColor: 'rgba(255, 170, 0, 0.3)',
                        showLine: true,
                        borderWidth: 1,
                        pointRadius: 0,
                        borderDash: [5, 5]
                    }},
                    {{
                        label: 'Earth',
                        data: [{{ x: 0, y: 0 }}],
                        borderColor: '#4488ff',
                        backgroundColor: '#2244cc',
                        pointRadius: 7,
                        showLine: false
                    }},
                    {{
                        label: 'Moon (flyby)',
                        data: [{{ x: flybyMoonU, y: flybyMoonV }}],
                        borderColor: '#ffff00',
                        backgroundColor: '#cccc00',
                        pointRadius: 7,
                        showLine: false
                    }}
                ]
            }},
            options: {{
                ...chartConfig,
                maintainAspectRatio: true,
                aspectRatio: 1,
                scales: {{
                    x: {{
                        type: 'linear',
                        title: {{ display: true, text: '{axis_names[ax1]} (x10³ km)', color: '#e0e0e0' }},
                        ticks: {{ color: '#e0e0e0' }},
                        grid: {{ color: 'rgba(0, 212, 255, 0.1)' }}
                    }},
                    y: {{
                        type: 'linear',
                        title: {{ display: true, text: '{axis_names[ax2]} (x10³ km)', color: '#e0e0e0' }},
                        ticks: {{ color: '#e0e0e0' }},
                        grid: {{ color: 'rgba(0, 212, 255, 0.1)' }}
                    }}
                }}
            }}
        }});
        
        // Update stats
        if (distEarth.length > 0) {{
            document.getElementById('latestEarthDist').textContent = 
                distEarth[distEarth.length - 1].toLocaleString('en-US', {{maximumFractionDigits: 0}});
        }}
        if (distMoon.length > 0) {{
            document.getElementById('latestMoonDist').textContent = 
                distMoon[distMoon.length - 1].toLocaleString('en-US', {{maximumFractionDigits: 0}});
        }}
        if (speed.length > 0) {{
            document.getElementById('latestSpeed').textContent = 
                speed[speed.length - 1].toFixed(3);
        }}
        if (timestamps.length > 0) {{
            const firstDate = new Date(timestamps[0]);
            const lastDate = new Date(timestamps[timestamps.length - 1]);
            const days = Math.floor((lastDate - firstDate) / (1000 * 60 * 60 * 24));
            document.getElementById('missionDays').textContent = days + ' days';
        }}
    </script>
</body>
</html>"""
    
    # Replace placeholders
    html = html.replace("<<<TIMESTAMPS_JSON>>>", timestamps_json)
    html = html.replace("<<<ORION_U_JSON>>>", orion_u_json)
    html = html.replace("<<<ORION_V_JSON>>>", orion_v_json)
    html = html.replace("<<<DIST_EARTH_JSON>>>", dist_earth_json)
    html = html.replace("<<<DIST_MOON_JSON>>>", dist_moon_json)
    html = html.replace("<<<SPEED_JSON>>>", speed_json)
    html = html.replace("<<<MOON_U_JSON>>>", moon_u_json)
    html = html.replace("<<<MOON_V_JSON>>>", moon_v_json)

    return html


def open_trajectory_viewer() -> None:
    """Open trajectory visualization in browser."""
    try:
        html_content = generate_trajectory_html()
        
        # Save to temp file
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        html_file = temp_dir / "artemis_trajectory_viewer.html"
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Open in browser
        webbrowser.open(f"file:///{html_file}")
        logger.info("Opened trajectory viewer: %s", html_file)
        
    except Exception as exc:
        logger.error("Failed to open trajectory viewer: %s", exc)
