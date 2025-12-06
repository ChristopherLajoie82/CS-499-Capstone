"""
Settings manager for Paint Tracking System
Manages dropdown options that can be edited by users
"""

import json
from pathlib import Path
from typing import List

class SettingsManager:
    """Manages application settings including dropdown options"""
    
    def __init__(self):
        self.settings_dir = Path.home() / ".paint_tracker"
        self.settings_dir.mkdir(exist_ok=True)
        self.settings_file = self.settings_dir / "dropdown_settings.json"
        
        # Default options
        self.defaults = {
            "manufacturers": [
                "PANTONE",
                "MATTHEWS PAINT",
                "SHERWIN-WILLIAMS",
                "BENJAMIN MOORE"
            ],
            "paint_versions": [
                "1.0", "1.1", "1.2", 
                "2.0", "2.1", "2.2",
                "3.0"
            ]
        }
        
        self.load_settings()
    
    def load_settings(self):
        """Load settings from file or use defaults"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
                # Add any missing keys from defaults
                for key, value in self.defaults.items():
                    if key not in self.settings:
                        self.settings[key] = value
            except (json.JSONDecodeError, IOError):
                self.settings = self.defaults.copy()
        else:
            self.settings = self.defaults.copy()
            self.save_settings()
    
    def save_settings(self):
        """Save current settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def get_manufacturers(self) -> List[str]:
        """Get list of manufacturers"""
        return self.settings.get("manufacturers", self.defaults["manufacturers"])
    
    def add_manufacturer(self, name: str) -> bool:
        """Add a new manufacturer"""
        if name and name not in self.settings["manufacturers"]:
            self.settings["manufacturers"].append(name)
            self.settings["manufacturers"].sort()
            self.save_settings()
            return True
        return False
    
    def get_paint_versions(self) -> List[str]:
        """Get list of paint versions"""
        return self.settings.get("paint_versions", self.defaults["paint_versions"])
    
    def add_paint_version(self, version: str) -> bool:
        """Add a new paint version"""
        if version and version not in self.settings["paint_versions"]:
            self.settings["paint_versions"].append(version)
            self.settings["paint_versions"].sort()
            self.save_settings()
            return True
        return False
