#!/usr/bin/env python3
"""
Onion-Style Breaking News Headline Generator for Live Streaming
Generates satirical breaking news headlines based on real game data events
"""

import json
import time
import random
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

try:
    from ai_client import AIClient
    from localization import HOI4Localizer
    from game_event_service import GameEventService, GameEvent
    AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI components not available: {e}")
    AI_AVAILABLE = False

class BreakingNewsGenerator:
    """Generates satirical breaking news headlines in the style of The Onion"""
    
    def __init__(self, data_path: str = None, config_path: str = None):
        if data_path is None:
            data_path = project_root / 'data' / 'game_data.json'
        if config_path is None:
            config_path = Path(__file__).parent / 'config.json'
        
        self.data_path = Path(data_path)
        self.config_path = Path(config_path)
        self.last_game_data = None
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize AI components and game event service
        if AI_AVAILABLE:
            self.ai_client = AIClient()
            self.game_event_service = GameEventService()
            print(f"BreakingNewsGenerator: GameEventService initialized")
        else:
            self.ai_client = None
            self.game_event_service = None
            self.localizer = None
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"Loaded configuration from {self.config_path}")
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Return default configuration
        return {
            "event_probabilities": {
                "political_leadership": 0.15,
                "game_events": 0.25,
                "absurd_random": 0.7
            },
            "content_settings": {
                "max_events_per_cycle": 3
            }
        }
    
    def load_game_data(self) -> Optional[Dict]:
        """Load current game data"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading game data: {e}")
        return None
    
    def find_interesting_events(self, current_data: Dict) -> List[Dict]:
        """Find interesting events to create satirical headlines about"""
        events = []
        
        if 'countries' not in current_data:
            return events
        
        # Get major and minor powers
        major_powers = []
        minor_powers = []
        
        for country in current_data['countries']:
            country_data = country.get('data', {})
            if country_data.get('major', False) or country.get('tag') in ['GER', 'USA', 'SOV', 'ENG', 'FRA', 'ITA', 'JAP']:
                major_powers.append(country)
            else:
                minor_powers.append(country)
        
        # Prefer majors but include some minors
        countries_to_check = major_powers + random.sample(minor_powers, min(2, len(minor_powers)))
        
        for country in countries_to_check:
            country_tag = country.get('tag')
            country_data = country.get('data', {})
            
            # Get ideological country name and leader info
            politics = country_data.get('politics', {})
            ruling_party = politics.get('ruling_party', 'democratic')
            country_name = self._get_ideological_country_name(country_tag, ruling_party)
            leader_name = self._get_leader_name(country_data, country_tag, ruling_party)
            
            # Focus completion events (high priority for majors)
            focus = country_data.get('focus', {})
            if focus.get('recent_completed'):
                for completed_focus in focus['recent_completed'][-2:]:  # Last 2 completed
                    focus_name = self._get_focus_name_for_display(completed_focus, country_tag)
                    focus_description = self._get_focus_description(completed_focus, country_tag)
                    events.append({
                        'type': 'focus_completed',
                        'country': country_tag,
                        'country_name': country_name,
                        'leader_name': leader_name,
                        'focus_name': focus_name,
                        'focus_description': focus_description,
                        'ruling_party': ruling_party,
                        'priority': 'high' if country_data.get('major') else 'medium'
                    })
            
            # Current focus progress
            current_focus = focus.get('current')
            progress = focus.get('progress', 0)
            if current_focus:
                focus_name = self._get_focus_name_for_display(current_focus, country_tag)
                focus_description = self._get_focus_description(current_focus, country_tag)
                
                if progress > 90:
                    events.append({
                        'type': 'focus_almost_done',
                        'country': country_tag,
                        'country_name': country_name,
                        'leader_name': leader_name,
                        'focus_name': focus_name,
                        'focus_description': focus_description,
                        'progress': progress,
                        'ruling_party': ruling_party,
                        'priority': 'high' if country_data.get('major') else 'medium'
                    })
                elif progress < 10 and random.random() < 0.3:  # New focus starts
                    events.append({
                        'type': 'focus_just_started',
                        'country': country_tag,
                        'country_name': country_name,
                        'leader_name': leader_name,
                        'focus_name': focus_name,
                        'focus_description': focus_description,
                        'ruling_party': ruling_party,
                        'priority': 'medium'
                    })
            
            # Political/ideological events
            political_prob = self.config.get('event_probabilities', {}).get('political_leadership', 0.15)
            if ruling_party and random.random() < political_prob:
                stability = country_data.get('stability', 0.5) * 100 if 'stability' in country_data else None
                war_support = country_data.get('war_support', 0.5) * 100 if 'war_support' in country_data else None
                
                events.append({
                    'type': 'political_leadership',
                    'country': country_tag,
                    'country_name': country_name,
                    'leader_name': leader_name,
                    'ruling_party': ruling_party,
                    'stability': stability,
                    'war_support': war_support,
                    'priority': 'medium' if country_data.get('major') else 'low'
                })
            
            # In-game events (if available)
            game_events_prob = self.config.get('event_probabilities', {}).get('game_events', 0.25)
            if country_data.get('events') and random.random() < game_events_prob:
                events.append({
                    'type': 'game_event',
                    'country': country_tag,
                    'country_name': country_name,
                    'leader_name': leader_name,
                    'ruling_party': ruling_party,
                    'priority': 'medium'
                })
        
        # Add some completely random/absurd events
        absurd_prob = self.config.get('event_probabilities', {}).get('absurd_random', 0.7)
        if random.random() < absurd_prob:
            random_country = random.choice(countries_to_check)
            country_tag = random_country.get('tag')
            country_data = random_country.get('data', {})
            ruling_party = country_data.get('politics', {}).get('ruling_party', 'democratic')
            country_name = self._get_ideological_country_name(country_tag, ruling_party)
            leader_name = self._get_leader_name(country_data, country_tag, ruling_party)
            
            events.append({
                'type': 'absurd_random',
                'country': country_tag,
                'country_name': country_name,
                'leader_name': leader_name,
                'ruling_party': ruling_party,
                'priority': random.choice(['low', 'medium'])
            })
        
        # Global/world events
        world_prob = self.config.get('event_probabilities', {}).get('world_situation', 0.4)
        if random.random() < world_prob:
            game_date = current_data.get('metadata', {}).get('date', '1936.1.1')
            year = int(game_date.split('.')[0]) if '.' in game_date else 1936
            
            # Pick a random major power to focus the global event on
            if major_powers:
                focus_country_obj = random.choice(major_powers)
                focus_country = focus_country_obj.get('tag')
                focus_country_data = focus_country_obj.get('data', {})
                
                if focus_country_data:
                    # Get ideological country name and leader for this country
                    ruling_party = focus_country_data.get('politics', {}).get('ruling_party', 'neutrality')
                    country_name = self._get_ideological_country_name(focus_country, ruling_party)
                    leader_name = self._get_leader_name(focus_country_data, focus_country, ruling_party)
                    
                    # Get world context similar to Twitter generator
                    world_context = self._build_world_context(current_data, focus_country)
                    
                    world_event = {
                        'type': 'world_situation',
                        'year': year,
                        'country': focus_country,
                        'country_name': country_name,
                        'leader_name': leader_name,
                        'ruling_party': ruling_party,
                        'world_context': world_context,
                        'total_countries': len(current_data.get('countries', [])),
                        'major_power_count': len(major_powers),
                        'priority': random.choice(['medium', 'low'])
                    }
                    events.append(world_event)
        
        # Prioritize and select events
        high_priority = [e for e in events if e.get('priority') == 'high']
        medium_priority = [e for e in events if e.get('priority') == 'medium']
        low_priority = [e for e in events if e.get('priority') == 'low']
        
        # Shuffle within priority levels
        random.shuffle(high_priority)
        random.shuffle(medium_priority)
        random.shuffle(low_priority)
        
        # Return a balanced mix
        selected = []
        selected.extend(high_priority[:2])  # Up to 2 high priority
        selected.extend(medium_priority[:2])  # Up to 2 medium priority
        if len(selected) < 3:
            selected.extend(low_priority[:3 - len(selected)])  # Fill up to 3 total
        
        return selected[:3]
    
    def generate_headline(self, event: Dict, game_data: Dict) -> Optional[Dict]:
        """Generate a satirical headline for an event"""
        if not AI_AVAILABLE:
            return self._generate_fallback_headline(event)
        
        try:
            prompt = self._create_headline_prompt(event, game_data)
            response = self.ai_client.generate_text(
                prompt,
                max_tokens=100,
                report_type="breaking_news_headline"
            )
            
            headline = self._parse_headline_response(response, event)
            return headline
            
        except Exception as e:
            print(f"Error generating AI headline: {e}")
            return self._generate_fallback_headline(event)
    
    def _create_headline_prompt(self, event: Dict, game_data: Dict) -> str:
        """Create a prompt for generating satirical headlines"""
        event_type = event.get('type', '')
        country_name = event.get('country_name', event.get('country', ''))
        leader_name = event.get('leader_name', '')
        ruling_party = event.get('ruling_party', '')
        
        base_prompt = f"""You are a satirical news headline writer in the style of The Onion. Create a funny, absurd breaking news headline based on this 1936-1945 historical scenario.

