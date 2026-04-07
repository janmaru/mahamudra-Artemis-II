// Artemis II Dashboard Main Controller

class Dashboard {
    constructor() {
        this.updateInterval = 10000; // 10 seconds between updates
        this.launchDate = new Date('2026-04-02T13:30:00Z');
        this.missionDuration = 10 * 24 * 60 * 60 * 1000; // 10 days
        this.photos = [];
        this.photoIndex = 0;
        this.photoRotationSeconds = 6;
    }

    /**
     * Initialize the dashboard
     */
    async init() {
        console.log('Initializing Artemis II Dashboard...');
        
        // Fetch initial data
        await this.updateAllData();

        // Set up auto-refresh for data
        setInterval(() => this.updateAllData(), this.updateInterval);

        // Set up photo rotation
        setInterval(() => this.rotatePhoto(), this.photoRotationSeconds * 1000);
    }

    /**
     * Update all dashboard data
     */
    async updateAllData() {
        console.log('Updating dashboard data...');

        try {
            // Fetch all data in parallel
            const [spacecraft, dsn, weather, donki, photos] = await Promise.allSettled([
                apiClient.fetchSpacecraft(),
                apiClient.fetchDSN(),
                apiClient.fetchSpaceWeather(),
                apiClient.fetchDONKI(),
                apiClient.fetchMissionPhotos(),
            ]);

            // Update UI with results (handle rejections gracefully)
            this.updateHeader();
            if (spacecraft.status === 'fulfilled' && spacecraft.value) {
                this.updateSpacecraft(spacecraft.value);
                this.updateSolarMap(spacecraft.value);
            }
            if (dsn.status === 'fulfilled' && dsn.value) {
                this.updateDSN(dsn.value);
            }
            if (weather.status === 'fulfilled' && weather.value) {
                this.updateWeather(weather.value);
            }
            if (donki.status === 'fulfilled' && donki.value) {
                this.updateAlerts(donki.value);
            }
            if (photos.status === 'fulfilled' && photos.value) {
                this.photos = photos.value;
                this.showPhoto(this.photoIndex);
            }

            this.updateStatus();
        } catch (error) {
            console.error('Dashboard update error:', error);
            this.updateStatus('error');
        }
    }

    /**
     * Update header with MET (Mission Elapsed Time)
     */
    updateHeader() {
        const now = new Date();
        const elapsed = now - this.launchDate;

        const days = Math.floor(elapsed / (24 * 60 * 60 * 1000));
        const hours = Math.floor((elapsed % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000));
        const minutes = Math.floor((elapsed % (60 * 60 * 1000)) / (60 * 1000));
        const seconds = Math.floor((elapsed % (60 * 1000)) / 1000);

        const metDisplay = `${days}d ${hours}h ${minutes}m ${seconds}s`;
        document.getElementById('met-display').textContent = `MET: ${metDisplay}`;

        const flightDay = Math.floor(days) + 1;
        document.getElementById('flight-day').textContent = `Flight Day ${flightDay}`;

        const phase = this.getMissionPhase(days);
        document.getElementById('phase').textContent = `Phase: ${phase}`;
    }

    /**
     * Determine mission phase based on elapsed time
     */
    getMissionPhase(days) {
        if (days < 0.5) return 'Launch';
        if (days < 1.5) return 'Earth Escape';
        if (days < 3) return 'Trans-Lunar';
        if (days < 5) return 'Lunar Approach';
        if (days < 6.5) return 'Lunar Flyby';
        if (days < 8) return 'Trans-Earth';
        if (days < 10) return 'Re-Entry';
        return 'Recovery';
    }

    /**
     * Update spacecraft panel
     */
    updateSpacecraft(data) {
        if (!data) return;

        document.getElementById('earth-distance').textContent =
            `${data.earthDistance.toLocaleString('en-US', { maximumFractionDigits: 0 })} km`;
        document.getElementById('moon-distance').textContent =
            `${data.moonDistance.toLocaleString('en-US', { maximumFractionDigits: 0 })} km`;
        document.getElementById('speed').textContent =
            `${data.speed.toFixed(3)} km/s (${(data.speed * 3600).toFixed(0)} km/h)`;
        document.getElementById('position').textContent =
            `${data.position.x.toFixed(0)} / ${data.position.y.toFixed(0)} / ${data.position.z.toFixed(0)}`;
    }

