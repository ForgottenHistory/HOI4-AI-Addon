#!/usr/bin/env python3
"""
Test script to verify environment loading and AI client setup
"""

import os
import sys
from pathlib import Path

# Load environment variables from project root
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')

# Add the src directory to path for imports
sys.path.append(str(project_root / 'src'))

print(f"Project root: {project_root}")
print(f"Environment file exists: {(project_root / '.env').exists()}")
print(f"OPENROUTER_API_KEY loaded: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")

if os.getenv('OPENROUTER_API_KEY'):
    key = os.getenv('OPENROUTER_API_KEY')
    print(f"API Key starts with: {key[:10]}..." if len(key) > 10 else "API Key too short")

try:
    from generators.twitter_generator import TwitterGenerator
    from ai_client import AIClient
    
    print("✅ Successfully imported generators")
    
    # Test AI client creation
    ai_client = AIClient()
    print("✅ Successfully created AI client")
    
    # Test twitter generator
    twitter_gen = TwitterGenerator()
    print("✅ Successfully created Twitter generator")
    
    # Test a simple prompt generation
    test_game_data = {
        'metadata': {
            'date': '1936.01.01',
            'recent_events': []
        },
        'major_powers': []
    }
    
    prompt = twitter_gen.generate_prompt(test_game_data)
    print("✅ Successfully generated test prompt")
    print(f"Prompt length: {len(prompt)} characters")
    
    print("\n🎉 All tests passed! The server should work correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")