Current situation:
- Country: {country_name}
- Leader: {leader_name}
- Government: {ruling_party}
"""
        
        if event_type == 'focus_completed':
            focus_name = event.get('focus_name', 'Major Initiative')
            focus_description = event.get('focus_description', '')
            base_prompt += f"- Recently completed policy: '{focus_name}'\n"
            if focus_description:
                base_prompt += f"- Policy details: {focus_description}\n"
            base_prompt += f"- Context: {leader_name} has just finished implementing this major national policy initiative. The country has completed whatever reforms, military preparations, or political changes this focus entailed.\n"
        elif event_type == 'focus_almost_done':
            focus_name = event.get('focus_name', 'Major Initiative')
            focus_description = event.get('focus_description', '')
            progress = event.get('progress', 95)
            base_prompt += f"- Current policy: '{focus_name}' ({progress:.0f}% complete)\n"
            if focus_description:
                base_prompt += f"- Policy details: {focus_description}\n"
            base_prompt += f"- Context: {leader_name} is on the verge of completing this major policy. The implementation is nearly finished and results are imminent.\n"
        elif event_type == 'focus_just_started':
            focus_name = event.get('focus_name', 'Major Initiative')
            focus_description = event.get('focus_description', '')
            base_prompt += f"- New policy: '{focus_name}' (just launched)\n"
            if focus_description:
                base_prompt += f"- Policy details: {focus_description}\n"
            base_prompt += f"- Context: {leader_name} has just announced and begun implementing this new major policy direction. The country is starting down this new path.\n"
        elif event_type == 'political_leadership':
            stability = event.get('stability')
            war_support = event.get('war_support')
            
            base_prompt += f"- Government: {leader_name} leading the {ruling_party} government\n"
            if stability is not None:
                base_prompt += f"- Political stability: {stability:.0f}%\n"
            if war_support is not None:
                base_prompt += f"- War support: {war_support:.0f}%\n"
            
            base_prompt += f"- Context: {leader_name} is managing the {ruling_party} government. "
            if stability is not None:
                if stability > 70:
                    base_prompt += "The country is politically stable. "
                elif stability < 40:
                    base_prompt += "The country is experiencing political instability. "
            if war_support is not None:
                if war_support > 70:
                    base_prompt += "Citizens are supportive of military action. "
                elif war_support < 40:
                    base_prompt += "Citizens are war-weary and oppose military action. "
            # Use configurable context templates
            political_contexts = self.config.get('prompt_templates', {}).get('political_leadership_contexts', [
                "Focus on the absurdities of political leadership, governance, and ideological rule."
            ])
            base_prompt += random.choice(political_contexts) + "\n"
        elif event_type == 'game_event':
            base_prompt += f"- Recent development: A significant political event has occurred in {country_name}\n"
            base_prompt += f"- Context: {leader_name} and the {ruling_party} government are dealing with major political developments, decisions, or crises. Focus on the absurd aspects of political crisis management and decision-making.\n"
        elif event_type == 'absurd_random':
            absurd_prompts = self.config.get('prompt_templates', {}).get('absurd_random_prompts', [
                "Leader dealing with ridiculous personal problems",
                "Bizarre national shortages or surpluses", 
                "Silly bureaucratic mix-ups"
            ])
            selected_prompt = random.choice(absurd_prompts)
            base_prompt += f"- Context: Create a completely absurd, mundane daily life situation involving {leader_name} or {country_name}. Focus on: {selected_prompt}\n"
        elif event_type == 'world_situation':
            year = event.get('year', 1936)
            total_countries = event.get('total_countries', 0)
            major_powers = event.get('major_power_count', 0)
            world_context = event.get('world_context', '')
            
            base_prompt += f"- Global context: Year {year}, {major_powers} major powers among {total_countries} nations worldwide\n"
            if world_context:
                base_prompt += f"- World situation details:\n{world_context}\n"
            base_prompt += f"- Context: Focus on the absurdities of international relations, diplomacy, and global politics. Create headlines about ridiculous diplomatic incidents, silly international rivalries, absurd alliance negotiations, or comical misunderstandings between nations. Use {country_name} as the focal point but make it about international/global implications.\n"
        
        base_prompt += f"""
