#!/usr/bin/env python3
"""Test script to debug focus description lookups"""

import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

from localization import HOI4Localizer

def test_focus_descriptions():
    """Test focus description lookups"""
    localizer = HOI4Localizer()
    
    # Load localization files
    print("Loading localization files...")
    localizer.load_localization_file("countries_l_english.yml")
    localizer.load_localization_file("focus_l_english.yml")
    localizer.load_localization_file("events_l_english.yml")
    
    # Load additional focus files that might have the descriptions
    import glob
    locale_dir = project_root / 'locale'
    focus_files = glob.glob(str(locale_dir / '*focus*l_english.yml'))
    print(f"Found {len(focus_files)} focus localization files")
    
    for focus_file in focus_files:
        filename = Path(focus_file).name
        if filename != "focus_l_english.yml":  # Already loaded
            print(f"Loading additional file: {filename}")
            localizer.load_localization_file(filename)
    
    # Test some common focus IDs
    test_focuses = [
        "ger_fuhrerprinzip",
        "jap_small_arms_modernization", 
        "sov_gain_support_from_party_members",
        "usa_war_department"
    ]
    
    for focus_id in test_focuses:
        print(f"\n=== Testing focus: {focus_id} ===")
        
        # Test both lowercase and uppercase versions
        for test_id in [focus_id, focus_id.upper()]:
            print(f"\n--- Testing variant: {test_id} ---")
            
            # Test focus name
            focus_name = localizer.get_localized_text(test_id)
            print(f"Focus name: {focus_name}")
            
            # Test focus description
            desc_key = f"{test_id}_desc"
            description = localizer.get_localized_text(desc_key)
            print(f"Description key: {desc_key}")
            print(f"Description: {description}")
            
            # Check if description is the same as key (not found)
            if description == desc_key:
                print("❌ Description not found")
            else:
                print("✅ Description found")
                if len(description) > 50:
                    print(f"Preview: {description[:200]}...")
                break  # Found it, don't test other case
            
    # Test the exact keys we found in grep results
    print("\n=== Testing exact keys from grep ===")
    exact_keys = [
        "GER_fuhrerprinzip_desc",  # This one we know exists
        "GER_fuhrerprinzip"
    ]
    
    for key in exact_keys:
        result = localizer.get_localized_text(key)
        print(f"{key}: {result}")
        if result != key:
            print(f"  ✅ Found: {result}")
        else:
            print(f"  ❌ Not found")
    
    # Test with some raw keys we've seen
    print("\n=== Testing raw keys from logs ===")
    raw_keys = [
        "ger_fuhrerprinzip_desc",
        "jap_small_arms_modernization_desc",
        "sov_gain_support_from_party_members_desc"
    ]
    
    for key in raw_keys:
        result = localizer.get_localized_text(key)
        print(f"{key}: {result}")
        if result != key:
            print(f"  ✅ Found: {result}")
        else:
            print(f"  ❌ Not found")

if __name__ == '__main__':
    test_focus_descriptions()