from bottle import Bottle, run, template, static_file
import os
import sys

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

@app.route('/')
def index():
    return jinja_template('index.html', title='Calendar Builder')

@app.route('/builder')
def builder():
    return jinja_template('builder.html', title='Calendar Builder')

@app.route('/static/<filename:path>')
def static(filename):
    return static_file(filename, root='static')

if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True)