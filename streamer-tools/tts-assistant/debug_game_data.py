#!/usr/bin/env python3
"""
Debug script to examine game data structure
"""

import json
import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

from game_data_loader import GameDataLoader
from game_event_service import GameEventService
from localization import HOI4Localizer

def main():
    print("=== Game Data Debug ===\n")
    
    # Load game data directly like other streaming tools
    data_path = project_root / 'data' / 'game_data.json'
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        print(f"✓ Game data loaded successfully")
        print(f"✓ Keys in game_data: {list(game_data.keys())}")
        
        if 'countries' in game_data:
            countries = game_data['countries']
            print(f"✓ Countries type: {type(countries)}")
            
            if isinstance(countries, list):
                print(f"✓ Number of countries: {len(countries)}")
                # Show first few countries
                for i, country in enumerate(countries[:3]):
                    if isinstance(country, dict):
                        tag = country.get('tag')
                        data = country.get('data', {})
                        major = data.get('major', False)
                        print(f"  [{i}] {tag}: major={major}")
                        if tag == 'GER':
                            print(f"    GER data keys: {list(data.keys())}")
                            if 'focus' in data:
                                focus = data['focus']
                                print(f"    GER focus: {focus}")
                            if 'politics' in data:
                                politics = data['politics']
                                print(f"    GER politics keys: {list(politics.keys())}")
        
        print(f"\n=== Testing GameEventService ===")
        localizer = HOI4Localizer()
        event_service = GameEventService(localizer)
        
        print("Testing focus event...")
        try:
            focus_event = event_service.get_random_focus_event(game_data, prefer_majors=True)
            if focus_event:
                print(f"✓ Focus event: {focus_event.country_tag} - {focus_event.focus_name}")
                print(f"  Description: {focus_event.focus_description}")
            else:
                print("✗ No focus event returned")
        except Exception as e:
            print(f"✗ Focus event error: {e}")
        
        print("\nTesting political event...")
        try:
            pol_event = event_service.get_random_political_situation(game_data, prefer_majors=True)
            if pol_event:
                print(f"✓ Political event: {pol_event.country_tag} - {pol_event.political_situation}")
            else:
                print("✗ No political event returned")
        except Exception as e:
            print(f"✗ Political event error: {e}")
            
        print("\nTesting world event...")
        try:
            world_event = event_service.get_random_world_situation(game_data)
            if world_event:
                print(f"✓ World event: {world_event.country_tag}")
                print(f"  Context: {world_event.world_context[:200]}...")
            else:
                print("✗ No world event returned")
        except Exception as e:
            print(f"✗ World event error: {e}")
            
    except Exception as e:
        print(f"✗ Error loading game data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()