# GitHub Actions Setup Complete ✅

## What Was Created

### 1. GitHub Action Workflow
**File:** `.github/workflows/update-web-data.yml`

Automatically fetches fresh NASA API data every **10 minutes** and updates the web dashboard:

```yaml
Schedule: */10 * * * * (every 10 minutes)
Triggers: 
  - Push to main branch
  - Manual trigger via "Run workflow"
  - Scheduled every 10 minutes

Steps:
  1. Checkout repository
  2. Set up Python 3.11
  3. Install dependencies
  4. Run update_web_data.py
  5. Commit and push changes
```

### 2. Data Update Script
**File:** `scripts/update_web_data.py`

Fetches data from all NASA APIs and saves as JSON:

```python
Fetches:
  - JPL Horizons → spacecraft.json (position, distance, speed)
  - DSN Now → dsn.json (Deep Space Network comms)
  - NOAA SWPC → weather.json (space weather)
  - NASA DONKI → alerts.json (CMEs, solar flares)
  - NASA IOTD RSS → photos.json (up to 10 mission photos, metadata only)

Output: web/data/*.json with timestamp
```

### 3. Updated Web Architecture

**Old approach:** Browser → NASA APIs (CORS blocked ❌)

**New approach:** 
```
NASA APIs
   ↓
GitHub Action (every 10 min)
   ↓
web/data/*.json (cached)
   ↓
GitHub Pages
   ↓
Browser → load from web/data/*.json ✅
```

### 4. Updated API Client
**File:** `web/api-client.js`

Now reads cached JSON files instead of live APIs:

```javascript
// Old
async fetchSpacecraft() → fetch('https://ssd.jpl.nasa.gov/...')

// New
async fetchSpacecraft() → fetch('./data/spacecraft.json')
```

Maps data fields correctly:
- `distance_earth_km` → `earthDistance`
- `distance_moon_km` → `moonDistance`
- `speed_km_s` → `speed`
- etc.

### 5. Data Directory
**Directory:** `web/data/`

Created to store cached JSON files:
```
web/data/
├── spacecraft.json  (Orion position, velocity, distances)
├── dsn.json        (Deep Space Network status)
├── weather.json    (Space weather, Kp index, solar wind)
├── alerts.json     (CMEs, solar flares)
├── photos.json     (Array of up to 10 NASA IOTD photos)
└── .gitkeep        (Git folder tracking)
```

## How to Deploy

### Step 1: Push to GitHub
```bash
git add .github/ scripts/ web/
git commit -m "feat: add GitHub Actions for web dashboard data"
git push origin main
```

### Step 2: Enable GitHub Pages
1. Go to repository Settings
2. Navigate to Pages (left sidebar)
3. Select:
   - **Source:** Deploy from a branch
   - **Branch:** main
   - **Folder:** / (root)
4. Save

### Step 3: GitHub Actions Will Run
- Automatically on every push
- Every 10 minutes on schedule
- You can trigger manually from Actions tab

### Step 4: Access Dashboard
Once GitHub Pages is enabled:

```
https://yourusername.github.io/mahamudra-Artemis-II/web/
```

or if repository is at root:

```
https://yourusername.github.io/mahamudra-Artemis-II/
```

## Local Testing

```bash
# Fetch data locally
python scripts/update_web_data.py

# Start web server
cd web
python -m http.server 8000

# Open browser
# http://localhost:8000
```

## Data Update Flow

1. **GitHub Action triggers** (on push or every 10 min)
2. **Checks out repository**
3. **Runs `scripts/update_web_data.py`**
4. **Fetches from NASA APIs:**
   - JPL Horizons (Orion position)
   - DSN Now (Deep Space Network)
   - NOAA SWPC (Space weather)
   - NASA DONKI (Solar events)
   - NASA Images (Mission photos)
5. **Fetches photos** from NASA IOTD RSS (up to 10, metadata only)
6. **Saves to `web/data/*.json`** with timestamp
7. **Commits and pushes** if data changed
8. **GitHub Pages serves** static files
9. **Browser loads** dashboard with fresh data, rotates photos every 6s

## Current Data Files Generated

✅ `spacecraft.json` (3.9 KB)
- Orion position: x, y, z (in km)
- Moon position: x, y, z
- Distance to Earth: 381,248 km
- Distance to Moon: 68,222 km
- Speed: 0.59 km/s
- Timestamp: 2026-04-07T18:04:00Z

✅ `dsn.json` (980 B)
- 2 DSN dishes (Canberra DSS43, DSS34)
- Downlink rate: 2.0 Mbps
- RTLT (signal delay): 2.5s
- Timestamp: 2026-04-07T18:04:05Z

✅ `weather.json` (399 B)
- Kp Index: 2.33 (Quiet)
- NOAA Scales: G0 S0 R0
- Solar wind speed: 406.9 km/s
- Density: 3.03 p/cm³
- Temperature: 86,146 K
- Timestamp: 2026-04-07T18:04:06Z

✅ `alerts.json` (1.5 KB)
- 4 recent solar events
- CMEs and solar flares
- Sorted by most recent
- Timestamp: 2026-04-07T18:04:07Z

✅ `photos.json` (~1 KB)
- Array of up to 10 photos from NASA Image of the Day RSS feed
- Each entry: title, image_url, url, published
- Browser loads images directly from NASA URLs (no binary download)
- Dashboard rotates photos every 6 seconds

## Next Steps

1. ✅ Push to GitHub and enable GitHub Pages
2. 📊 Monitor GitHub Actions runs
3. 🎨 Add 3D trajectory visualization
4. 🗺️ Create lunar map overlay
5. 📈 Add historical data charts
6. 🔔 Implement real-time alerts
