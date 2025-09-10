#!/usr/bin/env python3
"""
Configuration Test Script
Run this to test your configuration settings
"""

import json
from config_loader import ConfigLoader, get_config

def test_configuration():
    """Test current configuration"""
    print("[CONFIG] Twitter Stream Tool Configuration Test")
    print("=" * 50)
    
    # Load configuration
    config = get_config()
    
    # Test basic loading
    print("[OK] Configuration loaded successfully")
    
    # Test specific values
    test_cases = [
        ("Auto Generation Interval", "stream_settings.auto_generation_interval", "seconds"),
        ("Citizen Boost Chance", "persona_selection.citizen_boost_chance", "%", lambda x: f"{x*100:.1f}%"),
        ("Journalist Avoid Chance", "persona_selection.journalist_avoid_chance", "%", lambda x: f"{x*100:.1f}%"),
        ("Leader Selection Chance", "persona_selection.leader_selection_chance", "%", lambda x: f"{x*100:.1f}%"),
        ("AI Model", "ai_generation.model_name", ""),
        ("Max Tokens", "ai_generation.max_tokens", "tokens"),
        ("Temperature", "ai_generation.temperature", ""),
        ("Debug Mode", "stream_settings.debug_mode", "")
    ]
    
    print("\n[VALUES] Configuration Values:")
    print("-" * 30)
    
    for name, key, unit, *formatter in test_cases:
        value = config.get(key)
        if formatter:
            display_value = formatter[0](value)
        else:
            display_value = f"{value} {unit}".strip()
        
        print(f"{name:<25}: {display_value}")
    
    # Test satirical settings
    satirical_enabled = []
    satirical_settings = config.get_section('satirical_settings')
    for key, enabled in satirical_settings.items():
        if enabled and key.endswith('_enabled'):
            persona_type = key.replace('_enabled', '').replace('_', ' ').title()
            satirical_enabled.append(persona_type)
    
    print(f"\n[SATIRICAL] Satirical Personas Enabled: {len(satirical_enabled)}")
    for persona in satirical_enabled:
        print(f"  • {persona}")
    
    # Test paths
    print(f"\n[PATHS] File Paths:")
    paths = config.get_section('paths')
    for key, path in paths.items():
        print(f"  {key}: {path}")
    
    # Validate JSON structure
    try:
        config_dict = config._config
        json.dumps(config_dict, indent=2)
        print(f"\n[OK] JSON structure is valid")
    except Exception as e:
        print(f"\n[ERROR] JSON validation error: {e}")
        return False
    
    # Test convenience functions
    print(f"\n[FUNCTIONS] Convenience Functions Test:")
    try:
        from config_loader import get_auto_interval, get_citizen_boost, get_journalist_avoid
        print(f"  Auto interval: {get_auto_interval()}s")
        print(f"  Citizen boost: {get_citizen_boost()*100:.1f}%") 
        print(f"  Journalist avoid: {get_journalist_avoid()*100:.1f}%")
        print("[OK] All convenience functions working")
    except Exception as e:
        print(f"[ERROR] Convenience function error: {e}")
        return False
    
    print(f"\n[RESULTS] Configuration Test Results:")
    print("[OK] Configuration is valid and ready to use!")
    print("   Restart the server to apply any changes.")
    
    return True

def show_sample_configs():
    """Show some sample configurations"""
    print(f"\n[SAMPLES] Sample Configuration Snippets:")
    print("=" * 40)
    
    samples = {
        "Comedy Mode": {
            "persona_selection": {
                "citizen_boost_chance": 0.4,
                "journalist_avoid_chance": 0.9,
                "satirical_persona_chance": 0.3
            },
            "satirical_settings": {
                "peasant_personas_enabled": True,
                "time_traveler_enabled": True,
                "drunk_philosopher_enabled": True
            }
        },
        "Leader Focus": {
            "persona_selection": {
                "leader_selection_chance": 0.8,
                "official_selection_chance": 0.6,
                "journalist_avoid_chance": 0.85
            }
        },
        "Fast Testing": {
            "stream_settings": {
                "auto_generation_interval": 5,
                "debug_mode": True
            }
        }
    }
    
    for name, sample in samples.items():
        print(f"\n[CONFIG] {name}:")
        print(json.dumps(sample, indent=2))

if __name__ == "__main__":
    success = test_configuration()
    
    if success:
        show_sample_configs()
        
        print(f"\n[TIPS] Tips:")
        print("  • Edit config.json to customize behavior")
        print("  • Run this script after making changes to test")
        print("  • Check CONFIG_GUIDE.md for detailed documentation")
        print("  • Restart the server after configuration changes")
    
    exit(0 if success else 1)