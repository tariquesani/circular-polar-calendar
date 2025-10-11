from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional
import json
import os

@dataclass
class SavedConfiguration:
    name: str
    description: str
    created_at: str  # ISO format string
    updated_at: str
    config_data: Dict[str, Any]
    is_public: bool = False
    tags: list = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

class ConfigStorage:
    def __init__(self, storage_path=None):
        if storage_path is None:
            # Use the web directory storage folder
            import os
            current_dir = os.path.dirname(os.path.dirname(__file__))
            storage_path = os.path.join(current_dir, "storage", "configurations")
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def _filename_to_name(self, filename):
        """Convert filename to configuration name"""
        return filename.replace('.json', '').replace('_', ' ').title()
    
    def _name_to_filename(self, name):
        """Convert configuration name to filename"""
        return name.lower().replace(' ', '_').replace(' ', '_') + '.json'
    
    def save_configuration(self, config: SavedConfiguration):
        """Save configuration to JSON file"""
        filename = self._name_to_filename(config.name)
        filepath = os.path.join(self.storage_path, filename)
        
        with open(filepath, 'w') as f:
            f.write(config.to_json())
    
    def get_configuration(self, name: str) -> Optional[SavedConfiguration]:
        """Get configuration by name"""
        filename = self._name_to_filename(name)
        filepath = os.path.join(self.storage_path, filename)
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return SavedConfiguration(**data)
        except FileNotFoundError:
            return None
    
    def list_configurations(self, public_only=False):
        """List all saved configurations"""
        configs = []
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                config = self.get_configuration(self._filename_to_name(filename))
                if config and (not public_only or config.is_public):
                    configs.append(config)
        
        return sorted(configs, key=lambda x: x.updated_at, reverse=True)
    
    def delete_configuration(self, name: str):
        """Delete configuration file"""
        filename = self._name_to_filename(name)
        filepath = os.path.join(self.storage_path, filename)
        
        try:
            os.remove(filepath)
            return True
        except FileNotFoundError:
            return False
    
    def duplicate_configuration(self, original_name: str, new_name: str):
        """Duplicate an existing configuration"""
        original = self.get_configuration(original_name)
        if not original:
            return None
        
        new_config = SavedConfiguration(
            name=new_name,
            description=f"{original.description} (Copy)",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            config_data=original.config_data.copy(),
            is_public=False,
            tags=original.tags.copy()
        )
        
        self.save_configuration(new_config)
        return new_config
