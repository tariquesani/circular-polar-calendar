"""Data Generator Service - Wraps generator scripts for web interface."""

import os
import sys
import json
import time
from datetime import datetime, date, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Add parent directory to path to import generator modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import generator classes
from generators.generator_sun_weather import (
    Location, AstralDataCalculator, WeatherDataCalculator, 
    DataInterpolator, DataProcessor
)

# Strava imports
from stravalib.client import Client
from dotenv import load_dotenv

# Load environment config
load_dotenv()


class SunWeatherGenerator:
    """Service for generating sun and weather data."""
    
    def __init__(self):
        self.data_dir = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
        self.data_dir.mkdir(exist_ok=True)
    
    def generate_data(self, city_name: str, year: int) -> Dict[str, Any]:
        """
        Generate sun and weather data for a city.
        
        Args:
            city_name: Name of the city
            year: Year for data generation
            
        Returns:
            Dict with success status, file path, and location details
        """
        try:
            # Create data processor
            processor = DataProcessor(city_name, year)
            
            # Process data
            data = processor.process_data()
            
            # Generate filename
            filename = f"{city_name}_data.json"
            filepath = self.data_dir / filename
            
            # Save data
            with filepath.open('w') as f:
                json.dump(data, f, indent=4)
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'location': {
                    'name': processor.location.name,
                    'country': processor.location.country,
                    'timezone': processor.location.timezone,
                    'latitude': processor.location.latitude,
                    'longitude': processor.location.longitude
                },
                'year': year,
                'message': f"Successfully generated data for {city_name} ({year})"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to generate data: {str(e)}"
            }
    
    def validate_city(self, city_name: str) -> Dict[str, Any]:
        """
        Validate if a city can be processed.
        
        Args:
            city_name: Name of the city to validate
            
        Returns:
            Dict with validation status and location details
        """
        try:
            location = Location.from_city_name(city_name)
            return {
                'valid': True,
                'location': {
                    'name': location.name,
                    'country': location.country,
                    'timezone': location.timezone,
                    'latitude': location.latitude,
                    'longitude': location.longitude
                }
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f"Invalid city: {str(e)}"
            }


class StravaGenerator:
    """Service for generating Strava activity data."""
    
    def __init__(self):
        self.tokens_file = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'generators', 'strava_tokens.json'))
        self.output_file = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'strava_activities.json'))
        self.data_dir = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
        self.data_dir.mkdir(exist_ok=True)
        
        # Load environment variables
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        
        # OAuth state for web integration
        self.oauth_state = {}
    
    def get_auth_url(self, state: str = None) -> Dict[str, Any]:
        """
        Get Strava OAuth authorization URL.
        
        Args:
            state: Optional state parameter for OAuth flow
            
        Returns:
            Dict with authorization URL and state
        """
        if not self.client_id:
            return {
                'success': False,
                'error': 'Strava CLIENT_ID not configured in environment variables'
            }
        
        if state is None:
            state = f"web_{int(time.time())}"
        
        self.oauth_state[state] = {
            'timestamp': time.time(),
            'status': 'pending'
        }
        
        auth_url = (
            f"https://www.strava.com/oauth/authorize?"
            f"client_id={self.client_id}&"
            f"response_type=code&"
            f"redirect_uri=http://localhost:8080/api/data/strava/callback&"
            f"scope=activity:read_all&"
            f"approval_prompt=force&"
            f"state={state}"
        )
        
        return {
            'success': True,
            'auth_url': auth_url,
            'state': state
        }
    
    def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for tokens.
        
        Args:
            code: Authorization code from Strava
            state: State parameter from OAuth flow
            
        Returns:
            Dict with success status
        """
        if not self.client_secret:
            return {
                'success': False,
                'error': 'Strava CLIENT_SECRET not configured in environment variables'
            }
        
        if state not in self.oauth_state:
            return {
                'success': False,
                'error': 'Invalid OAuth state'
            }
        
        try:
            client = Client()
            tokens = client.exchange_code_for_token(
                client_id=self.client_id,
                client_secret=self.client_secret,
                code=code
            )
            
            # Save tokens
            self.save_tokens(tokens)
            
            # Update state
            self.oauth_state[state]['status'] = 'completed'
            self.oauth_state[state]['tokens'] = tokens
            
            return {
                'success': True,
                'message': 'Successfully authenticated with Strava'
            }
            
        except Exception as e:
            self.oauth_state[state]['status'] = 'error'
            return {
                'success': False,
                'error': f'OAuth callback failed: {str(e)}'
            }
    
    def get_token_status(self) -> Dict[str, Any]:
        """
        Check if Strava tokens exist and are valid.
        
        Returns:
            Dict with token status and expiry information
        """
        try:
            tokens = self.load_tokens()
            
            if not tokens:
                return {
                    'authenticated': False,
                    'message': 'No Strava tokens found'
                }
            
            # Check if token is expired
            expires_at = tokens.get('expires_at', 0)
            if expires_at <= time.time():
                return {
                    'authenticated': False,
                    'expired': True,
                    'message': 'Strava tokens have expired'
                }
            
            # Calculate expiry date
            expiry_date = datetime.fromtimestamp(expires_at)
            
            return {
                'authenticated': True,
                'expires_at': expires_at,
                'expiry_date': expiry_date.isoformat(),
                'message': f'Authenticated with Strava (expires {expiry_date.strftime("%Y-%m-%d %H:%M")})'
            }
            
        except Exception as e:
            return {
                'authenticated': False,
                'error': f'Failed to check token status: {str(e)}'
            }
    
    def generate_data(self, start_date: str, end_date: str, incremental: bool = False) -> Dict[str, Any]:
        """
        Fetch Strava activities and save to file.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            incremental: Whether to fetch incrementally from last activity
            
        Returns:
            Dict with success status, activity count, and file path
        """
        try:
            # Check authentication
            token_status = self.get_token_status()
            if not token_status['authenticated']:
                return {
                    'success': False,
                    'error': 'Not authenticated with Strava. Please connect first.'
                }
            
            # Load tokens
            tokens = self.load_tokens()
            
            # Create client and set token
            client = Client()
            client.access_token = tokens['access_token']
            
            # Parse dates
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Handle incremental mode
            if incremental:
                last_activity_date = self.get_last_activity_date()
                if last_activity_date:
                    start_dt = max(start_dt, last_activity_date)
            
            # Fetch activities
            activities = self.fetch_activities(client, start_dt, end_dt)
            
            if not activities:
                return {
                    'success': True,
                    'activity_count': 0,
                    'message': 'No new activities found in the specified date range'
                }
            
            # Handle incremental mode for file saving
            if incremental and self.output_file.exists():
                existing_activities = json.load(self.output_file.open('r'))
                activities = existing_activities + activities
            
            # Save activities
            json.dump(activities, self.output_file.open('w'), indent=4)
            
            return {
                'success': True,
                'activity_count': len(activities),
                'filepath': str(self.output_file),
                'message': f'Successfully fetched {len(activities)} activities'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to fetch activities: {str(e)}'
            }
    
    def disconnect(self) -> Dict[str, Any]:
        """
        Clear Strava tokens.
        
        Returns:
            Dict with success status
        """
        try:
            if self.tokens_file.exists():
                self.tokens_file.unlink()
            
            # Clear OAuth state
            self.oauth_state.clear()
            
            return {
                'success': True,
                'message': 'Successfully disconnected from Strava'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to disconnect: {str(e)}'
            }
    
    def load_tokens(self) -> Dict[str, Any]:
        """Load tokens from file."""
        if self.tokens_file.exists():
            return json.load(self.tokens_file.open('r'))
        return {}
    
    def save_tokens(self, tokens: Dict[str, Any]) -> None:
        """Save tokens to file."""
        json.dump(tokens, self.tokens_file.open('w'))
    
    def get_last_activity_date(self) -> Optional[datetime]:
        """Get the last activity date from the output file."""
        if self.output_file.exists():
            activities = json.load(self.output_file.open('r'))
            if activities:
                last_activity = max(activities, key=lambda x: x["start_date"])
                dt = datetime.fromisoformat(last_activity["start_date"])
                # Return timezone-naive datetime for consistent comparison
                return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt
        return None
    
    def fetch_activities(self, client: Client, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch and format Strava activities."""
        return [{
            "id": activity.id,
            "name": activity.name,
            "start_date": activity.start_date_local.isoformat(),
            "distance": activity.distance,
            "moving_time": activity.moving_time,
            "elapsed_time": activity.elapsed_time,
            "type": activity.type.root,
            "average_speed": activity.average_speed
        } for activity in client.get_activities(after=start_date, before=end_date)]


