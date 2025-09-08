#!/usr/bin/env python3
"""
Debug event localization issues
"""

import json
from localization import HOI4Localizer

def main():
    # Load the game data
    with open('game_data.json', 'r') as f:
        data = json.load(f)
    
    localizer = HOI4Localizer()
    localizer.load_all_files()
    
    print("=== EVENT LOCALIZATION DEBUG ===")
    print(f"Total translations loaded: {len(localizer.translations)}")
    
    # Get the raw events from the data
    raw_events = data['events'][:10]  # First 10 events
    
    print(f"\nDebugging first 10 events:")
    for i, event_id in enumerate(raw_events, 1):
        print(f"\n{i}. Raw event ID: {event_id}")
        
        # Try different localization patterns
        patterns_to_try = [
            event_id,                    # Direct match
            f"{event_id}.t",            # Title
            f"{event_id}.d",            # Description  
            f"{event_id}.title",        # Alternative title
            f"{event_id}.desc",         # Alternative description
            event_id.replace('_', '.'), # Different separator
        ]
        
        found_match = False
        for pattern in patterns_to_try:
            if pattern in localizer.translations:
                print(f"  ✓ {pattern} → {localizer.translations[pattern]}")
                found_match = True
                break
        
        if not found_match:
            print(f"  ✗ No localization found")
            
            # Search for any keys containing parts of the event ID
            event_parts = event_id.split('.')
            if len(event_parts) > 0:
                base_name = event_parts[0]
                print(f"  Searching for keys containing '{base_name}':")
                
                matches = []
                for key, value in localizer.translations.items():
                    if base_name.lower() in key.lower():
                        matches.append((key, value))
                
                # Show first 5 matches
                for key, value in matches[:5]:
                    print(f"    {key} → {value[:100]}...")
                
                if len(matches) > 5:
                    print(f"    ... and {len(matches) - 5} more matches")

if __name__ == "__main__":
    main()