#!/usr/bin/env python3
"""Test the final fix for focus descriptions"""

import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

from auto_tweet_generator import AutoTweetGenerator

def test_final_fix():
    """Test the fixed focus description method"""
    print("Testing final focus description fix...")
    
    # Create generator (will load all focus files)
    generator = AutoTweetGenerator()
    
    # Test problematic focus IDs we've seen
    test_cases = [
        ("ger_fuhrerprinzip", "GER"),
        ("jap_small_arms_modernization", "JAP"), 
        ("sov_gain_support_from_party_members", "SOV"),
        ("usa_war_department", "USA")
    ]
    
    for focus_id, country_tag in test_cases:
        print(f"\n=== Testing {focus_id} for {country_tag} ===")
        
        # Test the specific variations manually
        variations = [
            focus_id,  
            focus_id.upper(),  
            f"{country_tag.upper()}_{focus_id.split('_', 1)[1] if '_' in focus_id else focus_id}"
        ]
        
        print(f"Variations to try: {variations}")
        
        for variant in variations:
            desc_key = f"{variant}_desc"
            result = generator.localizer.get_localized_text(desc_key)
            print(f"  {desc_key}: {result[:100]}..." if len(result) > 100 else f"  {desc_key}: {result}")
            
            if result != desc_key and len(result) > 50:
                print(f"  ✅ Found real description!")
                break
        
        description = generator._get_focus_description(focus_id, country_tag)
        print(f"Final result: {description}")
        
        # Check if it's a placeholder or real description
        if "Desc" in description and len(description) < 50:
            print("❌ Still getting placeholder")
        elif len(description) > 50:
            print("✅ Got real description!")
        else:
            print("⚠️  Got fallback name")

if __name__ == '__main__':
    test_final_fix()