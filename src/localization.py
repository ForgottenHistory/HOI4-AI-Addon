#!/usr/bin/env python3
"""
HOI4 Localization Reader
Reads localization files from Hearts of Iron IV installation
"""

import re
from pathlib import Path
from typing import Dict, Optional

class HOI4Localizer:
    def __init__(self, hoi4_path: str = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"):
        self.hoi4_path = Path(hoi4_path)
        self.localization_path = self.hoi4_path / "localisation" / "english"
        self.translations: Dict[str, str] = {}
        self.loaded_files = set()
    
    def load_localization_file(self, filename: str) -> int:
        """Load a specific localization file using regex parsing"""
        if filename in self.loaded_files:
            return 0
        
        file_path = self.localization_path / filename
        
        if not file_path.exists():
            print(f"Warning: Localization file not found: {filename}")
            return 0
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            count = 0
            
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#') or line == 'l_english:':
                    continue
                
                # Try two patterns:
                # Pattern 1: key:version "value" (e.g., GER:0 "Germany")
                # Pattern 2: key: "value" (e.g., AUS_political_events.16.t: "Nazis in the Government")
                
                match = None
                
                # Pattern 1: with version number
                pattern1 = r'^\s*([^:]+?):\d+\s+"([^"]*)"'
                match = re.match(pattern1, line)
                
                if not match:
                    # Pattern 2: without version number  
                    pattern2 = r'^\s*([^:]+?):\s+"([^"]*)"'
                    match = re.match(pattern2, line)
                
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    
                    if key and value:
                        self.translations[key] = value
                        count += 1
            
            self.loaded_files.add(filename)
            if count > 0:
                print(f"Loaded {count} translations from {filename}")
            return count
            
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            self.loaded_files.add(filename)
        
        return 0

    def load_all_files(self):
        """Load ALL localization files"""
        if not self.localization_path.exists():
            print(f"Localization path not found: {self.localization_path}")
            return 0
        
        total_loaded = 0
        yml_files = list(self.localization_path.glob("*_l_english.yml"))
        
        print(f"Found {len(yml_files)} localization files")
        
        for file_path in yml_files:
            filename = file_path.name
            loaded = self.load_localization_file(filename)
            total_loaded += loaded
            
            # Show progress every 20 files
            if len(self.loaded_files) % 20 == 0:
                print(f"Processed {len(self.loaded_files)} files...")
        
        print(f"Total translations loaded: {total_loaded}")
        return total_loaded
    
    def get_localized_text(self, key: str) -> str:
        """Get localized text for a key, return key if not found"""
        if key in self.translations:
            return self.translations[key]
        
        # Try variations
        variations = [key.lower(), key.upper()]
        for variant in variations:
            if variant in self.translations:
                return self.translations[variant]
        
        # If not found, return a cleaned version
        return self._clean_key_for_display(key)
    
    def _clean_key_for_display(self, key: str) -> str:
        """Convert a game key to a readable format if no translation found"""
        cleaned = key
        cleaned = re.sub(r'^[A-Z]+_', '', cleaned)
        cleaned = re.sub(r'\.d$', '', cleaned)
        cleaned = re.sub(r'_events\.\d+$', '', cleaned)
        cleaned = cleaned.replace('_', ' ').title()
        return cleaned
    
    def get_country_name(self, tag: str) -> str:
        """Get country name from tag"""
        if tag in self.translations:
            return self.translations[tag]
        
        patterns = [f"{tag}_NAME", f"{tag}_DEF", f"{tag}_ADJ"]
        for pattern in patterns:
            if pattern in self.translations:
                return self.translations[pattern]
        
        return self._clean_key_for_display(tag)
    
    def get_event_name(self, event_id: str) -> str:
        """Get event name/description"""
        # Try direct lookup
        if event_id in self.translations:
            return self.translations[event_id]
        
        # Try with .t suffix (title)
        title_key = f"{event_id}.t"
        if title_key in self.translations:
            return self.translations[title_key]
        
        # If no localization found, return original ID (for hidden events)
        return event_id
    
    def get_idea_name(self, idea_id: str) -> str:
        """Get national idea name"""
        return self.get_localized_text(idea_id)

def test_localizer():
    """Test the localization system"""
    localizer = HOI4Localizer()
    
    if not localizer.localization_path.exists():
        print(f"HOI4 path not found: {localizer.localization_path}")
        return
    
    print("Loading ALL localization files...")
    localizer.load_all_files()
    
    # Test some lookups
    test_keys = ['GER', 'SOV', 'USA', 'sour_loser', 'fascism']
    
    print("\nTest translations:")
    for key in test_keys:
        result = localizer.get_country_name(key) if len(key) == 3 else localizer.get_localized_text(key)
        print(f"  {key} → {result}")
    
    print(f"\nTotal translations available: {len(localizer.translations)}")

if __name__ == "__main__":
    test_localizer()