    /**
     * Update solar map (canvas visualization)
     */
    updateSolarMap(data) {
        if (!data) return;

        const canvas = document.getElementById('solar-map-canvas');
        const container = canvas.parentElement;
        const rect = container.getBoundingClientRect();

        // Size canvas to fill panel content (minus legend space)
        const w = Math.floor(rect.width);
        const h = Math.floor(rect.height - 30);
        if (w <= 0 || h <= 0) return;

        const dpr = window.devicePixelRatio || 1;
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        canvas.style.width = w + 'px';
        canvas.style.height = h + 'px';

        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);

        // Clear
        ctx.fillStyle = '#0a0e27';
        ctx.fillRect(0, 0, w, h);

        // Positions (Earth-relative, km)
        const orionX = data.position.x * 1000;  // position is in x1000 km
        const orionY = data.position.y * 1000;
        const moonX = data.raw?.moon?.x || 0;
        const moonY = data.raw?.moon?.y || 0;

        // Logarithmic scaling (same as Python: exponent 0.55)
        const EXP = 0.55;
        const points = [[orionX, orionY], [moonX, moonY]];
        let scaleLimit = 0;
        for (const [px, py] of points) {
            scaleLimit = Math.max(scaleLimit, Math.hypot(px, py));
        }
        scaleLimit *= 1.15;
        if (scaleLimit < 1) scaleLimit = 400000;

        const cx = w / 2;
        const cy = h / 2;
        const halfW = w / 2 - 15;
        const halfH = h / 2 - 15;

        function toCanvas(x, y) {
            const dist = Math.hypot(x, y);
            if (dist < 1) return [cx, cy];
            const angle = Math.atan2(y, x);
            const c = Math.pow(Math.min(1.0, dist / scaleLimit), EXP);
            return [
                cx + c * Math.cos(angle) * halfW,
                cy - c * Math.sin(angle) * halfH,
            ];
        }

        // Draw Earth at center (cyan circle)
        ctx.beginPath();
        ctx.arc(cx, cy, 6, 0, Math.PI * 2);
        ctx.fillStyle = '#00ffff';
        ctx.fill();
        ctx.font = '11px Courier New';
        ctx.fillStyle = '#00ffff';
        ctx.fillText('Earth', cx + 10, cy + 4);

        // Draw Moon (yellow circle)
        const [mx, my] = toCanvas(moonX, moonY);
        ctx.beginPath();
        ctx.arc(mx, my, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#ffff00';
        ctx.fill();
        ctx.fillStyle = '#ffff00';
        ctx.fillText('Moon', mx + 9, my + 4);

        // Draw Orion (magenta diamond)
        const [ox, oy] = toCanvas(orionX, orionY);
        const ds = 6;
        ctx.beginPath();
        ctx.moveTo(ox, oy - ds);
        ctx.lineTo(ox + ds, oy);
        ctx.lineTo(ox, oy + ds);
        ctx.lineTo(ox - ds, oy);
        ctx.closePath();
        ctx.fillStyle = '#ff66ff';
        ctx.fill();
        ctx.fillStyle = '#ff66ff';
        ctx.font = 'bold 11px Courier New';
        ctx.fillText('Orion', ox + 10, oy + 4);

        // Update legend
        const earthDist = data.earthDistance.toLocaleString('en-US', { maximumFractionDigits: 0 });
        const moonDist = data.moonDistance.toLocaleString('en-US', { maximumFractionDigits: 0 });
        const speed = data.speed.toFixed(3);
        document.getElementById('solar-map-legend').innerHTML =
            `<span class="earth-legend">● ${earthDist} km</span> ` +
            `<span class="moon-legend">● ${moonDist} km</span> ` +
            `<span class="orion-legend">◆ Orion</span> | ${speed} km/s`;
    }

