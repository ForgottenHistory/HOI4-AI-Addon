#!/usr/bin/env python3
"""
Configuration Loader for Twitter Stream Tool
Loads and validates configuration from config.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration loader"""
        if config_path is None:
            # Default to config.json in the same directory
            config_path = Path(__file__).parent / "config.json"
        
        self.config_path = Path(config_path)
        self._config = None
        self.load()
    
    def load(self) -> None:
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                print(f"[OK] Configuration loaded from {self.config_path}")
            else:
                print(f"[WARN] Configuration file not found: {self.config_path}")
                print("Using default configuration...")
                self._config = self._get_default_config()
        except Exception as e:
            print(f"[ERROR] Error loading configuration: {e}")
            print("Using default configuration...")
            self._config = self._get_default_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'persona_selection.citizen_boost_chance')"""
        if not self._config:
            return default
        
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        if not self._config:
            return {}
        return self._config.get(section, {})
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        if not self._config:
            self._config = {}
        
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def save(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
            print(f"[OK] Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Error saving configuration: {e}")
            return False
    
    def reload(self) -> None:
        """Reload configuration from file"""
        self.load()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file doesn't exist"""
        return {
            "stream_settings": {
                "auto_generation_interval": 30,
                "max_tweets_stored": 50,
                "server_port": 5000,
                "debug_mode": False
            },
            "persona_selection": {
                "citizen_boost_chance": 0.5,
                "journalist_avoid_chance": 0.85,
                "leader_selection_chance": 0.6,
                "official_selection_chance": 0.3,
                "country_specific_boost": 0.7,
                "satirical_persona_chance": 0.2
            },
            "content_generation": {
                "enable_ideological_country_names": True,
                "show_leader_names": True,
                "show_ideology_in_summary": True,
                "max_world_powers_displayed": 11,
                "max_minor_powers_displayed": 4,
                "include_recent_focuses": True,
                "focus_progress_thresholds": {
                    "completing": 80,
                    "advancing": 50,
                    "ongoing": 0
                }
            },
            "ai_generation": {
                "model_name": "gpt-4o-mini",
                "max_tokens": 300,
                "temperature": 0.8,
                "enable_ai_logs": True,
                "ai_log_directory": "ai_logs"
            }
        }
    
    def print_config(self) -> None:
        """Print current configuration for debugging"""
        print("[CONFIG] Current Configuration:")
        print("=" * 50)
        print(json.dumps(self._config, indent=2))
        print("=" * 50)

# Global configuration instance
config = ConfigLoader()

def get_config() -> ConfigLoader:
    """Get the global configuration instance"""
    return config

def reload_config() -> None:
    """Reload the global configuration"""
    config.reload()

# Convenience functions for common settings
def get_auto_interval() -> int:
    """Get auto generation interval in seconds"""
    return config.get('stream_settings.auto_generation_interval', 30)

def get_citizen_boost() -> float:
    """Get citizen persona boost chance"""
    return config.get('persona_selection.citizen_boost_chance', 0.5)

def get_journalist_avoid() -> float:
    """Get journalist avoidance chance"""
    return config.get('persona_selection.journalist_avoid_chance', 0.85)

def get_leader_chance() -> float:
    """Get leader selection chance"""
    return config.get('persona_selection.leader_selection_chance', 0.6)

def is_satirical_enabled() -> bool:
    """Check if satirical personas are enabled"""
    return config.get('persona_categories.enable_satirical', True)

def get_ai_model() -> str:
    """Get AI model name"""
    return config.get('ai_generation.model_name', 'gpt-4o-mini')

def get_max_tokens() -> int:
    """Get max AI tokens"""
    return config.get('ai_generation.max_tokens', 300)

def get_temperature() -> float:
    """Get AI temperature"""
    return config.get('ai_generation.temperature', 0.8)

def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return config.get('stream_settings.debug_mode', False)

if __name__ == "__main__":
    # Test the configuration loader
    config = ConfigLoader()
    config.print_config()
    
    print(f"Auto interval: {get_auto_interval()}s")
    print(f"Citizen boost: {get_citizen_boost()*100}%")
    print(f"Journalist avoid: {get_journalist_avoid()*100}%")
    print(f"AI Model: {get_ai_model()}")