Create a single satirical breaking news headline (no quotation marks, byline, or extra text). Make it:
- Absurdly exaggerated and ridiculous
- In the authentic style of The Onion newspaper
- 8-20 words long (can be longer if funnier)
- Use specific leader/country names when appropriate
- Mix historical context with absurd modern concerns
- Family-friendly but edgy humor

Onion-style examples:
"Chancellor Hitler Reportedly Frustrated Nobody Compliments His Landscape Paintings"
"Stalin Introduces Five-Year Plan for Personally High-Fiving Every Soviet Citizen"  
"Local Democracy Accidentally Elects Competent Leader, Unsure How to Proceed"
"Nation's Military Budget Mysteriously Doubled After Defense Minister's Nephew Opens Tank Dealership"
"Breaking: World's Problems Could Be Solved If Everyone Just Tried Being Nice"

Your headline (use {country_name} and {leader_name} if appropriate):"""
        
        return base_prompt
    
    def _parse_headline_response(self, response: str, event: Dict) -> Dict:
        """Parse AI response into headline structure"""
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        
        # Find the actual headline (skip any preamble)
        headline_text = ""
        for line in lines:
            # Skip lines that look like instructions or formatting
            if not any(skip_word in line.lower() for skip_word in ['headline:', 'here', 'title:', 'breaking:']):
                headline_text = line.strip()
                break
        
        if not headline_text and lines:
            headline_text = lines[0].strip()
        
        # Clean up the headline
        headline_text = headline_text.strip('"\'').strip()
        
        return {
            'id': int(time.time() * 1000),
            'headline': headline_text,
            'country': event.get('country'),
            'event_type': event.get('type'),
            'priority': event.get('priority', 'medium'),
            'created_at': time.time(),
            'display_duration': self._get_display_duration(event.get('priority', 'medium'))
        }
    
    def _generate_fallback_headline(self, event: Dict) -> Dict:
        """Generate a simple fallback headline"""
        country_name = self._get_country_name(event.get('country', ''))
        event_type = event.get('type', '')
        
        fallback_headlines = {
            'focus_almost_complete': [
                f"{country_name} Leaders 'Almost Done' With Important Thing",
                f"Nation Reportedly 97% Finished With Mysterious Project",
                f"{country_name} Officials Promise to 'Wrap Things Up Soon'"
            ],
            'focus_progressing': [
                f"{country_name} Still Working on That One Thing",
                f"National Progress Meter Shows 'Getting There'",
                f"{country_name} Leaders Optimistic About Unnamed Initiative"
            ],
            'focus_just_started': [
                f"{country_name} Begins Ambitious New Something",
                f"Nation's Latest Project Already 'Going Well,' Say Officials",
                f"{country_name} Leaders Excited About Fresh Start"
            ],
            'political_situation': [
                f"{country_name} Government Continues to Govern",
                f"Nation's Politics Described as 'Very Political'",
                f"{country_name} Leaders Still in Charge of Things"
            ],
            'large_military': [
                f"{country_name} Army Reportedly 'Getting Quite Large'",
                f"Nation's Military Runs Out of Parade Ground Space",
                f"{country_name} Generals Complain About Overcrowded Barracks"
            ],
            'global_situation': [
                f"World Continues to Exist Despite Everything",
                f"International Community Still Figuring Things Out",
                f"Global Situation Remains Globally Situated"
            ]
        }
        
        headlines = fallback_headlines.get(event_type, [
            f"{country_name} Experiences Events",
            "Local Nation Does Nation Things",
            "Breaking: Something Happening Somewhere"
        ])
        
        return {
            'id': int(time.time() * 1000),
            'headline': random.choice(headlines),
            'country': event.get('country'),
            'event_type': event_type,
            'priority': event.get('priority', 'medium'),
            'created_at': time.time(),
            'display_duration': self._get_display_duration(event.get('priority', 'medium'))
        }
    
    def _get_display_duration(self, priority: str) -> int:
        """Get how long headline should be displayed (in seconds)"""
        durations = {
            'high': 20,
            'medium': 15,
            'low': 10
        }
        return durations.get(priority, 15)
    
    def _get_country_name(self, country_tag: str) -> str:
        """Get readable country name"""
        if self.localizer:
            return self.localizer.get_country_name(country_tag)
        
        # Fallback mapping
        country_names = {
            'GER': 'Germany', 'USA': 'America', 'SOV': 'Soviet Union', 
            'ENG': 'Britain', 'FRA': 'France', 'ITA': 'Italy', 'JAP': 'Japan',
            'POL': 'Poland', 'SPA': 'Spain', 'HOL': 'Netherlands'
        }
        return country_names.get(country_tag, country_tag)
    
    def _get_focus_name_for_display(self, focus_id: str, country_tag: str) -> str:
        """Get proper focus name for display"""
        if not self.localizer:
            return self._clean_focus_name(focus_id, country_tag)
        
        # Try to get localized focus name
        localized_name = self.localizer.get_localized_text(focus_id)
        if localized_name != focus_id and localized_name:
            return localized_name
        
        # Try uppercase variation
        localized_upper = self.localizer.get_localized_text(focus_id.upper())
        if localized_upper != focus_id.upper() and localized_upper:
            return localized_upper
        
        # Fall back to cleaned name
        return self._clean_focus_name(focus_id, country_tag)
    
    def _get_focus_description(self, focus_id: str, country_tag: str) -> str:
        """Get focus description"""
        if not self.localizer:
            return self._clean_focus_name(focus_id, country_tag)
        
        variations = [
            focus_id,
            focus_id.upper(),
            f"{country_tag.upper()}_{focus_id.split('_', 1)[1] if '_' in focus_id else focus_id}"
        ]
        
        for variant in variations:
            desc_key = f"{variant}_desc"
            description = self.localizer.get_localized_text(desc_key)
            
            if description != desc_key and description:
                if description.endswith(" Desc") and len(description) < 50:
                    continue
                
                import re
                description = re.sub(r'\[.*?\]', '', description)
                description = re.sub(r'§[A-Za-z]', '', description)
                description = description.strip()
                
                return description
        
        return self._clean_focus_name(focus_id, country_tag)
    
    def _get_ideological_country_name(self, country_tag: str, ruling_party: str) -> str:
        """Get ideological country name"""
        if self.localizer:
            # Try ideological variant first
            ideological_name = self.localizer.get_country_name(country_tag, ruling_party)
            if ideological_name and ideological_name != country_tag:
                return ideological_name
            
            # Fall back to standard name
            return self.localizer.get_country_name(country_tag)
        
        # Fallback mapping with ideological variants
        ideological_names = {
            ('GER', 'fascism'): 'Nazi Germany',
            ('GER', 'democratic'): 'German Republic', 
            ('GER', 'communism'): 'German Socialist Republic',
            ('SOV', 'communism'): 'Soviet Union',
            ('SOV', 'democratic'): 'Russian Republic',
            ('USA', 'fascism'): 'American Reich',
            ('USA', 'communism'): 'American Socialist Republic',
            ('ENG', 'fascism'): 'Fascist Britain',
            ('ENG', 'communism'): 'Socialist Britain',
            ('FRA', 'fascism'): 'Vichy France',
            ('FRA', 'communism'): 'French Socialist Republic',
            ('ITA', 'fascism'): 'Fascist Italy',
            ('ITA', 'democratic'): 'Italian Republic',
            ('JAP', 'fascism'): 'Imperial Japan',
        }
        
        ideological_name = ideological_names.get((country_tag, ruling_party))
        if ideological_name:
            return ideological_name
            
        # Standard fallback
        country_names = {
            'GER': 'Germany', 'USA': 'United States', 'SOV': 'Soviet Union',
            'ENG': 'Britain', 'FRA': 'France', 'ITA': 'Italy', 'JAP': 'Japan',
            'POL': 'Poland', 'SPA': 'Spain', 'HOL': 'Netherlands'
        }
        return country_names.get(country_tag, country_tag)
    
    def _get_leader_name(self, country_data: Dict, country_tag: str, ruling_party: str) -> str:
        """Get leader name or appropriate title"""
        politics = country_data.get('politics', {})
        
        # Try to get actual leader name from game data
        parties = politics.get('parties', {})
        if ruling_party in parties:
            party_data = parties[ruling_party]
            leaders = party_data.get('country_leader', [])
            if leaders:
                leader = leaders[0]
                character = leader.get('character', {})
                character_name = character.get('name')
                
                if character_name and self.localizer:
                    localized_name = self.localizer.get_localized_text(character_name)
                    if localized_name and localized_name != character_name:
                        return localized_name
        
        # Fallback to appropriate titles by ideology and country
        ideology = ruling_party.lower()
        
        if ideology == 'fascism':
            fascist_titles = {
                'GER': 'Chancellor Hitler',
                'ITA': 'Il Duce',
                'JAP': 'Emperor Hirohito',
                'ENG': 'Prime Minister Mosley',
                'USA': 'President Long',
                'FRA': 'Marshal Pétain'
            }
            return fascist_titles.get(country_tag, 'The Leader')
        elif ideology == 'communism':
            communist_titles = {
                'SOV': 'Comrade Stalin', 
                'GER': 'Chairman Thälmann',
                'USA': 'Comrade Foster',
                'ENG': 'Comrade Pollitt',
                'FRA': 'Comrade Thorez'
            }
            return communist_titles.get(country_tag, 'The Chairman')
        elif ideology == 'democratic':
            democratic_titles = {
                'USA': 'President Roosevelt',
                'ENG': 'Prime Minister Chamberlain',
                'FRA': 'President Lebrun', 
                'GER': 'Chancellor Wirth'
            }
            return democratic_titles.get(country_tag, 'The President')
        else:
            return f'Leader of {self._get_country_name(country_tag)}'
    
    def _clean_focus_name(self, focus_id: str, country_tag: str) -> str:
        """Clean up focus names for display"""
        clean = focus_id.replace(f"{country_tag.lower()}_", "")
        clean = clean.replace("_", " ").title()
        return clean
    
    def run_headline_generation(self, interval: int = 30):
        """Run automatic headline generation"""
        print(f"Starting breaking news headline generation (interval: {interval}s)")
        print(f"Data path: {self.data_path}")
        print(f"AI Available: {AI_AVAILABLE}")
        
        while True:
            try:
                current_data = self.load_game_data()
                
                if current_data:
                    events = self.find_interesting_events(current_data)
                    
                    if events:
                        selected_event = random.choice(events)
                        
                        print(f"📰 Processing event: {selected_event.get('type', 'unknown')}")
                        
                        headline = self.generate_headline(selected_event, current_data)
                        
                        if headline:
                            print(f"🚨 Generated headline: {headline.get('headline', '')}...")
                            
                            # Save headline to file for web interface
                            self._save_current_headline(headline)
                        
                    else:
                        print("⏳ No interesting events found, waiting...")
                    
                    self.last_game_data = current_data
                    
                else:
                    print("❌ Could not load game data")
                
            except Exception as e:
                print(f"Error in headline generation: {e}")
            
            time.sleep(interval)
    
    def _save_current_headline(self, headline: Dict):
        """Save current headline to file for web interface"""
        try:
            output_file = Path(__file__).parent / 'current_headline.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(headline, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving headline: {e}")
    
    def _build_world_context(self, game_data: Dict, focus_country: str) -> str:
        """Build comprehensive world context for global events, similar to Twitter generator"""
        context_parts = []
        
        if 'countries' in game_data:
            # Get major powers and create summaries
            major_powers = []
            country_summaries = []
            
            for country in game_data['countries']:
                country_tag = country.get('tag', '')
                country_data = country.get('data', {})
                is_major = country_data.get('major', False) == True
                
                if is_major:
                    major_powers.append((country_tag, country_data))
            
            # Process major powers for context
            for country_tag, country_data in major_powers[:4]:  # Top 4 majors
                # Get ideological country name and leader info
                ruling_party = country_data.get('politics', {}).get('ruling_party', 'neutrality')
                ideological_country_name = self._get_ideological_country_name(country_tag, ruling_party)
                current_leader = self._get_leader_name(country_data, country_tag, ruling_party)
                
                # Political situation analysis
                politics = country_data.get('politics', {})
                parties = politics.get('parties', {})
                stability = country_data.get('stability', 1.0)
                
                political_notes = []
                if parties:
                    fascist_pop = parties.get('fascism', {}).get('popularity', 0)
                    communist_pop = parties.get('communism', {}).get('popularity', 0)
                    
                    if fascist_pop > 30:
                        political_notes.append("rising fascist movement")
                    elif fascist_pop > 15:
                        political_notes.append("growing fascist support")
                    
                    if communist_pop > 30:
                        political_notes.append("strong communist influence")
                    elif communist_pop > 15:
                        political_notes.append("communist activity")
                    
                    if stability < 0.5:
                        political_notes.append("internal instability")
                    elif stability < 0.7:
                        political_notes.append("political tensions")
                
                # Focus analysis
                focus = country_data.get('focus', {})
                current_focus = focus.get('current', '')
                focus_notes = []
                
                if current_focus:
                    focus_description = self._get_focus_description(current_focus, country_tag)
                    if focus_description:
                        focus_progress = focus.get('progress', 0)
                        if focus_progress > 80:
                            focus_notes.append(f"completing {focus_description}")
                        else:
                            focus_notes.append(f"pursuing {focus_description}")
                
                # Combine information
                all_notes = political_notes + focus_notes
                if all_notes:
                    power_indicator = "★" if country_tag == focus_country else "•"
                    summary = f"{power_indicator} {ideological_country_name}"
                    if current_leader and current_leader not in ['Leader', 'Head of State', 'The Leader']:
                        summary += f" (led by {current_leader})"
                    summary += f": {' | '.join(all_notes)}"
                    country_summaries.append(summary)
            
            if country_summaries:
                context_parts.append("Major Powers Status:")
                for summary in country_summaries:
                    context_parts.append(f"  {summary}")
        
        # Add recent events context if available
        if 'metadata' in game_data and 'recent_events' in game_data['metadata']:
            recent = game_data['metadata']['recent_events'][:3]  # Last 3 events
            if recent:
                context_parts.append("Recent International Developments:")
                for i, event in enumerate(recent):
                    if isinstance(event, dict):
                        evt_title = event.get('title', str(event))
                        context_parts.append(f"  • {evt_title}")
                    else:
                        context_parts.append(f"  • {str(event)}")
        
        return "\n".join(context_parts) if context_parts else "General international situation developing"

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Breaking News Headline Generator')
    parser.add_argument('--interval', type=int, default=30, help='Generation interval in seconds')
    parser.add_argument('--data-path', type=str, help='Path to game_data.json')
    
    args = parser.parse_args()
    
    generator = BreakingNewsGenerator(args.data_path)
    generator.run_headline_generation(args.interval)