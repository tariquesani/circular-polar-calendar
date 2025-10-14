/**
 * Tools UI JavaScript - Handles data generation and file management
 */

class ToolsUI {
    constructor() {
        this.initializeEventListeners();
        this.stravaAuthWindow = null;
    }

    initializeEventListeners() {
        // Sun & Weather form
        const sunWeatherForm = document.getElementById('sunWeatherForm');
        if (sunWeatherForm) {
            console.log('Found sunWeatherForm, adding event listener');
            sunWeatherForm.addEventListener('submit', (e) => {
                e.preventDefault();
                console.log('Sun Weather form submitted');
                this.handleSunWeatherGeneration();
            });
        } else {
            console.error('sunWeatherForm not found!');
        }

        // Strava form
        document.getElementById('stravaForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleStravaGeneration();
        });

        // Strava authentication buttons
        document.getElementById('connectStravaBtn').addEventListener('click', () => {
            this.connectToStrava();
        });

        document.getElementById('disconnectStravaBtn').addEventListener('click', () => {
            this.disconnectStrava();
        });

        // Delete confirmation modal
        document.getElementById('confirmDeleteBtn').addEventListener('click', () => {
            this.confirmDelete();
        });

        // Listen for messages from OAuth popup
        window.addEventListener('message', (event) => {
            if (event.origin !== window.location.origin) return;
            
            if (event.data.type === 'strava_auth_success') {
                this.handleStravaAuthSuccess(event.data.state);
            } else if (event.data.type === 'strava_auth_error') {
                this.handleStravaAuthError(event.data.error);
            }
        });
    }

    // Sun & Weather Data Generation
    async handleSunWeatherGeneration() {
        const form = document.getElementById('sunWeatherForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        // Convert year to integer
        data.year = parseInt(data.year, 10);
        
        const btn = document.getElementById('generateSunWeatherBtn');
        const status = document.getElementById('sunWeatherStatus');
        
        // Update UI
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Generating...';
        status.innerHTML = '<div class="text-info"><i class="bi bi-hourglass-split"></i> Generating data, please wait...</div>';

        try {
            const response = await fetch('/api/data/sun-weather', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                status.innerHTML = `<div class="alert alert-success">
                    <i class="bi bi-check-circle"></i> ${result.message}
                </div>`;

                // Show location details
                if (result.location) {
                    this.showLocationDetails(result.location);
                }

                // Refresh files list
                this.refreshDataFiles();
            } else {
                status.innerHTML = `<div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> ${result.error}
                </div>`;
            }
        } catch (error) {
            status.innerHTML = `<div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> Network error: ${error.message}
            </div>`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-play-circle"></i> Generate Data';
        }
    }

    showLocationDetails(location) {
        const container = document.getElementById('sunWeatherLocation');
        const info = document.getElementById('locationInfo');
        
        info.innerHTML = `
            <div class="row">
                <div class="col-sm-6">
                    <strong>Name:</strong> ${location.name}<br>
                    <strong>Country:</strong> ${location.country}<br>
                    <strong>Timezone:</strong> ${location.timezone}
                </div>
                <div class="col-sm-6">
                    <strong>Coordinates:</strong><br>
                    ${location.latitude.toFixed(4)}°, ${location.longitude.toFixed(4)}°
                </div>
            </div>
        `;
        
        container.style.display = 'block';
    }

    // Strava Authentication
    async checkStravaStatus() {
        const status = document.getElementById('stravaAuthStatus');
        
        try {
            const response = await fetch('/api/data/strava/status');
            const result = await response.json();

            if (result.authenticated) {
                status.innerHTML = `<div class="alert alert-success">
                    <i class="bi bi-check-circle"></i> ${result.message}
                </div>`;
                
                document.getElementById('connectStravaBtn').style.display = 'none';
                document.getElementById('disconnectStravaBtn').style.display = 'inline-block';
                document.getElementById('fetchActivitiesBtn').disabled = false;
                
                // Update fetch status
                document.getElementById('stravaStatus').innerHTML = 
                    '<div class="text-success">Ready to fetch activities</div>';
            } else {
                status.innerHTML = `<div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i> ${result.message}
                </div>`;
                
                document.getElementById('connectStravaBtn').style.display = 'inline-block';
                document.getElementById('disconnectStravaBtn').style.display = 'none';
                document.getElementById('fetchActivitiesBtn').disabled = true;
                
                // Update fetch status
                document.getElementById('stravaStatus').innerHTML = 
                    '<div class="text-muted">Please connect to Strava first</div>';
            }
        } catch (error) {
            status.innerHTML = `<div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> Failed to check authentication: ${error.message}
            </div>`;
        }
    }

    async connectToStrava() {
        try {
            const response = await fetch('/api/data/strava/auth-url');
            const result = await response.json();

            if (result.success) {
                // Open OAuth popup
                const popup = window.open(
                    result.auth_url,
                    'strava_auth',
                    'width=600,height=700,scrollbars=yes,resizable=yes'
                );
                
                this.stravaAuthWindow = popup;
                
                // Focus on popup
                if (popup) {
                    popup.focus();
                }
            } else {
                this.showError('Failed to get Strava authorization URL: ' + result.error);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }

    handleStravaAuthSuccess(state) {
        // Close popup
        if (this.stravaAuthWindow) {
            this.stravaAuthWindow.close();
            this.stravaAuthWindow = null;
        }
        
        // Refresh status
        this.checkStravaStatus();
        
        this.showSuccess('Successfully connected to Strava!');
    }

    handleStravaAuthError(error) {
        // Close popup
        if (this.stravaAuthWindow) {
            this.stravaAuthWindow.close();
            this.stravaAuthWindow = null;
        }
        
        this.showError('Strava authentication failed: ' + error);
    }

    async disconnectStrava() {
        if (!confirm('Are you sure you want to disconnect from Strava?')) {
            return;
        }

        try {
            const response = await fetch('/api/data/strava/disconnect', {
                method: 'POST'
            });
            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                this.checkStravaStatus();
            } else {
                this.showError('Failed to disconnect: ' + result.error);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }

    // Strava Data Generation
    async handleStravaGeneration() {
        const form = document.getElementById('stravaForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        // Convert incremental to boolean
        data.incremental = formData.has('incremental');
        
        const btn = document.getElementById('fetchActivitiesBtn');
        const status = document.getElementById('stravaStatus');
        
        // Update UI
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Fetching...';
        status.innerHTML = '<div class="text-info"><i class="bi bi-hourglass-split"></i> Fetching activities, please wait...</div>';

        try {
            const response = await fetch('/api/data/strava/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                status.innerHTML = `<div class="alert alert-success">
                    <i class="bi bi-check-circle"></i> ${result.message}
                </div>`;

                // Refresh files list
                this.refreshDataFiles();
            } else {
                status.innerHTML = `<div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> ${result.error}
                </div>`;
            }
        } catch (error) {
            status.innerHTML = `<div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> Network error: ${error.message}
            </div>`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-download"></i> Fetch Activities';
        }
    }

    // Data Files Management
    async refreshDataFiles() {
        const loading = document.getElementById('filesLoading');
        const list = document.getElementById('filesList');
        const empty = document.getElementById('filesEmpty');
        const tableBody = document.getElementById('filesTableBody');
        
        loading.style.display = 'block';
        list.style.display = 'none';
        empty.style.display = 'none';

        try {
            const response = await fetch('/api/data/files');
            const result = await response.json();

            if (result.success && result.files.length > 0) {
                tableBody.innerHTML = '';
                
                result.files.forEach(file => {
                    const row = this.createFileRow(file);
                    tableBody.appendChild(row);
                });
                
                loading.style.display = 'none';
                list.style.display = 'block';
            } else {
                loading.style.display = 'none';
                empty.style.display = 'block';
            }
        } catch (error) {
            loading.style.display = 'none';
            this.showError('Failed to load data files: ' + error.message);
        }
    }

    createFileRow(file) {
        const row = document.createElement('tr');
        
        // Data types badges
        const dataTypes = [];
        if (file.has_weather) dataTypes.push('<span class="badge bg-info">Weather</span>');
        if (file.has_sun) dataTypes.push('<span class="badge bg-warning">Sun</span>');
        if (file.has_strava) dataTypes.push('<span class="badge bg-success">Strava</span>');
        
        row.innerHTML = `
            <td>
                <code>${file.filename}</code>
            </td>
            <td>${file.city_name}</td>
            <td>${file.year}</td>
            <td>${dataTypes.join(' ')}</td>
            <td>${this.formatFileSize(file.file_size)}</td>
            <td>${this.formatDate(file.modified)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <a href="/api/data/files/${file.filename}" class="btn btn-outline-primary" download>
                        <i class="bi bi-download"></i>
                    </a>
                    <button type="button" class="btn btn-outline-danger" onclick="toolsUI.confirmDeleteFile('${file.filename}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        return row;
    }

    confirmDeleteFile(filename) {
        document.getElementById('deleteFileName').textContent = filename;
        this.fileToDelete = filename;
        
        const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        modal.show();
    }

    async confirmDelete() {
        if (!this.fileToDelete) return;

        try {
            const response = await fetch(`/api/data/files/${this.fileToDelete}`, {
                method: 'DELETE'
            });
            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                this.refreshDataFiles();
            } else {
                this.showError('Failed to delete file: ' + result.error);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.fileToDelete = null;
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
            if (modal) {
                modal.hide();
            }
        }
    }

    // Utility functions
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    showSuccess(message) {
        // Create temporary success alert
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show position-fixed';
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            <i class="bi bi-check-circle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }

    showError(message) {
        // Create temporary error alert
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            <i class="bi bi-exclamation-triangle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 8000);
    }
}

// Global functions for inline event handlers
function refreshDataFiles() {
    if (window.toolsUI) {
        window.toolsUI.refreshDataFiles();
    }
}

function checkStravaStatus() {
    if (window.toolsUI) {
        window.toolsUI.checkStravaStatus();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing ToolsUI...');
    window.toolsUI = new ToolsUI();
    console.log('ToolsUI initialized');
});
