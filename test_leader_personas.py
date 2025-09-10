#!/usr/bin/env python3
"""
Test Leader Persona Generation
Check if country leaders can be generated and why they might not appear
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
# Add streamer tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'streamer-tools', 'twitter-feed'))

def test_leader_persona_availability():
    """Test if leader personas are loaded and available"""
    print("Testing Leader Persona Availability")
    print("-" * 40)
    
    try:
        from stream_twitter_generator import StreamTwitterGenerator
        
        generator = StreamTwitterGenerator()
        
        # Check if leader personas are loaded
        leader_personas = [p for p in generator.persona_loader.personas.values() 
                          if 'leader' in p.get('id', '').lower()]
        
        print(f"Total personas loaded: {len(generator.persona_loader.personas)}")
        print(f"Leader personas found: {len(leader_personas)}")
        
        for persona in leader_personas:
            print(f"  - {persona.get('id', 'unknown')}: {persona.get('name', 'unnamed')}")
        
        # Test specific leader persona lookup
        leader_persona = generator.persona_loader.get_persona('country_leader_official')
        if leader_persona:
            print(f"\nDirect lookup successful: {leader_persona['id']}")
        else:
            print("\nERROR: country_leader_official not found!")
        
        return len(leader_personas) > 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_leader_persona_generation():
    """Test actual leader persona generation with game data"""
    print("\nTesting Leader Persona Generation")
    print("-" * 40)
    
    try:
        from stream_twitter_generator import StreamTwitterGenerator
        
        generator = StreamTwitterGenerator()
        
        # Test game data
        test_game_data = {
            'metadata': {'date': '1936.6.1'},
            'countries': [
                {
                    'tag': 'GER',
                    'data': {
                        'major': True,
                        'politics': {'ruling_party': 'fascism'},
                        'stability': 0.75,
                        'war_support': 0.60
                    }
                },
                {
                    'tag': 'SOV',
                    'data': {
                        'major': True,
                        'politics': {'ruling_party': 'communism'},
                        'stability': 0.45,
                        'war_support': 0.70
                    }
                }
            ]
        }
        
        print("Testing forced leader persona generation:")
        
        # Test forcing a leader persona (like the server does)
        leader_persona_ger = generator._get_leader_persona('GER', test_game_data)
        leader_persona_sov = generator._get_leader_persona('SOV', test_game_data)
        
        print(f"\nGerman leader persona:")
        print(f"  Name: {leader_persona_ger.get('name', 'unknown')}")
        print(f"  Handle: {leader_persona_ger.get('handle', 'unknown')}")
        print(f"  Description: {leader_persona_ger.get('description', 'unknown')}")
        
        print(f"\nSoviet leader persona:")
        print(f"  Name: {leader_persona_sov.get('name', 'unknown')}")
        print(f"  Handle: {leader_persona_sov.get('handle', 'unknown')}")
        print(f"  Description: {leader_persona_sov.get('description', 'unknown')}")
        
        # Check if they have unprocessed templates
        templates_in_ger = '{{' in str(leader_persona_ger)
        templates_in_sov = '{{' in str(leader_persona_sov)
        
        print(f"\nTemplate processing:")
        print(f"  German leader has templates: {templates_in_ger}")
        print(f"  Soviet leader has templates: {templates_in_sov}")
        
        return not templates_in_ger and not templates_in_sov
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_random_persona_selection():
    """Test what personas are typically selected in normal operation"""
    print("\nTesting Random Persona Selection (10 trials)")
    print("-" * 50)
    
    try:
        from stream_twitter_generator import StreamTwitterGenerator
        
        generator = StreamTwitterGenerator()
        
        test_game_data = {
            'metadata': {'date': '1936.6.1'},
            'countries': [
                {
                    'tag': 'FRA',
                    'data': {
                        'major': True,
                        'politics': {'ruling_party': 'democratic'},
                        'stability': 0.65,
                        'war_support': 0.45
                    }
                }
            ]
        }
        
        # Test different event types
        event_types = ['politics', 'war', 'crisis', 'focus_ongoing', 'general']
        
        for event_type in event_types:
            print(f"\nEvent type: {event_type}")
            leader_count = 0
            official_count = 0
            journalist_count = 0
            other_count = 0
            
            for i in range(10):
                persona = generator.persona_loader.get_random_persona(
                    event_type=event_type,
                    country='FRA',
                    game_data=test_game_data
                )
                
                persona_id = persona.get('id', '')
                if 'leader' in persona_id.lower():
                    leader_count += 1
                elif 'minister' in persona_id.lower() or 'government' in persona_id.lower():
                    official_count += 1
                elif 'journalist' in persona_id.lower() or 'correspondent' in persona_id.lower():
                    journalist_count += 1
                else:
                    other_count += 1
            
            print(f"  Leaders: {leader_count}/10, Officials: {official_count}/10, Journalists: {journalist_count}/10, Other: {other_count}/10")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run leader persona tests"""
    try:
        print("LEADER PERSONA INVESTIGATION")
        print("=" * 50)
        
        availability_success = test_leader_persona_availability()
        generation_success = test_leader_persona_generation()
        selection_success = test_random_persona_selection()
        
        overall_success = availability_success and generation_success and selection_success
        
        print("\n" + "=" * 50)
        print("LEADER PERSONA TEST RESULTS:")
        print("=" * 50)
        
        print(f"{'PASS' if availability_success else 'FAIL'}: Leader personas available")
        print(f"{'PASS' if generation_success else 'FAIL'}: Leader persona generation works")
        print(f"{'PASS' if selection_success else 'FAIL'}: Random selection testing completed")
        
        if overall_success:
            print("\nLEADER PERSONA DIAGNOSIS:")
            print("- Leader personas ARE available in the system")
            print("- Leader persona generation works correctly")
            print("- They may just be selected rarely in normal operation")
            print("- Only 'leader_speech' events force leader selection")
            print("- Most events use random selection (journalists, officials, etc.)")
        else:
            print("\nISSUES FOUND - leader personas may not be working properly")
            
        return overall_success
        
    except Exception as e:
        print(f"CRITICAL FAILURE: Leader persona testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)