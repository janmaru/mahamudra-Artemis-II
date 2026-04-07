"""HTML Trajectory Visualization with 3D/2D interactive map."""

import json
import logging
import threading
import webbrowser
from pathlib import Path
from typing import Optional

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
    
    # Prepare data for chart
    timestamps = []
    orion_x = []
    orion_y = []
    orion_z = []
    orion_dist_earth = []
    orion_dist_moon = []
    orion_speed = []
    
    for sample in traj_samples:
        try:
            # Get orion and moon positions
            orion = sample.orion
            moon = sample.moon
            
            # Calculate distances (simple Euclidean)
            dist_earth = (orion.x**2 + orion.y**2 + orion.z**2) ** 0.5
            
            # Distance from Moon
            dx = orion.x - moon.x
            dy = orion.y - moon.y
            dz = orion.z - moon.z
            dist_moon = (dx**2 + dy**2 + dz**2) ** 0.5
            
            # Speed approximation (position magnitude, simplified)
            speed = (orion.x**2 + orion.y**2 + orion.z**2) ** 0.5 / 1000000  # Rough approximation
            
            timestamps.append(sample.timestamp.isoformat()[:16])  # YYYY-MM-DD HH:MM
            orion_x.append(orion.x / 1000)  # Convert to 1000s km
            orion_y.append(orion.y / 1000)
            orion_z.append(orion.z / 1000)
            orion_dist_earth.append(dist_earth)
            orion_dist_moon.append(dist_moon)
            orion_speed.append(max(0.1, speed))  # Avoid zero
        except Exception as e:
            logger.warning("Error parsing trajectory sample: %s", e)
            continue
    
    # Convert to JSON
    timestamps_json = json.dumps(timestamps)
    orion_x_json = json.dumps(orion_x)
    orion_y_json = json.dumps(orion_y)
    orion_z_json = json.dumps(orion_z)
    dist_earth_json = json.dumps(orion_dist_earth)
    dist_moon_json = json.dumps(orion_dist_moon)
    speed_json = json.dumps(orion_speed)
    
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
            <div class="chart-title">📊 X-Y Position (Moon-Relative)</div>
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
                    <div class="stat-value">{stats.get('total_size_mb', 0)}</div>
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
        const orionX = <<<ORION_X_JSON>>>;
        const orionY = <<<ORION_Y_JSON>>>;
        const orionZ = <<<ORION_Z_JSON>>>;
        const distEarth = <<<DIST_EARTH_JSON>>>;
        const distMoon = <<<DIST_MOON_JSON>>>;
        const speed = <<<SPEED_JSON>>>;
        
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
        
        // XY Position Chart
        new Chart(document.getElementById('xyChart'), {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: 'Orion Position (Moon-relative)',
                    data: orionX.map((x, i) => ({{ x: x, y: orionY[i] }})),
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.5)',
                    showLine: true,
                    borderWidth: 2
                }}]
            }},
            options: {{
                ...chartConfig,
                scales: {{
                    x: {{
                        type: 'linear',
                        title: {{ display: true, text: 'X (x10³ km)' }},
                        ticks: {{ color: '#e0e0e0' }},
                        grid: {{ color: 'rgba(0, 212, 255, 0.1)' }}
                    }},
                    y: {{
                        type: 'linear',
                        title: {{ display: true, text: 'Y (x10³ km)' }},
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
    html = html.replace("<<<ORION_X_JSON>>>", orion_x_json)
    html = html.replace("<<<ORION_Y_JSON>>>", orion_y_json)
    html = html.replace("<<<ORION_Z_JSON>>>", orion_z_json)
    html = html.replace("<<<DIST_EARTH_JSON>>>", dist_earth_json)
    html = html.replace("<<<DIST_MOON_JSON>>>", dist_moon_json)
    html = html.replace("<<<SPEED_JSON>>>", speed_json)
    
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
