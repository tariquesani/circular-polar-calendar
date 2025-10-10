/**
 * Builder UI Controller
 * Handles the calendar builder interface interactions
 */

class BuilderUI {
    constructor() {
        this.apiClient = apiClient;
        this.currentConfig = this.getDefaultConfig();
        this.previewTimeout = null;
        this.initializeEventListeners();
    }

    /**
     * Get default configuration
     */
    getDefaultConfig() {
        return {
            city_name: '',
            year: 2025,
            layers: ['dawn'],
            colors: {},
            format_type: 'calendar',
            smoothen: false,
            interval: 0.25
        };
    }

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        // Generate button
        document.getElementById('generate-btn')?.addEventListener('click', () => {
            this.generateCalendar();
        });

        // Save/Load configuration buttons
        document.getElementById('save-config-btn')?.addEventListener('click', () => {
            this.showSaveConfigModal();
        });

        document.getElementById('load-config-btn')?.addEventListener('click', () => {
            this.showLoadConfigModal();
        });

        // Format type change
        document.querySelectorAll('input[name="format_type"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.toggleWallpaperSettings();
            });
        });

        // Form inputs for live preview
        document.getElementById('city-select')?.addEventListener('change', () => {
            this.updateConfig();
            this.schedulePreviewUpdate();
        });

        document.getElementById('year-input')?.addEventListener('change', () => {
            this.updateConfig();
            this.schedulePreviewUpdate();
        });

        document.getElementById('theme-select')?.addEventListener('change', () => {
            this.updateConfig();
            this.schedulePreviewUpdate();
        });

        // Retry button
        document.getElementById('retry-btn')?.addEventListener('click', () => {
            this.generateCalendar();
        });
    }

    /**
     * Initialize the builder UI
     */
    async initialize() {
        try {
            console.log('Initializing builder UI...');
            
            await Promise.all([
                this.loadLayers(),
                this.loadCities(),
                this.loadThemes()
            ]);

            console.log('All data loaded, scheduling preview update...');
            
            // Don't generate preview immediately - wait for user to select city
            this.showPreviewPlaceholder();
        } catch (error) {
            console.error('Failed to initialize builder:', error);
            this.showError('Failed to initialize builder. Please refresh the page.');
        }
    }

    /**
     * Load available layers
     */
    async loadLayers() {
        try {
            const response = await this.apiClient.getLayers();
            this.renderLayers(response.layers);
        } catch (error) {
            console.error('Failed to load layers:', error);
            this.showLayerError('Failed to load layers');
        }
    }

    /**
     * Render layers in the UI
     */
    renderLayers(layers) {
        const container = document.getElementById('layers-container');
        if (!container) return;

        container.innerHTML = layers.map(layer => `
            <div class="layer-item" data-layer-id="${layer.id}">
                <div class="form-check">
                    <input class="form-check-input layer-checkbox" type="checkbox" 
                           value="${layer.id}" id="layer-${layer.id}" 
                           ${this.currentConfig.layers.includes(layer.id) ? 'checked' : ''}>
                    <label class="form-check-label layer-info" for="layer-${layer.id}">
                        <h6>${layer.name}</h6>
                        <small>${layer.description}</small>
                    </label>
                </div>
            </div>
        `).join('');

        // Add event listeners to checkboxes
        container.querySelectorAll('.layer-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateConfig();
                this.schedulePreviewUpdate();
            });
        });
    }

    /**
     * Show layer loading error
     */
    showLayerError(message) {
        const container = document.getElementById('layers-container');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle"></i> ${message}
                </div>
            `;
        }
    }

    /**
     * Load available cities
     */
    async loadCities() {
        try {
            const response = await this.apiClient.getCities();
            this.renderCities(response.cities);
        } catch (error) {
            console.error('Failed to load cities:', error);
            this.showCityError('Failed to load cities');
        }
    }

    /**
     * Render cities in the dropdown
     */
    renderCities(cities) {
        const select = document.getElementById('city-select');
        if (!select) return;

        select.innerHTML = '<option value="">Select a city...</option>' +
            cities.map(city => `
                <option value="${city.name}" 
                        ${this.currentConfig.city_name === city.name ? 'selected' : ''}>
                    ${city.name} ${city.has_weather ? '🌡️' : ''} ${city.has_sun ? '☀️' : ''}
                </option>
            `).join('');

        if (this.currentConfig.city_name) {
            select.value = this.currentConfig.city_name;
        }
    }

    /**
     * Show city loading error
     */
    showCityError(message) {
        const select = document.getElementById('city-select');
        if (select) {
            select.innerHTML = `<option value="">${message}</option>`;
        }
    }

    /**
     * Load available themes
     */
    async loadThemes() {
        try {
            const response = await this.apiClient.getThemes();
            this.renderThemes(response.themes);
        } catch (error) {
            console.error('Failed to load themes:', error);
            this.showThemeError('Failed to load themes');
        }
    }

    /**
     * Render themes in the dropdown
     */
    renderThemes(themes) {
        const select = document.getElementById('theme-select');
        if (!select) return;

        select.innerHTML = '<option value="">Select a theme...</option>' +
            themes.map(theme => `
                <option value="${theme.id}">${theme.name}</option>
            `).join('');
    }

    /**
     * Show theme loading error
     */
    showThemeError(message) {
        const select = document.getElementById('theme-select');
        if (select) {
            select.innerHTML = `<option value="">${message}</option>`;
        }
    }

    /**
     * Update configuration from form inputs
     */
    updateConfig() {
        // Get selected layers
        const layerCheckboxes = document.querySelectorAll('.layer-checkbox:checked');
        this.currentConfig.layers = Array.from(layerCheckboxes).map(cb => cb.value);

        // Get other form values
        this.currentConfig.city_name = document.getElementById('city-select')?.value || '';
        this.currentConfig.year = parseInt(document.getElementById('year-input')?.value) || 2025;
        this.currentConfig.format_type = document.querySelector('input[name="format_type"]:checked')?.value || 'calendar';
        this.currentConfig.smoothen = document.getElementById('smoothen-toggle')?.checked || false;
        this.currentConfig.interval = parseFloat(document.getElementById('interval-input')?.value) / 60 || 0.25;

        // Get theme colors if selected
        const themeSelect = document.getElementById('theme-select');
        if (themeSelect?.value) {
            // This will be handled when themes are loaded
        }
    }

    /**
     * Schedule a preview update (debounced)
     */
    schedulePreviewUpdate() {
        if (this.previewTimeout) {
            clearTimeout(this.previewTimeout);
        }

        this.previewTimeout = setTimeout(() => {
            this.updatePreview();
        }, 1000);
    }

    /**
     * Update the preview
     */
    async updatePreview() {
        console.log('Updating preview with config:', this.currentConfig);
        
        if (!this.currentConfig.city_name || this.currentConfig.layers.length === 0) {
            console.log('No city or layers selected, showing placeholder');
            this.showPreviewPlaceholder();
            return;
        }

        try {
            console.log('Generating preview...');
            this.showPreviewLoading();
            const response = await this.apiClient.generatePreview(this.currentConfig);
            
            console.log('Preview response:', response);
            
            if (response.success) {
                console.log('Preview generated successfully, showing image:', response.preview_url);
                this.showPreview(response.preview_url);
            } else {
                console.log('Preview generation failed:', response.error);
                this.showPreviewError(response.error);
            }
        } catch (error) {
            console.error('Preview generation failed:', error);
            this.showPreviewError(error.message);
        }
    }

    /**
     * Show preview loading state
     */
    showPreviewLoading() {
        const container = document.getElementById('preview-container');
        if (container) {
            container.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Generating preview...</span>
                    </div>
                    <p class="mt-2">Generating preview...</p>
                </div>
            `;
        }
    }

    /**
     * Show preview image
     */
    showPreview(imageUrl) {
        console.log('Showing preview image:', imageUrl);
        const container = document.getElementById('preview-container');
        if (container) {
            const img = document.createElement('img');
            img.src = imageUrl;
            img.alt = 'Calendar Preview';
            img.className = 'preview-image';
            
            img.onload = () => {
                console.log('Preview image loaded successfully');
                container.innerHTML = '';
                container.appendChild(img);
            };
            
            img.onerror = (event) => {
                console.error('Preview image failed to load:', event);
                container.innerHTML = `
                    <div class="alert alert-warning" role="alert">
                        <i class="bi bi-exclamation-triangle"></i> Preview failed to load
                        <br><small>This might be due to CORS restrictions or server issues.</small>
                        <br><small>URL: ${imageUrl}</small>
                    </div>
                `;
            };
            
            // Show loading state while image loads
            container.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading preview...</span>
                    </div>
                    <p class="mt-2">Loading preview...</p>
                </div>
            `;
        }
    }

    /**
     * Show preview placeholder
     */
    showPreviewPlaceholder() {
        const container = document.getElementById('preview-container');
        if (container) {
            container.innerHTML = `
                <div class="preview-placeholder">
                    <i class="bi bi-calendar3 display-1 text-muted"></i>
                    <p class="mt-3">Select a city and layers to see preview</p>
                </div>
            `;
        }
    }

    /**
     * Show preview error
     */
    showPreviewError(error) {
        const container = document.getElementById('preview-container');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="bi bi-exclamation-triangle"></i> Preview Error: ${error}
                </div>
            `;
        }
    }

    /**
     * Toggle wallpaper settings visibility
     */
    toggleWallpaperSettings() {
        const wallpaperSettings = document.getElementById('wallpaper-settings');
        const formatType = document.querySelector('input[name="format_type"]:checked')?.value;
        
        if (wallpaperSettings) {
            wallpaperSettings.style.display = formatType === 'wallpaper' ? 'block' : 'none';
        }
    }

    /**
     * Generate calendar
     */
    async generateCalendar() {
        this.updateConfig();

        if (!this.currentConfig.city_name) {
            this.showError('Please select a city');
            return;
        }

        if (this.currentConfig.layers.length === 0) {
            this.showError('Please select at least one layer');
            return;
        }

        try {
            this.showGenerating();
            const response = await this.apiClient.generateCalendar(this.currentConfig);
            
            if (response.success) {
                this.showResults(response);
            } else {
                this.showError(response.error);
            }
        } catch (error) {
            console.error('Calendar generation failed:', error);
            this.showError(error.message);
        }
    }

    /**
     * Show generating state
     */
    showGenerating() {
        const generateBtn = document.getElementById('generate-btn');
        if (generateBtn) {
            generateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Generating...';
            generateBtn.disabled = true;
        }
    }

    /**
     * Show results
     */
    showResults(response) {
        // Reset generate button
        const generateBtn = document.getElementById('generate-btn');
        if (generateBtn) {
            generateBtn.innerHTML = '<i class="bi bi-play-circle"></i> Generate Calendar';
            generateBtn.disabled = false;
        }

        // Show results section
        const resultsSection = document.getElementById('results-section');
        const errorSection = document.getElementById('error-section');
        
        if (resultsSection) {
            document.getElementById('generated-filename').textContent = response.filename;
            document.getElementById('generation-time').textContent = new Date().toLocaleString();
            
            const downloadPngBtn = document.getElementById('download-png-btn');
            const downloadPdfBtn = document.getElementById('download-pdf-btn');
            
            if (downloadPngBtn) downloadPngBtn.href = response.png_url;
            if (downloadPdfBtn) downloadPdfBtn.href = response.pdf_url;
            
            resultsSection.style.display = 'block';
        }

        if (errorSection) {
            errorSection.style.display = 'none';
        }

        // Scroll to results
        resultsSection?.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Show error
     */
    showError(error) {
        // Reset generate button
        const generateBtn = document.getElementById('generate-btn');
        if (generateBtn) {
            generateBtn.innerHTML = '<i class="bi bi-play-circle"></i> Generate Calendar';
            generateBtn.disabled = false;
        }

        // Show error section
        const resultsSection = document.getElementById('results-section');
        const errorSection = document.getElementById('error-section');
        
        if (errorSection) {
            document.getElementById('error-message').textContent = error;
            errorSection.style.display = 'block';
        }

        if (resultsSection) {
            resultsSection.style.display = 'none';
        }

        // Scroll to error
        errorSection?.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Show save configuration modal
     */
    showSaveConfigModal() {
        const modal = new bootstrap.Modal(document.getElementById('saveConfigModal'));
        modal.show();
    }

    /**
     * Show load configuration modal
     */
    showLoadConfigModal() {
        const modal = new bootstrap.Modal(document.getElementById('loadConfigModal'));
        modal.show();
        this.loadConfigurationsList();
    }

    /**
     * Load configurations list
     */
    async loadConfigurationsList() {
        // This will be implemented in the next step
        console.log('Loading configurations list...');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const builderUI = new BuilderUI();
    builderUI.initialize();
    
    // Make it globally accessible for debugging
    window.builderUI = builderUI;
});
