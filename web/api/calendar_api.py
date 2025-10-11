"""Calendar API endpoints for calendar generation and metadata."""

from bottle import route, request, response, static_file
import os
import json
from datetime import datetime
from typing import Dict, Any

from services.calendar_builder import calendar_builder, CalendarBuilderError


@route('/api/calendar/generate', method='POST')
def generate_calendar():
    """Generate calendar from web configuration."""
    try:
        data = request.json
        if not data:
            response.status = 400
            return {'success': False, 'error': 'JSON data required'}
        
        # Generate calendar
        result = calendar_builder.build_calendar(data, preview_mode=False)
        
        if not result['success']:
            response.status = 400 if 'validation' in result.get('error', '') else 500
            return result
        
        return result
        
    except Exception as e:
        response.status = 500
        return {
            'success': False,
            'error': f'Server error: {str(e)}'
        }


@route('/api/calendar/preview', method='POST')
def preview_calendar():
    """Generate preview of calendar."""
    try:
        data = request.json
        if not data:
            response.status = 400
            return {'success': False, 'error': 'JSON data required'}
        
        # Generate preview
        result = calendar_builder.build_calendar(data, preview_mode=True)
        
        if not result['success']:
            response.status = 400 if 'validation' in result.get('error', '') else 500
            return result
        
        return result
        
    except Exception as e:
        response.status = 500
        return {
            'success': False,
            'error': f'Server error: {str(e)}'
        }


@route('/api/calendar/validate', method='POST')
def validate_configuration():
    """Validate calendar configuration."""
    try:
        data = request.json
        if not data:
            response.status = 400
            return {'valid': False, 'errors': ['JSON data required']}
        
        validation = calendar_builder.validate_config(data)
        return validation
        
    except Exception as e:
        response.status = 500
        return {
            'valid': False,
            'errors': [f'Validation error: {str(e)}']
        }


@route('/api/calendar/layers', method='GET')
def list_layers():
    """List all available calendar layers."""
    try:
        layers = calendar_builder.get_available_layers()
        return {'layers': layers}
        
    except Exception as e:
        response.status = 500
        return {
            'error': f'Failed to list layers: {str(e)}',
            'layers': []
        }


@route('/api/calendar/cities', method='GET')
def list_cities():
    """List all available cities with data."""
    try:
        cities = calendar_builder.get_available_cities()
        return {'cities': cities}
        
    except Exception as e:
        response.status = 500
        return {
            'error': f'Failed to list cities: {str(e)}',
            'cities': []
        }


@route('/api/calendar/themes', method='GET')
def list_themes():
    """List predefined color themes."""
    try:
        themes = [
            {
                'id': 'default',
                'name': 'Default',
                'colors': {
                    'night': '#011F26',
                    'daylight': '#fbba43',
                    'astro': '#092A38',
                    'nautical': '#0A3F4D',
                    'civil': '#1C5C7C',
                    'background': '#faf0e6',
                    'divider': '#02735E',
                    'dial': '#FFFFFF',
                    'time_label': '#e7fdeb',
                    'month_label': '#2F4F4F',
                    'sunday_label': '#696969',
                    'title_text': '#000000',
                    'temperature': 'YlOrRd',
                    'precipitation': 'Blues'
                }
            },
            {
                'id': 'iceland',
                'name': 'Iceland',
                'colors': {
                    'night': '#133052',
                    'daylight': '#e4edf4',
                    'astro': '#35637d',
                    'nautical': '#82a6be',
                    'civil': '#b7cddb',
                    'background': '#faf0e6',
                    'divider': '#02735E',
                    'dial': '#FFFFFF',
                    'time_label': '#e7fdeb',
                    'month_label': '#2F4F4F',
                    'sunday_label': '#696969',
                    'title_text': '#000000',
                    'temperature': 'Blues',
                    'precipitation': 'Blues'
                }
            },
            {
                'id': 'monochrome',
                'name': 'Monochrome',
                'colors': {
                    'night': '#595959',
                    'daylight': '#ffffff',
                    'astro': '#6a6a6a',
                    'nautical': '#7a7a7a',
                    'civil': '#8b8b8b',
                    'background': '#ffffff',
                    'divider': '#02735E',
                    'dial': '#000000',
                    'time_label': '#000000',
                    'month_label': '#505050',
                    'sunday_label': '#696969',
                    'title_text': '#000000',
                    'temperature': 'Greys',
                    'precipitation': 'Greys'
                }
            },
            {
                'id': 'dark',
                'name': 'Dark Mode',
                'colors': {
                    'night': '#011F26',
                    'daylight': '#fbba43',
                    'astro': '#092A38',
                    'nautical': '#0A3F4D',
                    'civil': '#1C5C7C',
                    'background': '#1a1a1a',
                    'divider': '#02735E',
                    'dial': '#FFFFFF',
                    'time_label': '#e7fdeb',
                    'month_label': '#808080',
                    'sunday_label': '#696969',
                    'title_text': '#a6a6a6',
                    'temperature': 'YlOrRd',
                    'precipitation': 'Blues'
                }
            }
        ]
        
        return {'themes': themes}
        
    except Exception as e:
        response.status = 500
        return {
            'error': f'Failed to list themes: {str(e)}',
            'themes': []
        }


@route('/api/calendar/files/<filename>')
def serve_generated_file(filename):
    """Serve generated calendar files."""
    try:
        # Security: only allow files in the generated directory
        # Use absolute path to ensure we're looking in the right place
        import os
        current_dir = os.path.dirname(os.path.dirname(__file__))
        generated_dir = os.path.join(current_dir, 'generated')
        file_path = os.path.join(generated_dir, filename)
        
        if not os.path.exists(file_path):
            response.status = 404
            return {'error': 'File not found'}
        
        # Check if it's a valid file type
        if not filename.endswith(('.png', '.pdf')):
            response.status = 400
            return {'error': 'Invalid file type'}
        
        # Set appropriate content type
        if filename.endswith('.png'):
            response.content_type = 'image/png'
        elif filename.endswith('.pdf'):
            response.content_type = 'application/pdf'
        
        # Set cache headers
        response.set_header('Cache-Control', 'public, max-age=3600')
        
        return static_file(filename, root=generated_dir)
        
    except Exception as e:
        response.status = 500
        return {'error': f'Failed to serve file: {str(e)}'}


@route('/api/calendar/cleanup', method='POST')
def cleanup_files():
    """Clean up old generated files."""
    try:
        data = request.json or {}
        max_age_days = data.get('max_age_days', 7)
        
        calendar_builder.cleanup_old_files(max_age_days)
        
        return {'success': True, 'message': f'Cleaned up files older than {max_age_days} days'}
        
    except Exception as e:
        response.status = 500
        return {
            'success': False,
            'error': f'Cleanup failed: {str(e)}'
        }
