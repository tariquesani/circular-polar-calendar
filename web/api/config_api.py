from bottle import route, request, response
import json
from services.config_storage import storage
from models.config_models import SavedConfiguration
from datetime import datetime

@route('/api/configurations', method='GET')
def list_configurations():
    """List all saved configurations"""
    public_only = request.query.get('public_only', 'false').lower() == 'true'
    configs = storage.list_configurations(public_only=public_only)
    return {'configurations': [config.to_dict() for config in configs]}

@route('/api/configurations', method='POST')
def save_configuration():
    """Save a new configuration"""
    data = request.json
    
    config = SavedConfiguration(
        name=data['name'],
        description=data.get('description', ''),
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        config_data=data['config_data'],
        is_public=data.get('is_public', False),
        tags=data.get('tags', [])
    )
    
    storage.save_configuration(config)
    return {'success': True, 'name': config.name}

@route('/api/configurations/<name>', method='GET')
def get_configuration(name):
    """Get a specific configuration"""
    config = storage.get_configuration(name)
    if not config:
        response.status = 404
        return {'error': 'Configuration not found'}
    
    return config.to_dict()

@route('/api/configurations/<name>', method='PUT')
def update_configuration(name):
    """Update an existing configuration"""
    config = storage.get_configuration(name)
    if not config:
        response.status = 404
        return {'error': 'Configuration not found'}
    
    data = request.json
    config.name = data.get('name', config.name)
    config.description = data.get('description', config.description)
    config.config_data = data.get('config_data', config.config_data)
    config.is_public = data.get('is_public', config.is_public)
    config.tags = data.get('tags', config.tags)
    config.updated_at = datetime.now().isoformat()
    
    storage.save_configuration(config)
    return {'success': True}

@route('/api/configurations/<name>', method='DELETE')
def delete_configuration(name):
    """Delete a configuration"""
    success = storage.delete_configuration(name)
    if not success:
        response.status = 404
        return {'error': 'Configuration not found'}
    
    return {'success': True}

@route('/api/configurations/<name>/duplicate', method='POST')
def duplicate_configuration(name):
    """Duplicate an existing configuration"""
    data = request.json
    new_name = data.get('new_name', f"{name} Copy")
    
    new_config = storage.duplicate_configuration(name, new_name)
    if not new_config:
        response.status = 404
        return {'error': 'Original configuration not found'}
    
    return {'success': True, 'name': new_config.name}
