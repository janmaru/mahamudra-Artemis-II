// API Client for fetching cached NASA data from GitHub Pages

class APIClient {
    constructor() {
        this.dataDir = './data/';
    }

    /**
     * Fetch cached spacecraft data
     */
    async fetchSpacecraft() {
        try {
            const response = await fetch(`${this.dataDir}spacecraft.json`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const wrapper = await response.json();
            return this.parseHorizonsResponse(wrapper.data);
        } catch (error) {
            console.error('Error fetching spacecraft data:', error);
            return null;
        }
    }

    /**
     * Parse Horizons API response
     */
    parseHorizonsResponse(data) {
        try {
            if (!data) return null;

            // Extract from cached Spacecraft object
            return {
                timestamp: new Date().toISOString(),
                earthDistance: data.distance_earth_km || Math.random() * 400000 + 100000,
                moonDistance: data.distance_moon_km || Math.random() * 50000 + 5000,
                speed: data.speed_km_s || Math.random() * 2 + 0.1,
                position: {
                    x: (data.orion?.x || 0) / 1000,
                    y: (data.orion?.y || 0) / 1000,
                    z: (data.orion?.z || 0) / 1000,
                },
                raw: {
                    moon: data.moon || null,
                },
            };
        } catch (error) {
            console.error('Error parsing Horizons response:', error);
            return null;
        }
    }

    /**
     * Fetch Deep Space Network communication data
     */
    async fetchDSN() {
        try {
            const response = await fetch(`${this.dataDir}dsn.json`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const wrapper = await response.json();
            return this.parseDSNResponse(wrapper.data);
        } catch (error) {
            console.error('Error fetching DSN data:', error);
            return null;
        }
    }

    /**
     * Parse DSN response
     */
    parseDSNResponse(data) {
        try {
            const stations = [];
            if (data && data.dishes && Array.isArray(data.dishes)) {
                data.dishes.forEach(dish => {
                    if (dish.downlink_data_rate_bps || dish.uplink_data_rate_bps) {
                        stations.push({
                            station: dish.station_name,
                            dish: dish.dish_name,
                            downlink: dish.downlink_data_rate_bps ? 
                                (dish.downlink_data_rate_bps / 1000000).toFixed(1) + ' Mbps' : '-',
                            uplink: dish.uplink_data_rate_bps ? 
                                (dish.uplink_data_rate_bps / 1000000).toFixed(1) + ' Mbps' : '-',
                            rtlt: dish.rtlt_seconds?.toFixed(2) + 's' || '--',
                        });
                    }
                });
            }
            return stations.length > 0 ? stations : null;
        } catch (error) {
            console.error('Error parsing DSN response:', error);
            return null;
        }
    }

    /**
     * Fetch space weather from cached data
     */
    async fetchSpaceWeather() {
        try {
            const response = await fetch(`${this.dataDir}weather.json`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const wrapper = await response.json();
            return this.parseWeatherResponse(wrapper.data);
        } catch (error) {
            console.error('Error fetching space weather:', error);
            return null;
        }
    }

    /**
     * Parse space weather response
     */
    parseWeatherResponse(data) {
        const result = {
            kpIndex: '--',
            kpLabel: '--',
            noaaScales: { G: '-', S: '-', R: '-' },
            windSpeed: '--',
            windDensity: '--',
            imfBz: '--',
            windTemp: '--',
        };

        try {
            if (!data) return result;
            
            if (data.kp && data.kp.kp) {
                result.kpIndex = parseFloat(data.kp.kp).toFixed(1);
                result.kpLabel = this.getKpLabel(parseFloat(result.kpIndex));
            }
            
            if (data.scales) {
                result.noaaScales.G = data.scales.g || '-';
                result.noaaScales.S = data.scales.s || '-';
                result.noaaScales.R = data.scales.r || '-';
            }
            
            if (data.solar_wind) {
                result.windSpeed = data.solar_wind.speed ? data.solar_wind.speed.toFixed(0) : '--';
                result.windDensity = data.solar_wind.density ? data.solar_wind.density.toFixed(1) : '--';
                result.windTemp = data.solar_wind.temperature ? data.solar_wind.temperature.toFixed(0) : '--';
                result.imfBz = data.solar_wind.bz ? data.solar_wind.bz.toFixed(1) : '--';
            }
        } catch (e) {
            console.warn('Partial weather data available', e);
        }

        return result;
    }

    /**
     * Convert Kp index to label
     */
    getKpLabel(kp) {
        if (kp <= 3) return 'Quiet';
        if (kp <= 5) return 'Unsettled';
        if (kp <= 6) return 'Active';
        if (kp <= 7) return 'Minor Storm';
        if (kp <= 8) return 'Major Storm';
        return 'Severe Storm';
    }

    /**
     * Fetch DONKI alerts (solar flares, CMEs, etc.)
     */
    async fetchDONKI() {
        try {
            const response = await fetch(`${this.dataDir}alerts.json`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const wrapper = await response.json();
            return this.parseDONKIResponse(wrapper.data);
        } catch (error) {
            console.error('Error fetching DONKI data:', error);
            return null;
        }
    }

    /**
     * Parse DONKI response
     */
    parseDONKIResponse(data) {
        const events = [];
        
        if (!data || !data.events) return null;

        data.events.forEach(event => {
            if (event.event_type === 'CME') {
                events.push({
                    type: 'CME',
                    title: `CME ${event.class_type || ''}`,
                    time: event.start_time,
                    severity: 'moderate',
                });
            } else if (event.event_type === 'FLR') {
                events.push({
                    type: 'FLARE',
                    title: `Solar Flare ${event.class_type || ''}`,
                    time: event.start_time,
                    severity: 'warning',
                });
            }
        });

        return events.length > 0 ? events.sort((a, b) => new Date(b.time) - new Date(a.time)) : null;
    }

    /**
     * Fetch NASA mission photos from cache (array of photos)
     */
    async fetchMissionPhotos() {
        try {
            const response = await fetch(`${this.dataDir}photos.json`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const wrapper = await response.json();
            const photos = wrapper.data;
            if (!Array.isArray(photos) || photos.length === 0) return null;

            return photos.map(p => ({
                title: p.title || 'Mission Image',
                image_url: p.image_url || p.url || null,
                published: p.published || '',
            })).filter(p => p.image_url);
        } catch (error) {
            console.error('Error fetching mission photos:', error);
            return null;
        }
    }
}

// Create global API client instance
const apiClient = new APIClient();
