"""Data API endpoints for data generation and management."""

from bottle import route, request, response, static_file
import os
import json
from datetime import datetime
from typing import Dict, Any

from services.data_generator import (
    sun_weather_generator, strava_generator, data_file_manager
)


@route('/api/data/sun-weather', method='POST')
def generate_sun_weather():
    """Generate sun and weather data for a city."""
    try:
        data = request.json
        if not data:
            response.status = 400
            return {'success': False, 'error': 'JSON data required'}
        
        city_name = data.get('city_name', '').strip()
        year = data.get('year', datetime.now().year)
        
        if not city_name:
            response.status = 400
            return {'success': False, 'error': 'City name is required'}
        
        if not isinstance(year, int) or year < 1900 or year > 2100:
            response.status = 400
            return {'success': False, 'error': 'Year must be between 1900 and 2100'}
        
        # Validate city first
        validation = sun_weather_generator.validate_city(city_name)
        if not validation['valid']:
            response.status = 400
            return {
                'success': False,
                'error': validation['error']
            }
        
        # Generate data
        result = sun_weather_generator.generate_data(city_name, year)
        
        if not result['success']:
            response.status = 500
            return result
        
        return result
        
    except Exception as e:
        response.status = 500
        return {
            'success': False,
            'error': f'Server error: {str(e)}'
        }


@route('/api/data/strava/auth-url', method='GET')
def get_strava_auth_url():
    """Get Strava OAuth authorization URL."""
    try:
        state = request.query.get('state', '')
        result = strava_generator.get_auth_url(state or None)
        
        if not result['success']:
            response.status = 400
            return result
        
        return result
        
    except Exception as e:
        response.status = 500
        return {
            'success': False,
            'error': f'Server error: {str(e)}'
        }


@route('/api/data/strava/callback', method='GET')
def strava_callback():
    """Handle Strava OAuth callback."""
    try:
        code = request.query.get('code', '')
        state = request.query.get('state', '')
        error = request.query.get('error', '')
        
        if error:
            return {
                'success': False,
                'error': f'OAuth error: {error}'
            }
        
        if not code or not state:
            return {
                'success': False,
                'error': 'Missing authorization code or state'
            }
        
        result = strava_generator.handle_oauth_callback(code, state)
        
        if result['success']:
            # Return a simple HTML page for the popup
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Strava Authorization</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px;
                        background: #f5f5f5;
                    }
                    .success { 
                        color: #2ecc71; 
                        font-size: 18px;
                    }
                    .error { 
                        color: #e74c3c; 
                        font-size: 18px;
                    }
                </style>
            </head>
            <body>
                <div class="success">
                    <h2>✅ Successfully connected to Strava!</h2>
                    <p>You can close this window and return to the application.</p>
                </div>
                <script>
                    // Notify parent window
                    if (window.opener) {
                        window.opener.postMessage({
                            type: 'strava_auth_success',
                            state: '""" + state + """'
                        }, '*');
                    }
                    // Auto-close after 3 seconds
                    setTimeout(() => window.close(), 3000);
                </script>
            </body>
            </html>
            """
        else:
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Strava Authorization</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px;
                        background: #f5f5f5;
                    }}
                    .error {{ 
                        color: #e74c3c; 
                        font-size: 18px;
                    }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>❌ Authorization failed</h2>
                    <p>{result['error']}</p>
                    <p>You can close this window and try again.</p>
                </div>
                <script>
                    // Notify parent window
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'strava_auth_error',
                            error: '{result['error']}',
                            state: '{state}'
                        }}, '*');
                    }}
                </script>
            </body>
            </html>
            """
        
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Strava Authorization</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px;
                    background: #f5f5f5;
                }}
                .error {{ 
                    color: #e74c3c; 
                    font-size: 18px;
                }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2>❌ Server Error</h2>
                <p>{str(e)}</p>
                <p>You can close this window and try again.</p>
            </div>
        </body>
        </html>
        """


@route('/api/data/strava/generate', method='POST')
def generate_strava_data():
    """Fetch Strava activities."""
    try:
        data = request.json
        if not data:
            response.status = 400
            return {'success': False, 'error': 'JSON data required'}
        
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        incremental = data.get('incremental', False)
        
        if not start_date or not end_date:
            response.status = 400
            return {'success': False, 'error': 'Start date and end date are required'}
        
        # Validate date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            response.status = 400
            return {'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}
        
        # Generate data
        result = strava_generator.generate_data(start_date, end_date, incremental)
        
        if not result['success']:
            response.status = 500
            return result
        
        return result
        
    except Exception as e:
        response.status = 500
        return {
            'success': False,
            'error': f'Server error: {str(e)}'
        }


@route('/api/data/strava/status', method='GET')
def get_strava_status():
    """Check Strava token status."""
    try:
        result = strava_generator.get_token_status()
        return result
        
    except Exception as e:
        response.status = 500
        return {
            'authenticated': False,
            'error': f'Server error: {str(e)}'
        }


@route('/api/data/strava/disconnect', method='POST')
def disconnect_strava():
    """Disconnect from Strava (clear tokens)."""
    try:
        result = strava_generator.disconnect()
        
        if not result['success']:
            response.status = 500
            return result
        
        return result
        
    except Exception as e:
        response.status = 500
        return {
            'success': False,
            'error': f'Server error: {str(e)}'
        }


@route('/api/data/files', method='GET')
def list_data_files():
    """List all data files with metadata."""
    try:
        files = data_file_manager.list_files()
        return {
            'success': True,
            'files': files
        }
        
    except Exception as e:
        response.status = 500
        return {
            'success': False,
            'error': f'Failed to list files: {str(e)}',
            'files': []
        }


@route('/api/data/files/<filename>')
def download_data_file(filename):
    """Download a data file."""
    try:
        file_path = data_file_manager.download_file(filename)
        
        if not file_path:
            response.status = 404
            return {'error': 'File not found or invalid file type'}
        
        # Set appropriate content type
        response.content_type = 'application/json'
        
        # Set headers for download
        response.set_header('Content-Disposition', f'attachment; filename="{filename}"')
        
        return static_file(filename, root=os.path.dirname(file_path))
        
    except Exception as e:
        response.status = 500
        return {'error': f'Failed to download file: {str(e)}'}


@route('/api/data/files/<filename>', method='DELETE')
def delete_data_file(filename):
    """Delete a data file."""
    try:
        result = data_file_manager.delete_file(filename)
        
        if not result['success']:
            response.status = 400 if 'not found' in result['error'] else 500
            return result
        
        return result
        
    except Exception as e:
        response.status = 500
        return {
            'success': False,
            'error': f'Server error: {str(e)}'
        }
