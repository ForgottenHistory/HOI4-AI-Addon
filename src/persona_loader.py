#!/usr/bin/env python3
"""
Generic Persona Loader System
Loads personality definitions from data/personas/ directory
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from persona_template_processor import PersonaTemplateProcessor

class PersonaLoader:
    """Loads and manages persona definitions from JSON files"""
    
    def __init__(self, personas_dir: str = None, localizer=None):
        """Initialize persona loader with directory path"""
        if personas_dir is None:
            # Default to data/personas relative to project root
            project_root = Path(__file__).parent.parent
            personas_dir = project_root / "data" / "personas"
        
        self.personas_dir = Path(personas_dir)
        self.personas = {}
        self.categories = {}
        self.template_processor = PersonaTemplateProcessor(localizer)
        self.load_personas()
    
    def load_personas(self):
        """Load all persona files from the personas directory"""
        if not self.personas_dir.exists():
            print(f"Personas directory not found: {self.personas_dir}")
            return
        
        # Load all JSON files in personas directory
        for persona_file in self.personas_dir.glob("*.json"):
            try:
                with open(persona_file, 'r', encoding='utf-8') as f:
                    persona_data = json.load(f)
                    self._process_persona_file(persona_data, persona_file.stem)
            except Exception as e:
                print(f"Error loading persona file {persona_file}: {e}")
    
    def _process_persona_file(self, persona_data: Dict, filename: str):
        """Process a single persona file and organize personas by category"""
        if "personas" in persona_data:
            # File contains multiple personas
            for persona in persona_data["personas"]:
                self._add_persona(persona, filename)
        else:
            # File is a single persona
            self._add_persona(persona_data, filename)
    
    def _add_persona(self, persona: Dict, source_file: str):
        """Add a single persona to the collection"""
        persona_id = persona.get("id", f"{source_file}_{len(self.personas)}")
        persona["source_file"] = source_file
        
        # Add to main collection
        self.personas[persona_id] = persona
        
        # Organize by categories
        categories = persona.get("categories", ["general"])
        if isinstance(categories, str):
            categories = [categories]
        
        for category in categories:
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(persona_id)
    
    def get_persona(self, persona_id: str) -> Optional[Dict]:
        """Get a specific persona by ID"""
        return self.personas.get(persona_id)
    
    def get_personas_by_category(self, category: str) -> List[Dict]:
        """Get all personas in a specific category"""
        if category not in self.categories:
            return []
        
        return [self.personas[pid] for pid in self.categories[category]]
    
    def get_random_persona(self, category: str = None, event_type: str = None, country: str = None, game_data: Dict = None) -> Dict:
        """Get a random persona, optionally filtered by category, event type, or country"""
        candidates = []
        
        if category:
            candidates = self.get_personas_by_category(category)
        else:
            candidates = list(self.personas.values())
        
        # Filter by event type if specified
        if event_type and candidates:
            filtered = []
            for persona in candidates:
                suitable_events = persona.get("suitable_for_events", [])
                if not suitable_events or event_type in suitable_events:
                    filtered.append(persona)
            if filtered:
                candidates = filtered
        
        # Filter by country if specified - prioritize country-specific personas
        if country and candidates:
            # First try to find country-specific personas
            country_specific = []
            international_fallbacks = []
            
            for persona in candidates:
                countries = persona.get("countries", [])
                if country in countries:
                    country_specific.append(persona)
                elif not countries or "any" in countries:
                    international_fallbacks.append(persona)
            
            # Prefer country-specific personas, but allow international as fallback
            if country_specific:
                # 70% chance for country-specific, 30% for international
                if random.random() < 0.7:
                    candidates = country_specific
                else:
                    candidates = country_specific + international_fallbacks
            elif international_fallbacks:
                candidates = international_fallbacks
        
        if not candidates:
            return self._get_fallback_persona(game_data, country)
        
        # If we have a target country, try to create country-specific personas
        if country and game_data:
            # Higher chance for leaders on political events
            leader_boost = 0.6 if event_type in ['politics', 'war', 'crisis'] else 0.4
            
            # Try to generate a country-specific persona from templates
            if random.random() < leader_boost:
                country_templates = [p for p in self.personas.values() 
                                   if self._is_template(p) and self._is_country_template(p)]
                
                # If it's a political event, prefer leader templates
                if event_type in ['politics', 'war', 'crisis'] and country_templates:
                    leader_templates = [p for p in country_templates if 'leader' in p.get('id', '').lower()]
                    if leader_templates and random.random() < 0.5:  # 50% chance for leader on political events
                        selected_template = random.choice(leader_templates)
                        return self.template_processor.process_persona_template(selected_template, game_data, country)
                
                # Otherwise pick any country template
                if country_templates:
                    selected_template = random.choice(country_templates)
                    return self.template_processor.process_persona_template(selected_template, game_data, country)
        
        selected_template = random.choice(candidates)
        
        # If we have game data and a target country, process the template
        if game_data and country and self._is_template(selected_template):
            return self.template_processor.process_persona_template(selected_template, game_data, country)
        elif game_data and self._is_template(selected_template):
            # For international personas, process with game data but no specific country
            return self.template_processor.process_persona_template(selected_template, game_data)
        else:
            # Return template as-is for static personas
            return selected_template
    
    def get_templated_persona(self, persona_id: str, game_data: Dict, target_country: str = None) -> Dict:
        """Get a specific persona processed as a template with game data"""
        template = self.get_persona(persona_id)
        if not template:
            return self._get_fallback_persona(game_data, target_country)
        
        if self._is_template(template):
            return self.template_processor.process_persona_template(template, game_data, target_country)
        else:
            return template
    
    def _is_template(self, persona: Dict) -> bool:
        """Check if a persona contains template placeholders"""
        persona_str = str(persona)
        return '{{' in persona_str or '{' in persona_str and '|' in persona_str
    
    def _is_country_template(self, persona: Dict) -> bool:
        """Check if a persona is designed for country-specific use"""
        persona_str = str(persona)
        # Look for country-specific placeholders
        country_placeholders = ['{{country_name}}', '{{country_tag}}', '{{country_adjective}}', 
                              '{{current_leader}}', '{{ruling_ideology}}', '{{ideology_adjective}}']
        return any(placeholder in persona_str for placeholder in country_placeholders)
    
    def get_categories(self) -> List[str]:
        """Get list of all available categories"""
        return list(self.categories.keys())
    
    def get_persona_count(self) -> int:
        """Get total number of loaded personas"""
        return len(self.personas)
    
    def _get_fallback_persona(self, game_data: Dict = None, country: str = None) -> Dict:
        """Return a basic fallback persona if no suitable persona is found"""
        if game_data and country:
            # Create a dynamic fallback for a specific country
            country_name = self.template_processor.localizer.get_country_name(country) if self.template_processor.localizer else country
            return {
                "id": f"fallback_{country.lower()}",
                "name": f"{country_name} Observer",
                "handle": f"@{country}Watch",
                "avatar_type": "journalist",
                "country": country,
                "description": f"Observer reporting on {country_name}",
                "writing_style": "neutral",
                "categories": ["general"],
                "suitable_for_events": [],
                "countries": [country]
            }
        else:
            # Generic international fallback
            return {
                "id": "fallback_observer",
                "name": "International Observer",
                "handle": "@WorldWatch1936",
                "avatar_type": "journalist",
                "country": None,
                "description": "Generic international observer",
                "writing_style": "neutral",
                "categories": ["general"],
                "suitable_for_events": [],
                "countries": ["any"]
            }
    
    def reload_personas(self):
        """Reload all persona files (useful for development)"""
        self.personas.clear()
        self.categories.clear()
        self.load_personas()
    
    def get_persona_info(self) -> Dict:
        """Get summary information about loaded personas"""
        return {
            "total_personas": len(self.personas),
            "categories": {cat: len(personas) for cat, personas in self.categories.items()},
            "personas_by_file": {}
        }