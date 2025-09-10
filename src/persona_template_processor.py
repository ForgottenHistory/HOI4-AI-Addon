#!/usr/bin/env python3
"""
Persona Template Processor
Processes persona templates with dynamic game data to create context-appropriate characters
"""

import re
import random
from typing import Dict, List, Any, Optional
from localization import HOI4Localizer

class PersonaTemplateProcessor:
    """Processes persona templates with current game state"""
    
    def __init__(self, localizer: HOI4Localizer = None):
        self.localizer = localizer or HOI4Localizer()
    
    def process_persona_template(self, template: Dict, game_data: Dict, target_country: str = None) -> Dict:
        """Process a persona template with current game data to create a dynamic persona"""
        
        # Get country data if target country is specified
        country_data = self._get_country_data(game_data, target_country) if target_country else None
        
        # Create context for template processing
        context = {
            'game_data': game_data,
            'country_data': country_data,
            'target_country': target_country,
            'date': game_data.get('metadata', {}).get('date', '1936.01.01'),
            'year': game_data.get('metadata', {}).get('date', '1936.01.01')[:4]
        }
        
        # Process each field in the template
        processed_persona = {}
        for key, value in template.items():
            if isinstance(value, str):
                processed_persona[key] = self._process_template_string(value, context)
            elif isinstance(value, list):
                processed_persona[key] = [
                    self._process_template_string(item, context) if isinstance(item, str) else item 
                    for item in value
                ]
            elif isinstance(value, dict):
                # Handle conditional templates
                if '_conditional' in value:
                    processed_persona[key] = self._process_conditional(value, context)
                else:
                    processed_persona[key] = value
            else:
                processed_persona[key] = value
        
        return processed_persona
    
    def _process_template_string(self, template_str: str, context: Dict) -> str:
        """Process a template string with placeholders"""
        
        # Handle different types of placeholders
        result = template_str
        
        # Process {{variable}} placeholders
        result = self._process_variable_placeholders(result, context)
        
        # Process {option1|option2|option3} choice placeholders  
        result = self._process_choice_placeholders(result)
        
        # Process [conditional:condition] placeholders
        result = self._process_conditional_placeholders(result, context)
        
        return result
    
    def _process_variable_placeholders(self, text: str, context: Dict) -> str:
        """Process {{variable}} style placeholders"""
        
        def replace_placeholder(match):
            placeholder = match.group(1)
            return self._resolve_placeholder(placeholder, context)
        
        return re.sub(r'{{([^}]+)}}', replace_placeholder, text)
    
    def _process_choice_placeholders(self, text: str) -> str:
        """Process {option1|option2|option3} style placeholders"""
        
        def replace_choice(match):
            choices = match.group(1).split('|')
            return random.choice(choices).strip()
        
        return re.sub(r'{([^}]+\|[^}]*)}', replace_choice, text)
    
    def _process_conditional_placeholders(self, text: str, context: Dict) -> str:
        """Process [conditional:condition] style placeholders"""
        
        def replace_conditional(match):
            condition = match.group(1)
            return self._evaluate_condition(condition, context)
        
        return re.sub(r'\[([^\]]+)\]', replace_conditional, text)
    
    def _evaluate_condition(self, condition: str, context: Dict) -> str:
        """Evaluate a conditional expression - for now just return empty string"""
        # This was for a future feature, for now just return empty
        return ""
    
    def _resolve_placeholder(self, placeholder: str, context: Dict) -> str:
        """Resolve a specific placeholder with game data"""
        
        country_data = context.get('country_data')
        target_country = context.get('target_country')
        game_data = context.get('game_data')
        
        # Country-specific placeholders
        if placeholder == 'country_name' and target_country:
            return self.localizer.get_country_name(target_country)
        elif placeholder == 'country_tag' and target_country:
            return target_country
        elif placeholder == 'country_adjective' and target_country:
            return self._get_country_adjective(target_country)
        
        # Leader placeholders
        elif placeholder == 'current_leader' and country_data:
            return self._get_current_leader(country_data, target_country)
        elif placeholder == 'leader_title' and country_data:
            return self._get_leader_title(country_data, target_country)
        
        # Ideology placeholders
        elif placeholder == 'ruling_ideology' and country_data:
            return self._get_ruling_ideology(country_data)
        elif placeholder == 'ideology_adjective' and country_data:
            return self._get_ideology_adjective(country_data)
        
        # Date placeholders
        elif placeholder == 'current_date':
            return context.get('date', '1936.01.01')
        elif placeholder == 'current_year':
            return context.get('year', '1936')
        
        # Focus placeholders
        elif placeholder == 'current_focus' and country_data:
            return self._get_current_focus(country_data, target_country)
        
        # Fallback - provide reasonable defaults for missing placeholders
        if placeholder == 'country_name':
            return "International"
        elif placeholder == 'country_tag':
            return "INT"
        elif placeholder == 'country_adjective':
            return "International"
        elif placeholder == 'current_leader':
            return "Official"
        elif placeholder == 'leader_title':
            return "Leader"
        elif placeholder == 'ruling_ideology':
            return "General"
        elif placeholder == 'ideology_adjective':
            return "general"
        elif placeholder == 'current_focus':
            return "domestic policy"
        else:
            return f"[{placeholder}]"
    
    def _get_country_data(self, game_data: Dict, country_tag: str) -> Optional[Dict]:
        """Get country data from game data"""
        if 'countries' not in game_data:
            return None
        
        for country in game_data['countries']:
            if country.get('tag') == country_tag:
                return country.get('data', {})
        
        return None
    
    def _get_current_leader(self, country_data: Dict, country_tag: str) -> str:
        """Get the current leader name or generate appropriate title"""
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'democratic')
        
        # Check if we have leader data
        parties = politics.get('parties', {})
        if ruling_party in parties:
            party_data = parties[ruling_party]
            leaders = party_data.get('country_leader', [])
            if leaders:
                # For now, use generic titles - in future could extract actual leader names
                pass
        
        # Generate appropriate leader title based on ideology and country
        ideology = ruling_party.lower()
        
        if ideology == 'fascism':
            return f"{self._get_fascist_title(country_tag)}"
        elif ideology == 'communism':
            return f"{self._get_communist_title(country_tag)}"
        elif ideology == 'democratic':
            return f"{self._get_democratic_title(country_tag)}"
        else:
            return f"{self._get_neutral_title(country_tag)}"
    
    def _get_leader_title(self, country_data: Dict, country_tag: str) -> str:
        """Get appropriate leader title"""
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'democratic')
        ideology = ruling_party.lower()
        
        if ideology == 'fascism':
            return random.choice(['Führer', 'Leader', 'Chief', 'Supreme Leader'])
        elif ideology == 'communism':
            return random.choice(['General Secretary', 'Chairman', 'Premier', 'Comrade Leader'])
        elif ideology == 'democratic':
            return random.choice(['President', 'Prime Minister', 'Chancellor', 'Premier'])
        else:
            return random.choice(['Leader', 'Head of State', 'Chief', 'Premier'])
    
    def _get_ruling_ideology(self, country_data: Dict) -> str:
        """Get the ruling ideology name"""
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'democratic')
        
        ideology_names = {
            'fascism': 'Fascist',
            'communism': 'Communist', 
            'democratic': 'Democratic',
            'neutrality': 'Neutral'
        }
        
        return ideology_names.get(ruling_party.lower(), 'Democratic')
    
    def _get_ideology_adjective(self, country_data: Dict) -> str:
        """Get adjective form of ideology"""
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'democratic')
        
        adjectives = {
            'fascism': random.choice(['fascist', 'nationalist', 'authoritarian']),
            'communism': random.choice(['communist', 'socialist', 'revolutionary']),
            'democratic': random.choice(['democratic', 'parliamentary', 'constitutional']),
            'neutrality': random.choice(['neutral', 'independent', 'non-aligned'])
        }
        
        return adjectives.get(ruling_party.lower(), 'democratic')
    
    def _get_country_adjective(self, country_tag: str) -> str:
        """Get adjective form of country name"""
        adjectives = {
            'GER': 'German', 'USA': 'American', 'SOV': 'Soviet', 'ENG': 'British',
            'FRA': 'French', 'ITA': 'Italian', 'JAP': 'Japanese', 'POL': 'Polish',
            'SPA': 'Spanish', 'POR': 'Portuguese', 'HOL': 'Dutch', 'BEL': 'Belgian',
            'SWI': 'Swiss', 'AUS': 'Austrian', 'CZE': 'Czechoslovak', 'HUN': 'Hungarian',
            'ROM': 'Romanian', 'YUG': 'Yugoslav', 'BUL': 'Bulgarian', 'GRE': 'Greek',
            'TUR': 'Turkish', 'CHI': 'Chinese', 'MAN': 'Manchurian', 'SIA': 'Siamese',
            'RAJ': 'Indian', 'CAN': 'Canadian', 'AST': 'Australian', 'SAF': 'South African'
        }
        
        return adjectives.get(country_tag, f"{country_tag}n")
    
    def _get_current_focus(self, country_data: Dict, country_tag: str) -> str:
        """Get current national focus"""
        focus_data = country_data.get('focus', {})
        current_focus = focus_data.get('current')
        
        if current_focus:
            # Clean up focus name
            clean_name = current_focus.replace(f"{country_tag.lower()}_", "").replace("_", " ").title()
            return clean_name
        
        return "domestic development"
    
    def _get_fascist_title(self, country_tag: str) -> str:
        """Get appropriate fascist leader title for country"""
        if country_tag == 'GER':
            return 'The Führer'
        elif country_tag == 'ITA':
            return 'Il Duce'
        elif country_tag == 'SPA':
            return 'El Caudillo'
        else:
            return 'The Leader'
    
    def _get_communist_title(self, country_tag: str) -> str:
        """Get appropriate communist leader title for country"""
        if country_tag == 'SOV':
            return 'The General Secretary'
        elif country_tag == 'CHI':
            return 'Chairman Mao'
        else:
            return 'Comrade Leader'
    
    def _get_democratic_title(self, country_tag: str) -> str:
        """Get appropriate democratic leader title for country"""
        if country_tag == 'USA':
            return 'The President'
        elif country_tag in ['ENG', 'CAN', 'AST']:
            return 'The Prime Minister'
        elif country_tag in ['GER', 'AUS']:
            return 'The Chancellor'
        else:
            return 'The President'
    
    def _get_neutral_title(self, country_tag: str) -> str:
        """Get appropriate neutral leader title for country"""
        return 'The Head of State'
    
    def _process_conditional(self, conditional_dict: Dict, context: Dict) -> Any:
        """Process conditional template logic"""
        condition_type = conditional_dict.get('_conditional')
        
        if condition_type == 'ideology':
            return self._process_ideology_conditional(conditional_dict, context)
        elif condition_type == 'country':
            return self._process_country_conditional(conditional_dict, context)
        elif condition_type == 'focus_type':
            return self._process_focus_conditional(conditional_dict, context)
        
        return conditional_dict.get('default', '')
    
    def _process_ideology_conditional(self, conditional: Dict, context: Dict) -> str:
        """Process ideology-based conditionals"""
        country_data = context.get('country_data')
        if not country_data:
            return conditional.get('default', '')
        
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'democratic').lower()
        
        return conditional.get(ruling_party, conditional.get('default', ''))
    
    def _process_country_conditional(self, conditional: Dict, context: Dict) -> str:
        """Process country-based conditionals"""
        target_country = context.get('target_country')
        if not target_country:
            return conditional.get('default', '')
        
        return conditional.get(target_country, conditional.get('default', ''))
    
    def _process_focus_conditional(self, conditional: Dict, context: Dict) -> str:
        """Process focus-type conditionals"""
        country_data = context.get('country_data')
        if not country_data:
            return conditional.get('default', '')
        
        focus_data = country_data.get('focus', {})
        current_focus = focus_data.get('current', '').lower()
        
        # Categorize focus type
        if any(keyword in current_focus for keyword in ['army', 'military', 'war', 'rearm']):
            focus_type = 'military'
        elif any(keyword in current_focus for keyword in ['industry', 'production', 'economy']):
            focus_type = 'economic'
        elif any(keyword in current_focus for keyword in ['political', 'ideology', 'party']):
            focus_type = 'political'
        elif any(keyword in current_focus for keyword in ['diplomatic', 'alliance', 'foreign']):
            focus_type = 'diplomatic'
        else:
            focus_type = 'general'
        
        return conditional.get(focus_type, conditional.get('default', ''))