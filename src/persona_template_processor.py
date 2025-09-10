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
                    # Recursively process nested dictionaries
                    processed_persona[key] = self._process_nested_dict(value, context)
            else:
                processed_persona[key] = value
        
        return processed_persona
    
    def _process_nested_dict(self, nested_dict: Dict, context: Dict) -> Dict:
        """Recursively process nested dictionaries"""
        processed_dict = {}
        for key, value in nested_dict.items():
            if isinstance(value, str):
                processed_dict[key] = self._process_template_string(value, context)
            elif isinstance(value, list):
                processed_dict[key] = [
                    self._process_template_string(item, context) if isinstance(item, str) else item 
                    for item in value
                ]
            elif isinstance(value, dict):
                if '_conditional' in value:
                    processed_dict[key] = self._process_conditional(value, context)
                else:
                    processed_dict[key] = self._process_nested_dict(value, context)
            else:
                processed_dict[key] = value
        return processed_dict
    
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
        elif placeholder == 'ideological_country_name' and target_country:
            return self._get_ideological_country_name(country_data, target_country)
        
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
        
        # Satirical persona placeholders
        elif placeholder.startswith('peasant_'):
            return self._get_peasant_name_part(placeholder, target_country)
        elif placeholder == 'time_traveler_name':
            return random.choice(['Marcus Future', 'Jenny TimeSkip', 'Bob Chronos', 'Lisa Paradox'])
        elif placeholder == 'tourist_name':
            return random.choice(['Chad Tourism', 'Karen Wanderlost', 'Steve MapQuest', 'Brenda Confusion'])
        elif placeholder == 'philosopher_name':
            return random.choice(['Drunk Socrates', 'Tipsy Plato', 'Wasted Aristotle', 'Hammered Diogenes'])
        elif placeholder == 'operator_name':
            return random.choice(['Old Telegraph Tom', 'Morse Mary', 'Buzzing Bob', 'Clicking Clara'])
        elif placeholder == 'actor_name':
            return random.choice(['Drama Dan', 'Theater Tina', 'Method Mike', 'Stage Sarah'])
        elif placeholder == 'translator_name':
            return random.choice(['Literal Larry', 'Exact Emma', 'Precise Pete', 'Accurate Annie'])
        elif placeholder == 'random_number':
            return str(random.randint(1, 999))
        
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
        """Get the current leader name from game data or generate appropriate title"""
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'democratic')
        
        # Check if we have actual leader data with names
        parties = politics.get('parties', {})
        if ruling_party in parties:
            party_data = parties[ruling_party]
            leaders = party_data.get('country_leader', [])
            if leaders:
                # Get the first leader's name
                leader = leaders[0]
                character = leader.get('character', {})
                character_name = character.get('name')
                
                if character_name:
                    # Convert character name to display name
                    return self._convert_character_name_to_display(character_name, country_tag)
        
        # Fallback: Generate appropriate leader title based on ideology and country
        ideology = ruling_party.lower()
        
        if ideology == 'fascism':
            return f"{self._get_fascist_title(country_tag)}"
        elif ideology == 'communism':
            return f"{self._get_communist_title(country_tag)}"
        elif ideology == 'democratic':
            return f"{self._get_democratic_title(country_tag)}"
        else:
            return f"{self._get_neutral_title(country_tag)}"
    
    def _convert_character_name_to_display(self, character_name: str, country_tag: str) -> str:
        """Convert character name from game data to display name"""
        # Use localization system to get the display name
        if self.localizer:
            localized_name = self.localizer.get_localized_text(character_name)
            if localized_name and localized_name != character_name:
                return localized_name
        
        # Fallback: Clean up the character name for display
        # Remove country prefix and underscores, title case
        if '_' in character_name:
            # Remove country prefix if it exists
            parts = character_name.split('_', 1)
            if len(parts) == 2 and parts[0].upper() == country_tag:
                name_part = parts[1]
            else:
                name_part = character_name
            
            # Replace underscores with spaces and title case
            display_name = name_part.replace('_', ' ').title()
            return display_name
        else:
            # Simple name, just title case
            return character_name.title()
    
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
    
    def _get_ideological_country_name(self, country_data: Dict, target_country: str) -> str:
        """Get ideological country name based on ruling party"""
        if not country_data:
            return self.localizer.get_country_name(target_country)
        
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'democratic').lower()
        base_country = self.localizer.get_country_name(target_country)
        
        # Map ideological names for major countries
        ideological_names = {
            'GER': {
                'fascism': 'German Reich',
                'democratic': 'German Republic',
                'communism': 'German Socialist Republic',
                'neutrality': 'Germany'
            },
            'SOV': {
                'communism': 'Soviet Union',
                'fascism': 'Russian State', 
                'democratic': 'Russian Republic',
                'neutrality': 'Russia'
            },
            'ITA': {
                'fascism': 'Italian Empire',
                'democratic': 'Italian Republic',
                'communism': 'Italian Socialist Republic',
                'neutrality': 'Italy'
            },
            'JAP': {
                'fascism': 'Empire of Japan',
                'democratic': 'Japanese Republic',
                'communism': 'Japanese Socialist Republic',
                'neutrality': 'Japan'
            },
            'ENG': {
                'fascism': 'British Empire',
                'democratic': 'United Kingdom',
                'communism': 'British Socialist Republic',
                'neutrality': 'Britain'
            },
            'FRA': {
                'fascism': 'French State',
                'democratic': 'French Republic',
                'communism': 'French Socialist Republic',
                'neutrality': 'France'
            },
            'USA': {
                'fascism': 'American Reich',
                'democratic': 'United States',
                'communism': 'American Socialist Republic',
                'neutrality': 'United States'
            }
        }
        
        if target_country in ideological_names:
            return ideological_names[target_country].get(ruling_party, base_country)
        
        # Fallback for other countries
        if ruling_party == 'fascism':
            return f"{base_country} Reich"
        elif ruling_party == 'communism':
            return f"{base_country} Socialist Republic"
        elif ruling_party == 'democratic':
            return f"{base_country} Republic"
        else:
            return base_country
    
    def _get_current_focus(self, country_data: Dict, country_tag: str) -> str:
        """Get current national focus"""
        focus_data = country_data.get('focus', {})
        current_focus = focus_data.get('current')
        
        if current_focus:
            # Clean up focus name
            clean_name = current_focus.replace(f"{country_tag.lower()}_", "").replace("_", " ").title()
            return clean_name
        
        return "domestic development"
    
    def _get_peasant_name_part(self, placeholder: str, country_tag: str) -> str:
        """Get peasant name parts based on country"""
        peasant_names = {
            'GER': {'first': ['Hans', 'Fritz', 'Greta', 'Brunhilde'], 'last': ['Müller', 'Schmidt', 'Bauer', 'Kartoffel'], 'handle': ['FarmHans', 'PotatoFritz', 'ChickenGreta']},
            'SOV': {'first': ['Ivan', 'Dimitri', 'Katya', 'Olga'], 'last': ['Petrov', 'Volkov', 'Smirnov', 'Tractor'], 'handle': ['ComradeIvan', 'SovietPlow', 'RedFarmer']},
            'FRA': {'first': ['Pierre', 'Marcel', 'Marie', 'Brigitte'], 'last': ['Dubois', 'Martin', 'Fromage', 'Baguette'], 'handle': ['PierreFarm', 'WinePeasant', 'CheeseMarie']},
            'ENG': {'first': ['William', 'George', 'Mary', 'Elizabeth'], 'last': ['Smith', 'Brown', 'Sheep', 'Pudding'], 'handle': ['TudorWill', 'TeaPeasant', 'RainMary']},
            'ITA': {'first': ['Giuseppe', 'Mario', 'Anna', 'Lucia'], 'last': ['Rossi', 'Bianchi', 'Pasta', 'Vino'], 'handle': ['MarioFarm', 'PastaJoe', 'WineAnna']},
            'USA': {'first': ['Jebediah', 'Cletus', 'Mary-Sue', 'Betty-Lou'], 'last': ['Johnson', 'Williams', 'Cornfield', 'Tractor'], 'handle': ['JebCorn', 'YeeHawCletus', 'FarmMary']},
            'JAP': {'first': ['Hiroshi', 'Takeshi', 'Yuki', 'Sakura'], 'last': ['Tanaka', 'Sato', 'Ricefield', 'Miso'], 'handle': ['RiceHiro', 'FishTake', 'SakuraSake']}
        }
        
        default_names = {
            'first': ['Bob', 'Joe', 'Mary', 'Sue'],
            'last': ['Farmer', 'Field', 'Crop', 'Dirt'],
            'handle': ['SimpleBob', 'FarmJoe', 'FieldMary']
        }
        
        names = peasant_names.get(country_tag, default_names)
        
        if placeholder == 'peasant_first_name':
            return random.choice(names['first'])
        elif placeholder == 'peasant_last_name':
            return random.choice(names['last'])
        elif placeholder == 'peasant_handle':
            return random.choice(names['handle'])
        else:
            return 'SimpleFolk'
    
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
    
    def _process_ideology_conditional(self, conditional: Dict, context: Dict) -> Any:
        """Process ideology-based conditionals"""
        country_data = context.get('country_data')
        if not country_data:
            result = conditional.get('default', '')
        else:
            politics = country_data.get('politics', {})
            ruling_party = politics.get('ruling_party', 'democratic').lower()
            result = conditional.get(ruling_party, conditional.get('default', ''))
        
        # Process template variables in the conditional result
        return self._process_conditional_result(result, context)
    
    def _process_country_conditional(self, conditional: Dict, context: Dict) -> Any:
        """Process country-based conditionals"""
        target_country = context.get('target_country')
        if not target_country:
            result = conditional.get('default', '')
        else:
            result = conditional.get(target_country, conditional.get('default', ''))
        
        # Process template variables in the conditional result
        return self._process_conditional_result(result, context)
    
    def _process_focus_conditional(self, conditional: Dict, context: Dict) -> Any:
        """Process focus-type conditionals"""
        country_data = context.get('country_data')
        if not country_data:
            result = conditional.get('default', '')
        else:
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
            
            result = conditional.get(focus_type, conditional.get('default', ''))
        
        # Process template variables in the conditional result
        return self._process_conditional_result(result, context)
    
    def _process_conditional_result(self, result: Any, context: Dict) -> Any:
        """Process template variables in conditional results"""
        if isinstance(result, str):
            return self._process_template_string(result, context)
        elif isinstance(result, list):
            return [
                self._process_template_string(item, context) if isinstance(item, str) else item 
                for item in result
            ]
        elif isinstance(result, dict):
            if '_conditional' in result:
                return self._process_conditional(result, context)
            else:
                return self._process_nested_dict(result, context)
        else:
            return result