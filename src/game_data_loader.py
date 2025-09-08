#!/usr/bin/env python3
"""
HOI4 Game Data Loader
Handles loading and extracting game data from JSON files
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

class GameDataLoader:
    """Loads and manages HOI4 game data"""
    
    def __init__(self, json_path: str = "game_data.json"):
        self.json_path = json_path
        self.data: Optional[Dict[str, Any]] = None
    
    def extract_data(self) -> bool:
        """Run Rust extractor to generate JSON data"""
        try:
            print("Running Rust data extractor...")
            result = subprocess.run(["cargo", "run"], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Rust extractor failed: {result.stderr}")
                return False
            
            print("Rust extraction completed successfully")
            return True
            
        except Exception as e:
            print(f"Error running Rust extractor: {e}")
            return False
    
    def load_data(self) -> bool:
        """Load JSON data from file"""
        try:
            if not Path(self.json_path).exists():
                print(f"Data file {self.json_path} not found. Running extractor...")
                if not self.extract_data():
                    return False
            
            with open(self.json_path, 'r') as f:
                self.data = json.load(f)
            
            print(f"Loaded data for {self.data['metadata']['date']}")
            print(f"Events: {len(self.data['events'])}")
            print(f"Active countries: {len(self.data['countries'])}")
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get game metadata"""
        return self.data['metadata'] if self.data else {}
    
    def get_events(self) -> List[str]:
        """Get raw event list"""
        return self.data['events'] if self.data else []
    
    def get_countries(self) -> List[Dict[str, Any]]:
        """Get country data list"""
        return self.data['countries'] if self.data else []
    
    def get_country(self, tag: str) -> Optional[Dict[str, Any]]:
        """Get specific country data by tag"""
        if not self.data:
            return None
        
        for country in self.data['countries']:
            if country['tag'] == tag:
                return country['data']
        return None
    
    def get_player_tag(self) -> str:
        """Get player country tag"""
        return self.data['metadata']['player'] if self.data else ""
    
    def is_loaded(self) -> bool:
        """Check if data is loaded"""
        return self.data is not None