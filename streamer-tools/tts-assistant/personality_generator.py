#!/usr/bin/env python3
"""
TTS Assistant Personality Generator
Generates random personalities for the HOI4 TTS assistant based on player's country
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

@dataclass
class AssistantPersonality:
    """Data structure for assistant personality"""
    name: str
    personality_type: str
    traits: List[str]
    voice_style: str
    backstory: str
    quirks: List[str]
    catchphrases: List[str]
    response_style: str
    country: str

class PersonalityGenerator:
    """Generates random personalities for the TTS assistant based on player country"""
    
    def __init__(self, templates_path: str = None, names_path: str = None):
        if templates_path is None:
            project_root = Path(__file__).parent.parent.parent
            templates_path = project_root / 'data' / 'personas' / 'tts-assistant' / 'personality_templates.json'
        
        if names_path is None:
            project_root = Path(__file__).parent.parent.parent
            names_path = project_root / 'data' / 'personas' / 'tts-assistant' / 'extracted_names.json'
        
        self.templates_path = Path(templates_path)
        self.names_path = Path(names_path)
        self.templates = self._load_templates()
        self.extracted_names = self._load_extracted_names()
    
    def _load_templates(self) -> Dict:
        """Load personality templates from JSON file"""
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading personality templates: {e}")
            # Fallback to basic templates
            return {
                "personality_types": {
                    "confused": {
                        "description": "Never quite understands what's happening",
                        "traits": ["bewildered", "forgetful", "well-meaning"],
                        "voice_style": "slow and uncertain",
                        "catchphrases": ["Wait, what are we doing again?"],
                        "response_style": "Confused and uncertain"
                    }
                },
                "country_data": {
                    "GER": {"names": ["Fritz"], "backgrounds": ["bureaucrat"], "cultural_quirks": ["mentions beer"]}
                }
            }
    
    def _load_extracted_names(self) -> Dict[str, List[str]]:
        """Load extracted names from HOI4 locale files"""
        try:
            with open(self.names_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load extracted names: {e}")
            return {}
    
    def detect_player_country(self) -> str:
        """Detect player country from game data, defaults to Germany"""
        try:
            project_root = Path(__file__).parent.parent.parent
            game_data_path = project_root / 'data' / 'game_data.json'
            
            if game_data_path.exists():
                with open(game_data_path, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                
                # Look for human player or assume major power
                if 'countries' in game_data:
                    # Check for human player flag first
                    for country_tag, country_data in game_data['countries'].items():
                        if country_data.get('is_player', False):
                            return country_tag
                    
                    # Fallback: look for major powers in order of preference
                    major_countries = ['GER', 'SOV', 'USA', 'UK', 'FRA', 'JAP', 'ITA']
                    for country in major_countries:
                        if country in game_data['countries']:
                            return country
            
        except Exception as e:
            print(f"Could not detect player country: {e}")
        
        return 'GER'  # Default fallback
    
    def generate_personality(self, country: str = None) -> AssistantPersonality:
        """Generate a random personality for the assistant"""
        # Detect or use provided country
        if country is None:
            country = self.detect_player_country()
        
        print(f"Generating personality for country: {country}")
        
        # Get personality type and data
        personality_type = random.choice(list(self.templates["personality_types"].keys()))
        personality_data = self.templates["personality_types"][personality_type]
        
        # Get country-specific data
        country_data = self.templates["country_data"].get(country, self.templates["country_data"]["GER"])
        
        # Select random name from country (prefer extracted names, fallback to templates)
        if country in self.extracted_names and self.extracted_names[country]:
            name = random.choice(self.extracted_names[country])
        else:
            name = random.choice(country_data["names"])
        
        # Generate backstory
        backstory = self._generate_backstory(name, personality_type, country_data)
        
        # Select quirks (mix of cultural and universal)
        cultural_quirks = country_data.get("cultural_quirks", [])
        universal_quirks = self.templates.get("universal_quirks", [])
        all_quirks = cultural_quirks + universal_quirks
        
        num_quirks = random.randint(2, 4)
        quirks = random.sample(all_quirks, min(num_quirks, len(all_quirks)))
        
        return AssistantPersonality(
            name=name,
            personality_type=personality_type,
            traits=personality_data["traits"],
            voice_style=personality_data["voice_style"],
            backstory=backstory,
            quirks=quirks,
            catchphrases=personality_data["catchphrases"],
            response_style=personality_data["response_style"],
            country=country
        )
    
    def _generate_backstory(self, name: str, personality_type: str, country_data: Dict) -> str:
        """Generate a backstory for the assistant"""
        background = random.choice(country_data.get("backgrounds", ["bureaucrat"]))
        
        personality_context = {
            "scared": "but is terrified of making mistakes",
            "overeager": "and is thrilled to serve their nation",
            "sarcastic": "who thinks this whole war business is absurd", 
            "confused": "who isn't quite sure how he got this job",
            "dramatic": "who sees himself as a tragic hero",
            "pedantic": "who insists on following every protocol",
            "lazy": "who was hoping for a desk job",
            "superstitious": "who believes fate controls everything"
        }
        
        context = personality_context.get(personality_type, "with his own unique perspective")
        
        return f"{name} is a {background} {context}."
    
def test_personality_generator():
    """Test the personality generator"""
    generator = PersonalityGenerator()
    
    print("=== TTS Assistant Personality Generator Test ===\n")
    
    # Test different countries
    test_countries = ['GER', 'SOV', 'USA', 'UK', 'FRA']
    
    for country in test_countries:
        personality = generator.generate_personality(country)
        
        print(f"Generated Personality for {country}:")
        print(f"Name: {personality.name}")
        print(f"Country: {personality.country}")
        print(f"Type: {personality.personality_type}")
        print(f"Traits: {', '.join(personality.traits)}")
        print(f"Voice Style: {personality.voice_style}")
        print(f"Backstory: {personality.backstory}")
        print(f"Quirks: {', '.join(personality.quirks)}")
        print(f"Response Style: {personality.response_style}")
        print(f"Sample Catchphrases:")
        for phrase in personality.catchphrases[:3]:
            print(f"  - \"{phrase}\"")
        print("-" * 50)
    
    print("\n=== Auto-Detection Test ===")
    auto_personality = generator.generate_personality()  # Let it auto-detect
    print(f"Auto-detected: {auto_personality.name} from {auto_personality.country} ({auto_personality.personality_type})")

if __name__ == '__main__':
    test_personality_generator()