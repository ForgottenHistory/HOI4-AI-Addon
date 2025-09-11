#!/usr/bin/env python3
"""
Game Event Service
Centralized service for extracting random game events with proper localization
Used by all content generators (breaking news, Twitter, etc.) for consistency
"""

import random
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Import existing localization system
from localization import HOI4Localizer


@dataclass
class GameEvent:
    """Standardized game event with all necessary data for content generation"""
    event_type: str  # 'focus_completed', 'focus_progressing', 'political_situation', 'world_situation', 'absurd_random'
    country_tag: str
    country_name: str  # Localized, ideological name
    leader_name: str   # Localized leader name
    ruling_party: str  # Generic party (fascism, communism, democratic, neutrality)
    specific_ideology: Optional[str]  # Specific ideology (leninism, nazism, etc.)
    priority: str      # 'high', 'medium', 'low'
    
    # Event-specific data
    focus_id: Optional[str] = None
    focus_name: Optional[str] = None  # Localized
    focus_description: Optional[str] = None  # Localized
    focus_progress: Optional[int] = None
    
    political_situation: Optional[str] = None
    stability: Optional[float] = None
    world_context: Optional[str] = None
    
    # Raw data for advanced use
    raw_country_data: Optional[Dict] = None


class GameEventService:
    """Centralized service for extracting random game events from HOI4 data"""
    
    def __init__(self, localizer: Optional[HOI4Localizer] = None):
        """Initialize with optional localizer (will create one if not provided)"""
        self.localizer = localizer
        if not self.localizer:
            print("GameEventService: Initializing new localizer...")
            self.localizer = HOI4Localizer()
            self._load_all_localization()
    
    def _load_all_localization(self):
        """Load all available localization files"""
        try:
            import glob
            locale_dir = Path(__file__).parent.parent / 'locale'
            print(f"Loading all localization files from {locale_dir}")
            
            all_locale_files = glob.glob(str(locale_dir / '*_l_english.yml'))
            
            # Prioritize core files
            base_files = []
            dlc_files = []
            
            for locale_file in all_locale_files:
                filename = Path(locale_file).name
                if any(core in filename for core in ['countries_', 'focus_', 'events_', 'core_']):
                    base_files.append(filename)
                else:
                    dlc_files.append(filename)
            
            # Load base files first, then DLC files
            for filename in sorted(base_files):
                try:
                    self.localizer.load_localization_file(filename)
                except Exception as e:
                    print(f"Warning: Could not load {filename}: {e}")
            
            for filename in sorted(dlc_files):
                try:
                    self.localizer.load_localization_file(filename)
                except Exception as e:
                    print(f"Warning: Could not load {filename}: {e}")
            
            print(f"GameEventService: Loaded {len(self.localizer.translations)} total translations")
            
        except Exception as e:
            print(f"Warning: Could not load localization files: {e}")
    
    def get_random_focus_event(self, game_data: Dict, prefer_majors: bool = True, 
                             event_types: List[str] = None) -> Optional[GameEvent]:
        """
        Get a random focus-related event
        event_types: ['completed', 'progressing', 'just_started'] or None for any
        """
        if not event_types:
            event_types = ['completed', 'progressing', 'just_started']
        
        countries = game_data.get('countries', [])
        if not countries:
            return None
        
        # Separate major and minor powers
        majors = [c for c in countries if c.get('data', {}).get('major', False)]
        minors = [c for c in countries if not c.get('data', {}).get('major', False)]
        
        # Choose country pool
        if prefer_majors and majors:
            candidates = majors + minors[:2]  # All majors + 2 minors
        else:
            candidates = countries
        
        # Try to find a country with focus data
        random.shuffle(candidates)
        for country in candidates:
            country_tag = country.get('tag')
            country_data = country.get('data', {})
            focus_data = country_data.get('focus', {})
            
            if not focus_data:
                continue
            
            # Determine event type based on focus state
            current_focus = focus_data.get('current')
            completed_focuses = focus_data.get('completed', [])
            progress = focus_data.get('progress', 0)
            
            event_type = None
            focus_id = None
            
            if 'completed' in event_types and completed_focuses:
                event_type = 'focus_completed'
                focus_id = random.choice(completed_focuses[-3:])  # Recent completions
            elif 'progressing' in event_types and current_focus and progress > 20:
                if progress > 90 and 'just_started' not in event_types:
                    continue  # Skip almost done if just_started not allowed
                event_type = 'focus_progressing'
                focus_id = current_focus
            elif 'just_started' in event_types and current_focus and progress <= 20:
                event_type = 'focus_just_started'
                focus_id = current_focus
            
            if event_type and focus_id:
                return self._create_focus_event(
                    event_type, country_tag, country_data, focus_id, progress
                )
        
        return None
    
    def get_random_political_situation(self, game_data: Dict, prefer_majors: bool = True) -> Optional[GameEvent]:
        """Get a random political situation event"""
        countries = game_data.get('countries', [])
        if not countries:
            return None
        
        # Filter for interesting political situations
        candidates = []
        for country in countries:
            country_data = country.get('data', {})
            politics = country_data.get('politics', {})
            parties = politics.get('parties', {})
            stability = country_data.get('stability', 1.0)
            
            # Look for interesting political dynamics
            if parties:
                fascist_pop = parties.get('fascism', {}).get('popularity', 0)
                communist_pop = parties.get('communism', {}).get('popularity', 0)
                
                is_interesting = (
                    fascist_pop > 15 or communist_pop > 15 or 
                    stability < 0.7 or politics.get('political_power', 0) < 30
                )
                
                if is_interesting:
                    priority = 'high' if country_data.get('major', False) else 'medium'
                    candidates.append((country, priority))
        
        if not candidates:
            # Fallback to any country
            candidates = [(c, 'low') for c in countries]
        
        if candidates:
            country, priority = random.choice(candidates)
            return self._create_political_event(
                country.get('tag'), country.get('data', {}), priority
            )
        
        return None
    
    def get_random_world_situation(self, game_data: Dict) -> Optional[GameEvent]:
        """Get a world situation event focused on a major power"""
        countries = game_data.get('countries', [])
        majors = [c for c in countries if c.get('data', {}).get('major', False)]
        
        if not majors:
            return None
        
        focus_country = random.choice(majors)
        country_tag = focus_country.get('tag')
        country_data = focus_country.get('data', {})
        
        # Build world context
        world_context = self._build_world_context(game_data, country_tag)
        
        ruling_party = country_data.get('politics', {}).get('ruling_party', 'neutrality')
        
        return GameEvent(
            event_type='world_situation',
            country_tag=country_tag,
            country_name=self._get_ideological_country_name(country_tag, country_data),
            leader_name=self._get_leader_name(country_data, country_tag),
            ruling_party=ruling_party,
            specific_ideology=self._get_specific_ideology(country_data, ruling_party),
            priority=random.choice(['medium', 'low']),
            world_context=world_context,
            raw_country_data=country_data
        )
    
    def get_random_absurd_event(self, game_data: Dict) -> Optional[GameEvent]:
        """Get a completely absurd/random event"""
        countries = game_data.get('countries', [])
        if not countries:
            return None
        
        # Prefer majors but allow any
        majors = [c for c in countries if c.get('data', {}).get('major', False)]
        candidates = majors if majors else countries
        
        country = random.choice(candidates)
        country_tag = country.get('tag')
        country_data = country.get('data', {})
        
        ruling_party = country_data.get('politics', {}).get('ruling_party', 'neutrality')
        
        return GameEvent(
            event_type='absurd_random',
            country_tag=country_tag,
            country_name=self._get_ideological_country_name(country_tag, country_data),
            leader_name=self._get_leader_name(country_data, country_tag),
            ruling_party=ruling_party,
            specific_ideology=self._get_specific_ideology(country_data, ruling_party),
            priority=random.choice(['low', 'medium']),
            raw_country_data=country_data
        )
    
    def get_any_random_event(self, game_data: Dict, prefer_majors: bool = True) -> GameEvent:
        """
        Get any random event - guaranteed to return something
        This eliminates the "no events found" problem
        """
        # Try different event types in order of preference
        attempts = [
            lambda: self.get_random_focus_event(game_data, prefer_majors),
            lambda: self.get_random_political_situation(game_data, prefer_majors),
            lambda: self.get_random_world_situation(game_data),
            lambda: self.get_random_absurd_event(game_data)
        ]
        
        random.shuffle(attempts)  # Randomize the order
        
        for attempt in attempts:
            event = attempt()
            if event:
                return event
        
        # Ultimate fallback - create a minimal event
        return self._create_fallback_event(game_data)
    
    def _create_focus_event(self, event_type: str, country_tag: str, country_data: Dict, 
                          focus_id: str, progress: int) -> Optional[GameEvent]:
        """Create a focus-related event with full localization"""
        ruling_party = country_data.get('politics', {}).get('ruling_party', 'neutrality')
        
        # Get localized focus data
        focus_name = self._get_localized_focus_name(focus_id, country_tag)
        focus_description = self._get_localized_focus_description(focus_id, country_tag)
        
        # Skip events with dynamic content in focus name or description
        if '[' in focus_name or ']' in focus_name or '[' in focus_description or ']' in focus_description:
            return None
        
        return GameEvent(
            event_type=event_type,
            country_tag=country_tag,
            country_name=self._get_ideological_country_name(country_tag, country_data),
            leader_name=self._get_leader_name(country_data, country_tag),
            ruling_party=ruling_party,
            specific_ideology=self._get_specific_ideology(country_data, ruling_party),
            priority='high' if country_data.get('major', False) else 'medium',
            focus_id=focus_id,
            focus_name=focus_name,
            focus_description=focus_description,
            focus_progress=progress,
            raw_country_data=country_data
        )
    
    def _create_political_event(self, country_tag: str, country_data: Dict, priority: str) -> GameEvent:
        """Create a political situation event"""
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'neutrality')
        
        return GameEvent(
            event_type='political_situation',
            country_tag=country_tag,
            country_name=self._get_ideological_country_name(country_tag, country_data),
            leader_name=self._get_leader_name(country_data, country_tag),
            ruling_party=ruling_party,
            specific_ideology=self._get_specific_ideology(country_data, ruling_party),
            priority=priority,
            political_situation=self._analyze_political_situation(country_data),
            stability=country_data.get('stability', 1.0),
            raw_country_data=country_data
        )
    
    def _create_fallback_event(self, game_data: Dict) -> GameEvent:
        """Create a minimal fallback event when all else fails"""
        return GameEvent(
            event_type='absurd_random',
            country_tag='GER',  # Safe fallback
            country_name='Germany',
            leader_name='The Leader', 
            ruling_party='neutrality',
            specific_ideology=None,
            priority='low'
        )
    
    def _get_ideological_country_name(self, country_tag: str, country_data: Dict) -> str:
        """Get ideologically appropriate country name using localization"""
        ruling_party = country_data.get('politics', {}).get('ruling_party', 'neutrality')
        
        # Try ideological variant first
        if self.localizer:
            ideological_name = self.localizer.get_country_name(country_tag, ruling_party)
            if ideological_name and ideological_name != country_tag:
                return ideological_name
            
            # Fallback to standard name
            standard_name = self.localizer.get_country_name(country_tag)
            if standard_name and standard_name != country_tag:
                return standard_name
        
        # Ultimate fallback
        fallback_names = {
            'GER': 'Germany', 'USA': 'United States', 'SOV': 'Soviet Union',
            'ENG': 'Britain', 'FRA': 'France', 'ITA': 'Italy', 'JAP': 'Japan'
        }
        return fallback_names.get(country_tag, country_tag)
    
    def _get_leader_name(self, country_data: Dict, country_tag: str) -> str:
        """Get localized leader name with ideological fallbacks"""
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'neutrality')
        
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
                    # Try direct localization of character name (e.g. "DEN_thorvald_stauning")
                    localized_name = self.localizer.get_localized_text(character_name)
                    if localized_name and localized_name != character_name and len(localized_name) > 3:
                        return localized_name
                    
                    # Try additional patterns as fallback
                    localization_attempts = [
                        character_name.upper(),
                        f"{character_name}_NAME", 
                        f"{country_tag}_{character_name}",
                        f"LEADER_{country_tag}_{character_name}"
                    ]
                    
                    for attempt in localization_attempts:
                        localized_name = self.localizer.get_localized_text(attempt)
                        if localized_name and localized_name != attempt and len(localized_name) > 3:
                            return localized_name
        
        # Get specific ideology for better fallbacks
        specific_ideology = self._get_specific_ideology(country_data, ruling_party)
        ideology = specific_ideology.lower() if specific_ideology else ruling_party.lower()
        
        # Use specific ideology for more descriptive leaders
        if 'fascis' in ideology or 'nazi' in ideology:
            fascist_leaders = {
                'GER': 'Chancellor Hitler', 'ITA': 'Il Duce', 'JAP': 'Emperor Hirohito',
                'ENG': 'Prime Minister Mosley', 'USA': 'President Long', 'FRA': 'Marshal Pétain'
            }
            return fascist_leaders.get(country_tag, 'The Führer')
        elif 'commun' in ideology or 'lenin' in ideology or 'stalin' in ideology or 'trotskyis' in ideology:
            communist_leaders = {
                'SOV': 'Comrade Stalin', 'GER': 'Chairman Thälmann', 'USA': 'Comrade Foster',
                'ENG': 'Comrade Pollitt', 'FRA': 'Comrade Thorez'
            }
            if 'lenin' in ideology:
                return communist_leaders.get(country_tag, 'Comrade Lenin')
            elif 'stalin' in ideology:
                return communist_leaders.get(country_tag, 'Comrade Stalin')
            elif 'trotskyis' in ideology:
                return communist_leaders.get(country_tag, 'Comrade Trotsky')
            else:
                return communist_leaders.get(country_tag, 'The Chairman')
        elif 'democrat' in ideology or 'liberal' in ideology:
            democratic_leaders = {
                'USA': 'President Roosevelt', 'ENG': 'Prime Minister Baldwin',
                'FRA': 'President Lebrun', 'GER': 'Chancellor Brüning'
            }
            return democratic_leaders.get(country_tag, 'The President')
        else:
            # Neutrality or other specific ideologies
            neutral_leaders = {
                'GER': 'Chancellor Brüning', 'USA': 'President Hoover',
                'ENG': 'King Edward VIII', 'FRA': 'President Lebrun'
            }
            return neutral_leaders.get(country_tag, 'The Leader')
    
    def _get_specific_ideology(self, country_data: Dict, ruling_party: str) -> Optional[str]:
        """Extract specific ideology from party data (e.g. 'leninism' instead of 'communism')"""
        politics = country_data.get('politics', {})
        parties = politics.get('parties', {})
        
        if ruling_party in parties:
            party_data = parties[ruling_party]
            leaders = party_data.get('country_leader', [])
            if leaders:
                leader = leaders[0]
                specific_ideology = leader.get('ideology')
                if specific_ideology:
                    return specific_ideology
        
        return None
    
    def _get_localized_focus_name(self, focus_id: str, country_tag: str) -> str:
        """Get localized focus name"""
        if not self.localizer:
            return self._clean_focus_name(focus_id, country_tag)
        
        # Try various localization formats for focus names
        variations = [
            focus_id,
            focus_id.upper(),
            f"{focus_id}_NAME",
            f"{focus_id}_TITLE", 
            f"{country_tag}_{focus_id}",
            f"{country_tag.upper()}_{focus_id}",
            f"{country_tag.upper()}_{focus_id.upper()}",
            # Remove country prefix and try
            focus_id.replace(f"{country_tag}_", "") if f"{country_tag}_" in focus_id else focus_id,
            focus_id.replace(f"{country_tag.upper()}_", "") if f"{country_tag.upper()}_" in focus_id else focus_id
        ]
        
        for variant in variations:
            if not variant:  # Skip empty strings
                continue
            localized = self.localizer.get_localized_text(variant)
            if localized and localized != variant and len(localized) > 3 and not localized.endswith("_NAME"):
                # Skip any localized text with dynamic placeholders
                if '[' in localized or ']' in localized:
                    continue
                return localized
        
        return self._clean_focus_name(focus_id, country_tag)
    
    def _get_localized_focus_description(self, focus_id: str, country_tag: str) -> str:
        """Get localized focus description"""
        if not self.localizer:
            return self._clean_focus_name(focus_id, country_tag)
        
        # Try description variants - more comprehensive patterns
        focus_base = focus_id.replace(f"{country_tag}_", "") if f"{country_tag}_" in focus_id else focus_id
        focus_base = focus_base.replace(f"{country_tag.upper()}_", "") if f"{country_tag.upper()}_" in focus_id else focus_base
        
        variations = [
            f"{focus_id}_desc",
            f"{focus_id.upper()}_DESC",
            f"{focus_id}_description", 
            f"{focus_id.upper()}_DESCRIPTION",
            f"{focus_base}_desc",
            f"{focus_base.upper()}_DESC",
            f"{country_tag.upper()}_{focus_base}_desc",
            f"{country_tag.upper()}_{focus_base.upper()}_DESC",
            # Tooltip variations
            f"{focus_id}_tt",
            f"{focus_id.upper()}_TT",
            f"{focus_id}_tooltip",
            f"{focus_id.upper()}_TOOLTIP"
        ]
        
        for variant in variations:
            if not variant:
                continue
            description = self.localizer.get_localized_text(variant)
            if description and description != variant and len(description) > 10:
                # Skip any description with dynamic placeholders - reject entirely
                if '[' in description or ']' in description:
                    continue
                    
                # Clean up description
                import re
                description = re.sub(r'§[A-Za-z!]', '', description)  # Remove color codes
                description = re.sub(r'\$[A-Za-z_]+\$', '', description)  # Remove variable placeholders
                description = description.strip()
                
                # Reject if it's just the name + "Desc" suffix - not a real description  
                if (len(description) > 25 and 
                    not description.upper().endswith(("DESC", "DESCRIPTION", "TT", "TOOLTIP")) and
                    not description.endswith(" Desc") and
                    not description.endswith(" Focus")):
                    return description
        
        return self._clean_focus_name(focus_id, country_tag)
    
    def _clean_focus_name(self, focus_id: str, country_tag: str) -> str:
        """Clean focus ID into readable name"""
        # Remove country prefix
        if focus_id.upper().startswith(country_tag.upper() + "_"):
            clean_name = focus_id[len(country_tag) + 1:]
        else:
            clean_name = focus_id
        
        # Convert underscores to spaces and title case
        return clean_name.replace("_", " ").title()
    
    def _analyze_political_situation(self, country_data: Dict) -> str:
        """Analyze political situation and return description"""
        politics = country_data.get('politics', {})
        parties = politics.get('parties', {})
        stability = country_data.get('stability', 1.0)
        political_power = politics.get('political_power', 0)
        
        situations = []
        
        if parties:
            fascist_pop = parties.get('fascism', {}).get('popularity', 0)
            communist_pop = parties.get('communism', {}).get('popularity', 0)
            
            if fascist_pop > 30:
                situations.append("dominant fascist movement")
            elif fascist_pop > 15:
                situations.append("rising fascist influence")
            
            if communist_pop > 30:
                situations.append("strong communist support")
            elif communist_pop > 15:
                situations.append("growing communist movement")
        
        if stability < 0.4:
            situations.append("severe instability")
        elif stability < 0.6:
            situations.append("political unrest")
        
        if political_power < 20:
            situations.append("government crisis")
        
        return "; ".join(situations) if situations else "stable political situation"
    
    def _build_world_context(self, game_data: Dict, focus_country: str) -> str:
        """Build comprehensive world context summary using Twitter generator logic"""
        context_parts = []
        
        # Add world situation summary
        context_parts.append("=== WORLD SITUATION SUMMARY ===")
        
        # Economic and political overview
        if 'countries' in game_data:
            # Separate major and minor powers
            majors_list = []
            minors_list = []
            
            for country in game_data['countries']:
                country_data = country.get('data', {})
                is_major = country_data.get('major', False) == True
                
                if is_major:
                    majors_list.append(country)
                else:
                    minors_list.append(country)
            
            # Process major powers first, then select a few interesting minors
            countries_to_process = majors_list + minors_list[:4]  # All majors + 4 minors
            
            country_summaries = []
            
            for country in countries_to_process:
                country_tag = country.get('tag', 'Unknown')
                country_data = country.get('data', {})
                
                # Get ideological country name and leader info
                ideological_country_name = self._get_ideological_country_name(country_tag, country_data)
                
                # Political situation
                politics = country_data.get('politics', {})
                parties = politics.get('parties', {})
                stability = country_data.get('stability', 1.0)
                political_power = politics.get('political_power', 0)
                ruling_party = politics.get('ruling_party', 'unknown')
                
                # Get current leader name
                current_leader = self._get_leader_name(country_data, country_tag)
                
                # Focus details with descriptions
                focus = country_data.get('focus', {})
                current_focus = focus.get('current', '')
                focus_progress = focus.get('progress', 0)
                completed_focuses = focus.get('completed', [])
                
                # Build rich country profile
                political_notes = []
                
                # Political analysis with descriptive text
                if parties:
                    fascist_pop = parties.get('fascism', {}).get('popularity', 0)
                    communist_pop = parties.get('communism', {}).get('popularity', 0)
                    democratic_pop = parties.get('democratic', {}).get('popularity', 0)
                    
                    if fascist_pop > 30:
                        political_notes.append("dominant fascist movement")
                    elif fascist_pop > 15:
                        political_notes.append("rising fascist influence")
                    
                    if communist_pop > 30:
                        political_notes.append("strong communist support")
                    elif communist_pop > 15:
                        political_notes.append("growing communist movement")
                    
                    if stability < 0.4:
                        political_notes.append("severe instability")
                    elif stability < 0.6:
                        political_notes.append("political unrest")
                    
                    if political_power < 20:
                        political_notes.append("government crisis")

                # Economic analysis - simplified for now
                economic_notes = []
                # Default to focused war economy assumption for major powers
                if country_data.get('major', False):
                    economic_notes.append("focused war economy")

                # Enhanced focus analysis with descriptions
                focus_notes = []
                if current_focus:
                    focus_description = self._get_localized_focus_description(current_focus, country_tag)
                    
                    if focus_description:
                        if focus_progress > 80:
                            focus_notes.append(f"completing {focus_description}")
                        elif focus_progress > 50:
                            focus_notes.append(f"advancing {focus_description}")
                        else:
                            focus_notes.append(f"pursuing {focus_description}")
                    else:
                        focus_name = current_focus.replace('_', ' ').title()
                        focus_notes.append(f"developing {focus_name.lower()}")
                
                # Recent completed focuses with enhanced context
                if completed_focuses:
                    recent_completed = completed_focuses[-2:]  # Last 2 completed for space
                    recent_with_desc = []
                    for focus_id in recent_completed:
                        focus_desc = self._get_localized_focus_description(focus_id, country_tag)
                        focus_clean = focus_id.replace('_', ' ').title()
                        if focus_desc:
                            recent_with_desc.append(f"{focus_clean} ({focus_desc})")
                        else:
                            recent_with_desc.append(focus_clean)
                    
                    if recent_with_desc:
                        focus_notes.append(f"recently: {'; '.join(recent_with_desc)}")
                
                # Add ideology and leader information
                ideology_info = []
                if ruling_party and ruling_party != 'unknown':
                    ideology_name = ruling_party.replace('_', ' ').title()
                    ideology_info.append(f"{ideology_name}")
                
                if current_leader and current_leader not in ['Leader', 'Head of State', 'The Leader']:
                    ideology_info.append(f"led by {current_leader}")
                
                # Combine all information
                all_notes = ideology_info + political_notes + economic_notes + focus_notes
                if all_notes:
                    is_major = country_data.get('major', False) == True
                    power_indicator = "★" if is_major else "○"
                    country_summaries.append(f"{power_indicator} {ideological_country_name}: {' | '.join(all_notes)}")
                    
            # Add comprehensive summaries
            if country_summaries:
                context_parts.append("WORLD POWERS STATUS:")
                for power_info in country_summaries:
                    context_parts.append(f"  - {power_info}")
        
        # Add recent events if available
        metadata = game_data.get('metadata', {})
        recent_events = metadata.get('recent_events', [])
        if recent_events:
            context_parts.append("Recent International Developments:")
            for event in recent_events[:3]:
                if isinstance(event, dict):
                    title = event.get('title', str(event))
                    context_parts.append(f"  • {title}")
                else:
                    context_parts.append(f"  • {str(event)}")
        
        return "\n".join(context_parts) if context_parts else "General international situation developing"