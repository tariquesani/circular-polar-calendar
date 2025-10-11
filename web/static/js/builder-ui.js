/**
 * Builder UI Controller
 * Handles the calendar builder interface interactions
 */

class BuilderUI {
    constructor() {
        this.apiClient = apiClient;
        this.currentConfig = this.getDefaultConfig();
        this.previewTimeout = null;
        this.themes = []; // Store themes data
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
                this.updateConfig();
                this.toggleWallpaperSettings();
                this.schedulePreviewUpdate();
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
            console.log('Theme changed, updating config...');
            this.updateConfig();
            this.schedulePreviewUpdate();
        });

        // Retry button
        document.getElementById('retry-btn')?.addEventListener('click', () => {
            this.generateCalendar();
        });

        // Generate preview button
        document.getElementById('generate-preview-btn')?.addEventListener('click', () => {
            this.updateConfig();
            this.updatePreview();
        });

        // Wallpaper settings
        document.getElementById('resolution-select')?.addEventListener('change', () => {
            this.toggleCustomResolution();
            this.updateConfig();
            this.schedulePreviewUpdate();
        });
        
        // Custom position inputs
        document.getElementById('custom-pos-left')?.addEventListener('change', () => {
            this.updateConfig();
            this.schedulePreviewUpdate();
        });
        
        document.getElementById('custom-pos-bottom')?.addEventListener('change', () => {
            this.updateConfig();
            this.schedulePreviewUpdate();
        });
        
        document.getElementById('custom-pos-width')?.addEventListener('change', () => {
            this.updateConfig();
            this.schedulePreviewUpdate();
        });
        
        document.getElementById('custom-pos-height')?.addEventListener('change', () => {
            this.updateConfig();
            this.schedulePreviewUpdate();
        });
        
        document.getElementById('dark-mode')?.addEventListener('change', () => {
            this.updateConfig();
            this.schedulePreviewUpdate();
        });
        
        // Custom resolution inputs
        document.getElementById('custom-width')?.addEventListener('change', () => {
            this.updateConfig();
            this.schedulePreviewUpdate();
        });
        
        document.getElementById('custom-height')?.addEventListener('change', () => {
            this.updateConfig();
            this.schedulePreviewUpdate();
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
            checkbox.addEventListener('change', (event) => {
                // Handle mutual exclusivity between Sunday and Holidays layers
                this.handleLayerExclusivity(event.target);
                
                this.updateConfig();
                this.updateLayerSpecificSettingsVisibility();
                this.schedulePreviewUpdate();
            });
        });
    }

    /**
     * Handle mutual exclusivity between conflicting layers
     */
    handleLayerExclusivity(checkbox) {
        const layerId = checkbox.value;
        
        // Sunday and Holidays layers are mutually exclusive
        if (layerId === 'sunday' && checkbox.checked) {
            const holidaysCheckbox = document.getElementById('layer-holidays');
            if (holidaysCheckbox && holidaysCheckbox.checked) {
                holidaysCheckbox.checked = false;
                this.showLayerNotification('Holidays layer unchecked - it includes Sunday labels');
            }
        }
        
        if (layerId === 'holidays' && checkbox.checked) {
            const sundayCheckbox = document.getElementById('layer-sunday');
            if (sundayCheckbox && sundayCheckbox.checked) {
                sundayCheckbox.checked = false;
                this.showLayerNotification('Sunday layer unchecked - Holidays layer includes Sunday labels');
            }
        }
        
        // Temperature and Precipitation layers are mutually exclusive
        if (layerId === 'temperature' && checkbox.checked) {
            const precipitationCheckbox = document.getElementById('layer-precipitation');
            if (precipitationCheckbox && precipitationCheckbox.checked) {
                precipitationCheckbox.checked = false;
                this.showLayerNotification('Precipitation layer unchecked - only one weather layer can be active');
            }
        }
        
        if (layerId === 'precipitation' && checkbox.checked) {
            const temperatureCheckbox = document.getElementById('layer-temperature');
            if (temperatureCheckbox && temperatureCheckbox.checked) {
                temperatureCheckbox.checked = false;
                this.showLayerNotification('Temperature layer unchecked - only one weather layer can be active');
            }
        }
    }

    /**
     * Show a brief notification for layer exclusivity
     */
    showLayerNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
        notification.innerHTML = `
            <i class="bi bi-info-circle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
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
            this.themes = response.themes; // Store themes data
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
        
        // Set default theme to "default" if available
        const defaultTheme = themes.find(t => t.id === 'default');
        if (defaultTheme) {
            select.value = 'default';
            console.log('Setting default theme:', defaultTheme.name);
            this.applyThemeColors('default');
        }
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

        // Get wallpaper settings if format is wallpaper
        if (this.currentConfig.format_type === 'wallpaper') {
            this.updateWallpaperSettings();
        }

        // Get layer-specific settings
        this.updateLayerSpecificSettings();

        // Get theme colors if selected
        const themeSelect = document.getElementById('theme-select');
        if (themeSelect?.value) {
            this.applyThemeColors(themeSelect.value);
        }
    }
    
    /**
     * Update wallpaper settings
     */
    updateWallpaperSettings() {
        const resolutionSelect = document.getElementById('resolution-select');
        const darkModeCheckbox = document.getElementById('dark-mode');
        
        // Get resolution settings
        const resolution = resolutionSelect?.value || 'hd';
        let width, height;
        
        if (resolution === 'custom') {
            const customWidth = document.getElementById('custom-width');
            const customHeight = document.getElementById('custom-height');
            width = parseInt(customWidth?.value) || 1920;
            height = parseInt(customHeight?.value) || 1080;
        } else {
            const resolutions = {
                'hd': { width: 1920, height: 1080 },
                '4k': { width: 3840, height: 2160 }
            };
            const res = resolutions[resolution] || resolutions['hd'];
            width = res.width;
            height = res.height;
        }
        
        // Get position settings (always custom)
        const customPosLeft = document.getElementById('custom-pos-left');
        const customPosBottom = document.getElementById('custom-pos-bottom');
        const customPosWidth = document.getElementById('custom-pos-width');
        const customPosHeight = document.getElementById('custom-pos-height');
        
        const calendarPosition = {
            left: parseFloat(customPosLeft?.value) || -0.3,
            bottom: parseFloat(customPosBottom?.value) || -1.2,
            width: parseFloat(customPosWidth?.value) || 1.02,
            height: parseFloat(customPosHeight?.value) || 2.3
        };
        
        // Set wallpaper settings
        this.currentConfig.wallpaper = {
            resolution: resolution,
            width: width,
            height: height,
            position: calendarPosition,
            dark_mode: darkModeCheckbox?.checked || false
        };
    }

    /**
     * Update layer-specific settings based on selected layers
     */
    updateLayerSpecificSettings() {
        // Strava layer settings
        if (this.currentConfig.layers.includes('strava')) {
            const runningTarget = document.getElementById('strava-running-target');
            const footerOffset = document.getElementById('strava-footer-offset');
            const footerHeight = document.getElementById('strava-footer-height');
            
            if (runningTarget) {
                this.currentConfig.strava_running_target = parseInt(runningTarget.value) || 1000;
            }
            if (footerOffset) {
                this.currentConfig.strava_footer_offset = parseFloat(footerOffset.value) || 0;
            }
            if (footerHeight) {
                this.currentConfig.strava_footer_height = parseFloat(footerHeight.value) || 0.1;
            }
        }
    }
    
    /**
     * Show/hide layer-specific settings based on selected layers
     */
    updateLayerSpecificSettingsVisibility() {
        // Hide all layer-specific settings first
        document.querySelectorAll('.layer-settings').forEach(settings => {
            settings.style.display = 'none';
        });
        
        // Show settings for selected layers
        this.currentConfig.layers.forEach(layerId => {
            const settingsElement = document.getElementById(`${layerId}-settings`);
            if (settingsElement) {
                settingsElement.style.display = 'block';
            }
        });
    }

    /**
     * Apply theme colors to configuration
     */
    applyThemeColors(themeId) {
        console.log('applyThemeColors called with themeId:', themeId);
        console.log('Available themes:', this.themes);
        
        const theme = this.themes.find(t => t.id === themeId);
        if (theme && theme.colors) {
            console.log('Applying theme colors:', theme.name, theme.colors);
            this.currentConfig.colors = { ...theme.colors };
            console.log('Updated currentConfig.colors:', this.currentConfig.colors);
        } else {
            console.log('Theme not found or no colors defined:', themeId);
            console.log('Found theme:', theme);
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
        console.log('Colors in config:', this.currentConfig.colors);
        
        if (!this.currentConfig.city_name || this.currentConfig.layers.length === 0) {
            console.log('No city or layers selected, showing placeholder');
            this.showPreviewPlaceholder();
            return;
        }

        try {
            console.log('Generating preview...');
            this.showPreviewLoading();
            this.setPreviewButtonLoading(true);
            
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
        } finally {
            this.setPreviewButtonLoading(false);
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
                    <p class="mt-3">Select a city and layers to see preview</p>
                </div>
            `;
        }
        // Ensure preview button is enabled
        this.setPreviewButtonLoading(false);
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
     * Set preview button loading state
     */
    setPreviewButtonLoading(loading) {
        const button = document.getElementById('generate-preview-btn');
        if (button) {
            if (loading) {
                button.disabled = true;
                button.innerHTML = '<i class="bi bi-hourglass-split"></i> Generating...';
                button.classList.add('loading');
            } else {
                button.disabled = false;
                button.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Generate Preview';
                button.classList.remove('loading');
            }
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
     * Toggle custom resolution inputs visibility
     */
    toggleCustomResolution() {
        const resolutionSelect = document.getElementById('resolution-select');
        const customInputs = document.getElementById('custom-resolution-inputs');
        
        if (resolutionSelect && customInputs) {
            customInputs.style.display = resolutionSelect.value === 'custom' ? 'block' : 'none';
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
