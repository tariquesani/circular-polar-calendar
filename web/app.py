from bottle import Bottle, run, template, static_file
import os
import sys
import socket
from zeroconf import Zeroconf, ServiceInfo

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Configure Jinja2 template engine
from jinja2 import Environment, FileSystemLoader

app = Bottle()

# Set the template directory
template_dir = os.path.join(os.path.dirname(__file__), 'templates')

# Configure Jinja2 environment
jinja_env = Environment(loader=FileSystemLoader(template_dir))

def jinja_template(template_name, **kwargs):
    """Render template using Jinja2"""
    template = jinja_env.get_template(template_name)
    return template.render(**kwargs)

# Import API routes and mount them
from api.config_api import (
    list_configurations, save_configuration, get_configuration,
    update_configuration, delete_configuration, duplicate_configuration
)
from api.calendar_api import (
    generate_calendar, preview_calendar, validate_configuration,
    list_layers, list_cities, list_themes, serve_generated_file, cleanup_files
)

# Import data API routes
from api.data_api import (
    generate_sun_weather, get_strava_auth_url, strava_callback,
    generate_strava_data, get_strava_status, disconnect_strava,
    list_data_files, download_data_file, delete_data_file
)

# Import CalendarBuilder for automatic cleanup
from services.calendar_builder import CalendarBuilder

def perform_startup_cleanup():
    """Perform automatic cleanup of old generated files on startup."""
    try:
        # print("Performing automatic cleanup of old generated files...")
        calendar_builder = CalendarBuilder()
        calendar_builder.cleanup_old_files(max_age_days=7)  # Clean files older than 7 days
        # print("Automatic cleanup completed successfully.")
    except Exception as e:
        print(f"Warning: Automatic cleanup failed: {str(e)}")

# Perform automatic cleanup on startup
perform_startup_cleanup()

# === Zeroconf Setup ===
def check_existing_mdns_service(port=8080):
    """Check if mDNS service is already running and return hostname if found."""
    try:
        zeroconf = Zeroconf()
        hostname = socket.gethostname()
        print(f"Hostname: {hostname}")
        
        # Check if we can resolve our own hostname
        try:
            ip = socket.gethostbyname(hostname)
            print(f"Server is accessible at: {hostname}:{port}")
            zeroconf.close()
            return True
        except socket.gaierror:
            zeroconf.close()
            return False
    except Exception as e:
        print(f"Error checking existing mDNS service: {e}")
        return False

def register_mdns_service(port=8080):
    """Register mDNS service only if not already running."""
    if check_existing_mdns_service(port):
        print("mDNS service appears to already be running. Using existing hostname.")
        return None
    
    zeroconf = Zeroconf()
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

    service_info = ServiceInfo(
        type_="_http._tcp.local.",
        name="Tarique EPD Server._http._tcp.local.",
        addresses=[socket.inet_aton(ip)],
        port=port,
        properties={},
        server="tariquesani.local."
    )

    zeroconf.register_service(service_info)
    # print(f"Zeroconf service registered as 'tariquesani.local:{port}'")
    return zeroconf

# Mount configuration API routes
app.route('/api/configurations', method='GET')(list_configurations)
app.route('/api/configurations', method='POST')(save_configuration)
app.route('/api/configurations/<name>', method='GET')(get_configuration)
app.route('/api/configurations/<name>', method='PUT')(update_configuration)
app.route('/api/configurations/<name>', method='DELETE')(delete_configuration)
app.route('/api/configurations/<name>/duplicate', method='POST')(duplicate_configuration)

# Mount calendar API routes
app.route('/api/calendar/generate', method='POST')(generate_calendar)
app.route('/api/calendar/preview', method='POST')(preview_calendar)
app.route('/api/calendar/validate', method='POST')(validate_configuration)
app.route('/api/calendar/layers', method='GET')(list_layers)
app.route('/api/calendar/cities', method='GET')(list_cities)
app.route('/api/calendar/themes', method='GET')(list_themes)
app.route('/api/calendar/files/<filename>')(serve_generated_file)
app.route('/api/calendar/cleanup', method='POST')(cleanup_files)

# Mount data API routes
app.route('/api/data/sun-weather', method='POST')(generate_sun_weather)
app.route('/api/data/strava/auth-url', method='GET')(get_strava_auth_url)
app.route('/api/data/strava/callback', method='GET')(strava_callback)
app.route('/api/data/strava/generate', method='POST')(generate_strava_data)
app.route('/api/data/strava/status', method='GET')(get_strava_status)
app.route('/api/data/strava/disconnect', method='POST')(disconnect_strava)
app.route('/api/data/files', method='GET')(list_data_files)
app.route('/api/data/files/<filename>')(download_data_file)
app.route('/api/data/files/<filename>', method='DELETE')(delete_data_file)

@app.route('/')
def index():
    return jinja_template('index.html', title='Home')

@app.route('/builder')
def builder():
    return jinja_template('builder.html', title='Builder')

@app.route('/tools')
def tools():
    return jinja_template('tools.html', title='Data Tools')

@app.route('/static/<filename:path>')
def static(filename):
    return static_file(filename, root='static')

# === Run Server ===
if __name__ == '__main__':
    port = 8080
    zeroconf = register_mdns_service(port)
    try:
        run(app, host='0.0.0.0', port=port, debug=True)
    finally:
        if zeroconf is not None:
            zeroconf.unregister_all_services()
            zeroconf.close()