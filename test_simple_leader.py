#!/usr/bin/env python3
"""
Simple test for leader persona generation
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
# Add streamer tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'streamer-tools', 'twitter-feed'))

def test_simple_leader():
    """Simple leader test"""
    try:
        from stream_twitter_generator import StreamTwitterGenerator
        
        generator = StreamTwitterGenerator()
        
        # Load real game data with character names
        import json
        game_data_path = os.path.join(os.path.dirname(__file__), 'data', 'game_data.json')
        
        if os.path.exists(game_data_path):
            with open(game_data_path, 'r', encoding='utf-8') as f:
                test_game_data = json.load(f)
            print(f"Loaded real game data with {len(test_game_data.get('countries', []))} countries")
        else:
            # Fallback to simple test data
            test_game_data = {
                'metadata': {'date': '1936.6.1'},
                'countries': [
                    {
                        'tag': 'GER',
                        'data': {
                            'major': True,
                            'politics': {'ruling_party': 'fascism'}
                        }
                    }
                ]
            }
        
        print("Testing leader persona generation...")
        leader_persona = generator._get_leader_persona('GER', test_game_data)
        
        print(f"Generated leader persona: {leader_persona}")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_leader()