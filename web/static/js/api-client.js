/**
 * API Client for Calendar Builder
 * Handles all API communication with the backend
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    /**
     * Make an API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            return data;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // Calendar API methods

    /**
     * Get available layers
     */
    async getLayers() {
        return this.get('/api/calendar/layers');
    }

    /**
     * Get available cities
     */
    async getCities() {
        return this.get('/api/calendar/cities');
    }

    /**
     * Get available themes
     */
    async getThemes() {
        return this.get('/api/calendar/themes');
    }

    /**
     * Validate configuration
     */
    async validateConfig(config) {
        return this.post('/api/calendar/validate', config);
    }

    /**
     * Generate calendar
     */
    async generateCalendar(config) {
        return this.post('/api/calendar/generate', config);
    }

    /**
     * Generate preview
     */
    async generatePreview(config) {
        return this.post('/api/calendar/preview', config);
    }

    /**
     * Get file URL
     */
    getFileURL(filename) {
        return `${this.baseURL}/api/calendar/files/${filename}`;
    }

    // Configuration API methods

    /**
     * List saved configurations
     */
    async listConfigurations(publicOnly = false) {
        const endpoint = publicOnly ? '/api/configurations?public_only=true' : '/api/configurations';
        return this.get(endpoint);
    }

    /**
     * Get specific configuration
     */
    async getConfiguration(name) {
        return this.get(`/api/configurations/${name}`);
    }

    /**
     * Save configuration
     */
    async saveConfiguration(config) {
        return this.post('/api/configurations', config);
    }

    /**
     * Update configuration
     */
    async updateConfiguration(name, config) {
        return this.put(`/api/configurations/${name}`, config);
    }

    /**
     * Delete configuration
     */
    async deleteConfiguration(name) {
        return this.delete(`/api/configurations/${name}`);
    }

    /**
     * Duplicate configuration
     */
    async duplicateConfiguration(name, newName) {
        return this.post(`/api/configurations/${name}/duplicate`, { new_name: newName });
    }

    /**
     * Load configuration by name
     */
    async loadConfiguration(name) {
        return this.get(`/api/configurations/${name}`);
    }

    /**
     * List all configurations
     */
    async listConfigurations(publicOnly = false) {
        return this.get(`/api/configurations?public_only=${publicOnly}`);
    }
}

// Create global instance
const apiClient = new APIClient();
