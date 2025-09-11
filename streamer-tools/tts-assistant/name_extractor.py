#!/usr/bin/env python3
"""
Name Extractor for TTS Assistant
Extracts character names from HOI4 locale files for dynamic personality generation
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class NameExtractor:
    """Extracts character names from HOI4 locale files"""
    
    def __init__(self, locale_path: str = None):
        if locale_path is None:
            project_root = Path(__file__).parent.parent.parent
            locale_path = project_root / 'locale'
        
        self.locale_path = Path(locale_path)
        self.character_files = list(self.locale_path.glob('*characters*'))
        print(f"Found {len(self.character_files)} character locale files")
    
    def extract_names_by_country(self) -> Dict[str, List[str]]:
        """Extract character names organized by country"""
        names_by_country = defaultdict(set)
        
        # Pattern to match character entries: COUNTRY_name:number "Display Name"
        pattern = re.compile(r'^[ ]*([A-Z]{3})_([^:]+):\d+[ ]+"([^"]+)"')
        
        for file_path in self.character_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        match = pattern.match(line)
                        
                        if match:
                            country_tag = match.group(1)
                            internal_name = match.group(2)
                            display_name = match.group(3)
                            
                            # Skip placeholder names and variables
                            if '$' in display_name or display_name.startswith('$'):
                                continue
                            
                            # Extract first name (before space or title)
                            first_name = self._extract_first_name(display_name)
                            if first_name and len(first_name) >= 3:  # Minimum name length
                                names_by_country[country_tag].add(first_name)
                                
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        # Convert sets to lists and sort
        return {country: sorted(list(names)) for country, names in names_by_country.items()}
    
    def _extract_first_name(self, display_name: str) -> str:
        """Extract first name from display name"""
        # Remove common titles and prefixes
        prefixes_to_remove = [
            'Kaiser', 'König', 'Führer', 'General', 'Admiral', 'Field Marshal',
            'Generalfeldmarschall', 'Großadmiral', 'President', 'Chancellor',
            'Prime Minister', 'Marshal', 'Colonel', 'Major', 'Captain',
            'Reichsführer', 'SS-', 'von', 'zu', 'de', 'el', 'al-'
        ]
        
        # Split name into parts
        parts = display_name.split()
        
        # Find first part that's not a title/prefix
        for part in parts:
            clean_part = part.strip('.,')
            
            # Skip if it's a known prefix
            if any(clean_part.startswith(prefix) for prefix in prefixes_to_remove):
                continue
            
            # Skip single letters (initials)
            if len(clean_part) <= 2:
                continue
                
            # Return first valid name part
            return clean_part
        
        # Fallback: return first part if nothing else worked
        if parts:
            return parts[0].strip('.,')
        
        return display_name
    
    def generate_names_config(self, output_path: str = None) -> Dict[str, List[str]]:
        """Generate and save names configuration"""
        if output_path is None:
            output_path = Path(__file__).parent.parent.parent / 'data' / 'personas' / 'tts-assistant' / 'extracted_names.json'
        
        names_by_country = self.extract_names_by_country()
        
        # Filter to major countries and ensure minimum names
        major_countries = ['GER', 'SOV', 'USA', 'UK', 'FRA', 'JAP', 'ITA', 'CHI']
        filtered_names = {}
        
        for country in major_countries:
            if country in names_by_country and len(names_by_country[country]) >= 5:
                # Take up to 20 names to keep it manageable
                filtered_names[country] = names_by_country[country][:20]
        
        # Save to file
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(filtered_names, f, ensure_ascii=False, indent=2)
            
            print(f"Saved extracted names to: {output_path}")
            
        except Exception as e:
            print(f"Error saving names: {e}")
        
        return filtered_names
    
    def print_summary(self):
        """Print summary of extracted names"""
        names_by_country = self.extract_names_by_country()
        
        print("\n=== Character Name Extraction Summary ===")
        for country, names in sorted(names_by_country.items()):
            if len(names) >= 3:  # Only show countries with reasonable name counts
                sample_names = names[:5] if len(names) > 5 else names
                print(f"{country}: {len(names)} names - {', '.join(sample_names)}...")
        
        print(f"\nTotal countries with names: {len(names_by_country)}")

def test_extractor():
    """Test the name extractor"""
    extractor = NameExtractor()
    extractor.print_summary()
    names_config = extractor.generate_names_config()
    
    print(f"\n=== Final Config Preview ===")
    for country, names in names_config.items():
        print(f"{country}: {names}")

if __name__ == '__main__':
    test_extractor()