class DataFileManager:
    """Service for managing data files."""
    
    def __init__(self):
        self.data_dir = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
    
    def list_files(self) -> List[Dict[str, Any]]:
        """
        List all data files with metadata.
        
        Returns:
            List of file information dictionaries
        """
        files = []
        
        if not self.data_dir.exists():
            return files
        
        for file_path in self.data_dir.glob("*_data.json"):
            try:
                # Load file to get metadata
                with file_path.open('r') as f:
                    data = json.load(f)
                
                # Get file stats
                stat = file_path.stat()
                
                files.append({
                    'filename': file_path.name,
                    'filepath': str(file_path),
                    'city_name': data.get('year', 'Unknown'),
                    'year': data.get('year', 2025),
                    'has_weather': 'temperature' in data and 'precipitation' in data,
                    'has_sun': 'sunrise' in data and 'sunset' in data,
                    'has_strava': file_path.name == 'strava_activities.json',
                    'file_size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'coordinates': data.get('coordinates', {})
                })
                
            except Exception:
                # Skip corrupted files
                continue
        
        return sorted(files, key=lambda x: (x['city_name'], -x['year']))
    
    def delete_file(self, filename: str) -> Dict[str, Any]:
        """
        Delete a data file.
        
        Args:
            filename: Name of file to delete
            
        Returns:
            Dict with success status
        """
        try:
            # Security check - only allow data files
            if not filename.endswith('_data.json') and filename != 'strava_activities.json':
                return {
                    'success': False,
                    'error': 'Invalid file type'
                }
            
            file_path = self.data_dir / filename
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'File not found'
                }
            
            file_path.unlink()
            
            return {
                'success': True,
                'message': f'Successfully deleted {filename}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to delete file: {str(e)}'
            }
    
    def download_file(self, filename: str) -> Optional[str]:
        """
        Get file path for download.
        
        Args:
            filename: Name of file to download
            
        Returns:
            File path if exists, None otherwise
        """
        # Security check
        if not filename.endswith('_data.json') and filename != 'strava_activities.json':
            return None
        
        file_path = self.data_dir / filename
        
        if file_path.exists():
            return str(file_path)
        
        return None


# Initialize service instances
sun_weather_generator = SunWeatherGenerator()
strava_generator = StravaGenerator()
data_file_manager = DataFileManager()