    /**
     * Update DSN communications panel
     */
    updateDSN(stations) {
        if (!stations || stations.length === 0) {
            document.getElementById('dsn-tbody').innerHTML = '<tr><td colspan="5">No active connections</td></tr>';
            return;
        }

        const tbody = document.getElementById('dsn-tbody');
        tbody.innerHTML = stations.map(s => `
            <tr>
                <td>${s.station}</td>
                <td>${s.dish}</td>
                <td>${s.downlink}</td>
                <td>${s.uplink}</td>
                <td>${s.rtlt}</td>
            </tr>
        `).join('');
    }

    /**
     * Update space weather panel
     */
    updateWeather(weather) {
        if (!weather) return;

        document.getElementById('kp-index').textContent = 
            `${weather.kpIndex} (${weather.kpLabel})`;
        document.getElementById('noaa-scales').textContent = 
            `G${weather.noaaScales.G}  S${weather.noaaScales.S}  R${weather.noaaScales.R}`;
        document.getElementById('wind-speed').textContent = 
            `${weather.windSpeed} km/s`;
        document.getElementById('wind-density').textContent = 
            `${weather.windDensity} p/cm³`;
        document.getElementById('imf-bz').textContent = 
            `${weather.imfBz} nT`;
        document.getElementById('wind-temp').textContent = 
            `${weather.windTemp} K`;
    }

    /**
     * Update alerts and events panel
     */
    updateAlerts(events) {
        const alertsList = document.getElementById('alerts-list');

        if (!events || events.length === 0) {
            alertsList.innerHTML = '<li class="none">No active alerts</li>';
            return;
        }

        alertsList.innerHTML = events.slice(0, 10).map(event => {
            const className = event.type === 'CME' ? 'cme' : 'flare';
            const icon = event.type === 'CME' ? '[*]' : '[!]';
            const time = new Date(event.time).toLocaleString();
            return `<li class="${className}">${icon} ${event.title} ${time}</li>`;
        }).join('');
    }

    /**
     * Update photo panel
     */
    /**
     * Show photo at given index
     */
    showPhoto(index) {
        const placeholder = document.getElementById('photo-placeholder');
        const image = document.getElementById('photo-image');

        if (!this.photos || this.photos.length === 0) {
            placeholder.textContent = 'No photos available';
            placeholder.style.display = 'block';
            image.style.display = 'none';
            return;
        }

        const idx = index % this.photos.length;
        const photo = this.photos[idx];

        if (image.getAttribute('data-url') !== photo.image_url) {
            image.onerror = () => {
                image.style.display = 'none';
                placeholder.textContent = photo.title || 'Image unavailable';
                placeholder.style.display = 'block';
            };
            image.onload = () => {
                image.style.display = 'block';
                placeholder.style.display = 'none';
                // Update title below image
                const title = document.getElementById('photo-title');
                if (title) title.textContent = `${photo.title} (${idx + 1}/${this.photos.length})`;
            };
            image.setAttribute('data-url', photo.image_url);
            image.src = photo.image_url;
            image.alt = photo.title || 'Mission Photo';
        }
    }

    /**
     * Rotate to next photo
     */
    rotatePhoto() {
        if (this.photos.length <= 1) return;
        this.photoIndex = (this.photoIndex + 1) % this.photos.length;
        this.showPhoto(this.photoIndex);
    }

    /**
     * Update status bar
     */
    updateStatus(status = 'ready') {
        const statusContent = document.getElementById('status-content');
        const lastUpdate = document.getElementById('last-update');

        const now = new Date();
        lastUpdate.textContent = `Updated ${now.toLocaleTimeString()}`;

        if (status === 'error') {
            statusContent.textContent = 'Error: Check connection';
            statusContent.style.color = '#ff6666';
        } else {
            statusContent.textContent = 'Dashboard ready';
            statusContent.style.color = '#88ff99';
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new Dashboard();
    dashboard.init();
});
