#!/usr/bin/env python3
"""
Stream Twitter Generator
Optimized single-tweet generator for live streaming feeds
"""

import sys
import random
from pathlib import Path
from typing import Dict, List, Any

# Add the src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from generators.base_generator import BaseGenerator
from localization import HOI4Localizer
from persona_loader import PersonaLoader

class StreamTwitterGenerator(BaseGenerator):
    """Generates single tweets optimized for streaming overlay"""
    
    def __init__(self):
        super().__init__()
        # Initialize localizer for proper country names and focus descriptions
        self.localizer = HOI4Localizer()
        # Load basic localization files
        self.localizer.load_localization_file("countries_l_english.yml")
        self.localizer.load_localization_file("focus_l_english.yml")
        self.localizer.load_localization_file("events_l_english.yml")
        
        # Load all additional focus files for complete coverage
        import glob
        from pathlib import Path
        locale_dir = Path(__file__).parent.parent.parent / 'locale'
        focus_files = glob.glob(str(locale_dir / '*focus*l_english.yml'))
        for focus_file in focus_files:
            filename = Path(focus_file).name
            if filename != "focus_l_english.yml":  # Already loaded
                self.localizer.load_localization_file(filename)
        
        # Initialize persona loader with localizer
        self.persona_loader = PersonaLoader(localizer=self.localizer)
    
    def generate_prompt(self, game_data: Dict[str, Any], event_data: Dict = None, **kwargs) -> str:
        """Generate prompt for a single, focused tweet"""
        
        if event_data:
            context = self._build_event_context(event_data, game_data)
            event_type = self._categorize_event(event_data)
            
            # Select persona from loaded personas
            selected_persona = self._select_persona(event_type, event_data, game_data)
            
            # Add focused guidance to avoid scattered context use
            focus_guidance = self._generate_focus_guidance(event_data, game_data)
            persona_guidance = self._generate_detailed_persona_guidance(selected_persona)
            
            return f"""You are generating a single social media post from 1936 for a live news feed. Use the extensive world context below to create an authentic, informed response.

{context}

{focus_guidance}

{persona_guidance}

Generate exactly ONE authentic tweet from a 1930s perspective. React to the current event with sophisticated understanding of the broader geopolitical situation. Use period-appropriate language and capture the growing tensions of 1936.

Format: @{selected_persona['handle'][1:]}: [tweet content with hashtags]
Username: {selected_persona['name']}
Maximum 280 characters. Generate only ONE tweet, nothing else."""

        else:
            # Fallback for general world situation
            context = self._build_general_context(game_data)
            
            # Select a random persona for general commentary  
            selected_persona = self.persona_loader.get_random_persona(
                category="general", 
                game_data=game_data
            )
            persona_guidance = self._generate_detailed_persona_guidance(selected_persona)
            
            return f"""You are generating a single social media post from 1936 for a live news feed.

WORLD SITUATION:
{context}

{persona_guidance}

Generate exactly ONE tweet commenting on the current world situation from a 1930s perspective.

Format: @{selected_persona['handle'][1:]}: [tweet content with hashtags]
Username: {selected_persona['name']}
Maximum 280 characters. Use period-appropriate language and relevant hashtags.

Generate only ONE tweet, nothing else."""

    def get_max_tokens(self) -> int:
        return 300  # Increased to ensure complete responses

    def _build_event_context(self, event_data: Dict, game_data: Dict) -> str:
        """Build context for a specific event"""
        context_parts = []
        
        # Event details with full descriptions
        title = event_data.get('title', 'Major event reported')
        description = event_data.get('description', '')
        event_type = event_data.get('type', 'general')
        
        context_parts.append(f"CURRENT EVENT: {title}")
        if description:
            context_parts.append(f"EVENT DETAILS: {description}")
        context_parts.append(f"EVENT TYPE: {event_type}")
        
        # Current date for historical context
        if 'metadata' in game_data:
            date = game_data['metadata'].get('date', '1936.01.01')
            context_parts.append(f"DATE: {date}")
        
        # Add world situation summary
        context_parts.append("\n=== WORLD SITUATION SUMMARY ===")
        
        # Economic and political overview
        if 'countries' in game_data:
            major_powers = []
            economic_situations = []
            political_crises = []
            
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
                country_name = self._get_country_name(country_tag)
                country_data = country.get('data', {})
                
                # Political situation
                politics = country_data.get('politics', {})
                parties = politics.get('parties', {})
                stability = country_data.get('stability', 1.0)
                political_power = politics.get('political_power', 0)
                ruling_party = politics.get('ruling_party', 'unknown')
                
                # Economic indicators
                consumer_goods = 0
                factory_output = 0
                # Look for economic indicators in variables
                variables = country_data.get('variables', {})
                for var_name, value in variables.items():
                    if 'consumer_goods' in var_name:
                        consumer_goods = value
                    elif 'factory_output' in var_name:
                        factory_output = value
                
                # Focus details with descriptions
                focus = country_data.get('focus', {})
                current_focus = focus.get('current', '')
                focus_progress = focus.get('progress', 0)
                completed_focuses = focus.get('completed', [])
                
                # Build rich country profile
                country_profile = f"{country_tag}:"
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
                
                # Economic analysis
                economic_notes = []
                if consumer_goods > 0.25:
                    economic_notes.append("high consumer demand")
                elif consumer_goods < 0.15:
                    economic_notes.append("focused war economy")
                
                # Enhanced focus analysis with descriptions (no progress numbers)
                focus_notes = []
                if current_focus:
                    focus_name = current_focus.replace('_', ' ').title()
                    focus_description = self._get_focus_description(current_focus, country_tag)
                    
                    if focus_description:
                        if focus_progress > 80:
                            focus_notes.append(f"completing {focus_description}")
                        elif focus_progress > 50:
                            focus_notes.append(f"advancing {focus_description}")
                        else:
                            focus_notes.append(f"pursuing {focus_description}")
                    else:
                        focus_notes.append(f"developing {focus_name.lower()}")
                
                # Recent completed focuses with enhanced context
                if completed_focuses:
                    recent_completed = completed_focuses[-2:]  # Last 2 completed for space
                    recent_with_desc = []
                    for focus_id in recent_completed:
                        focus_desc = self._get_focus_description(focus_id, country_tag)
                        focus_clean = focus_id.replace('_', ' ').title()
                        if focus_desc:
                            recent_with_desc.append(f"{focus_clean} ({focus_desc})")
                        else:
                            recent_with_desc.append(focus_clean)
                    
                    if recent_with_desc:
                        focus_notes.append(f"recently: {'; '.join(recent_with_desc)}")
                
                # Combine all information
                all_notes = political_notes + economic_notes + focus_notes
                if all_notes:
                    is_major = country_data.get('major', False) == True
                    power_indicator = "★" if is_major else "○"
                    country_summaries.append(f"{power_indicator} {country_name}: {' | '.join(all_notes)}")
                    
            # Add comprehensive summaries
            if country_summaries:
                context_parts.append("WORLD POWERS STATUS:")
                for power_info in country_summaries:
                    context_parts.append(f"  - {power_info}")
        
        # Add recent events with full details
        if 'metadata' in game_data and 'recent_events' in game_data['metadata']:
            recent = game_data['metadata']['recent_events'][:5]  # More recent events
            if recent:
                context_parts.append("\nRECENT WORLD EVENTS:")
                for i, event in enumerate(recent):
                    if isinstance(event, dict):
                        evt_title = event.get('title', str(event))
                        evt_desc = event.get('description', '')
                        if evt_desc:
                            context_parts.append(f"  {i+1}. {evt_title} - {evt_desc}")
                        else:
                            context_parts.append(f"  {i+1}. {evt_title}")
                    else:
                        context_parts.append(f"  {i+1}. {str(event)}")
        
        return "\n".join(context_parts)

    def _build_general_context(self, game_data: Dict) -> str:
        """Build general world context"""
        context_parts = []
        
        # Date
        if 'metadata' in game_data:
            date = game_data['metadata'].get('date', '1936.01.01')
            context_parts.append(f"Date: {date}")
        
        # Major powers status (simplified)
        if 'countries' in game_data and game_data['countries']:
            for country in game_data['countries'][:3]:
                country_tag = country.get('tag', 'Unknown')
                country_data = country.get('data', {})
                status_notes = []
                
                # Check focus
                focus = country_data.get('focus', {}).get('current', '')
                if focus and any(keyword in focus.lower() for keyword in ['war', 'army', 'military', 'rearmament']):
                    status_notes.append("military focus")
                elif focus:
                    status_notes.append("policy development")
                
                # Check political situation
                politics = country_data.get('politics', {})
                parties = politics.get('parties', {})
                if parties:
                    fascist_pop = parties.get('fascism', {}).get('popularity', 0)
                    if fascist_pop > 20:
                        status_notes.append("rising tensions")
                
                if status_notes:
                    context_parts.append(f"{country_tag}: {', '.join(status_notes)}")
        
        return "\n".join(context_parts) or "General world situation, 1936"

    def _get_focus_description(self, focus_id: str, country_tag: str) -> str:
        """Get focus description using localization system with fallback to contextual descriptions"""
        # Try to get the focus name from localization
        localized_name = self.localizer.get_localized_text(focus_id)
        
        # If we got a localized name that's different from the focus_id, use it
        if localized_name != focus_id and not localized_name.startswith(country_tag):
            return localized_name.lower()
        
        # Fallback to contextual descriptions based on keywords
        focus_lower = focus_id.lower()
        
        if any(keyword in focus_lower for keyword in ['army', 'military', 'rearm', 'doctrine']):
            return "military modernization"
        elif any(keyword in focus_lower for keyword in ['industry', 'production', 'factory']):
            return "industrial development"
        elif any(keyword in focus_lower for keyword in ['political', 'ideology', 'party']):
            return "political restructuring"
        elif any(keyword in focus_lower for keyword in ['diplomatic', 'alliance', 'trade']):
            return "diplomatic initiatives"
        elif any(keyword in focus_lower for keyword in ['research', 'technology']):
            return "technological advancement"
        elif any(keyword in focus_lower for keyword in ['naval', 'fleet', 'submarine']):
            return "naval expansion"
        elif any(keyword in focus_lower for keyword in ['air', 'aviation', 'bomber']):
            return "air force development"
        elif any(keyword in focus_lower for keyword in ['agricultural', 'farming', 'rural']):
            return "agricultural reforms"
        else:
            # Clean up the focus name for display
            clean_name = focus_id.replace(f"{country_tag.lower()}_", "").replace("_", " ")
            return clean_name.lower()
    
    def _analyze_focus_implications(self, focus_id: str, country_tag: str) -> str:
        """Analyze strategic implications of a focus"""
        focus_lower = focus_id.lower()
        
        # Military implications
        if any(keyword in focus_lower for keyword in ['army', 'military', 'rearm', 'mobiliz', 'air', 'naval']):
            return "⚠️ MILITARY BUILDUP DETECTED"
        
        # Economic/Industrial implications  
        elif any(keyword in focus_lower for keyword in ['industry', 'production', 'factory']):
            return "📈 INDUSTRIAL EXPANSION"
            
        # Political implications
        elif any(keyword in focus_lower for keyword in ['political', 'ideology', 'party']):
            return "🏛️ POLITICAL TRANSFORMATION"
            
        # Diplomatic implications
        elif any(keyword in focus_lower for keyword in ['alliance', 'diplomatic', 'trade']):
            return "🤝 DIPLOMATIC MANEUVERING"
            
        # Territorial implications
        elif any(keyword in focus_lower for keyword in ['expansion', 'claim', 'territorial']):
            return "🗺️ TERRITORIAL AMBITIONS"
        
        return ""

    def _get_country_name(self, country_tag: str) -> str:
        """Convert country tags to readable names using localization"""
        return self.localizer.get_country_name(country_tag)

    def _generate_focus_guidance(self, event_data: Dict, game_data: Dict) -> str:
        """Generate directive guidance on what to focus on"""
        focus_options = [
            "Focus ONLY on the military implications. Ignore civilian politics.",
            "Focus ONLY on the political power struggle. Ignore economic details.",
            "Focus ONLY on one or two key countries. Don't mention minor nations.", 
            "Focus ONLY on the immediate diplomatic consequences. Ignore domestic issues.",
            "Focus ONLY on the historical significance. Keep it concise.",
            "Focus ONLY on the economic/industrial angle. Ignore political commentary.",
            "Focus ONLY on the regional impact. Don't discuss global implications.",
            "Focus ONLY on what this means for ordinary citizens. Ignore high politics."
        ]
        
        # Add length variety guidance
        length_guidance = random.choice([
            "Keep it SHORT - under 200 characters.",
            "Write a MEDIUM tweet - around 220-250 characters.", 
            "Use the FULL space - approach 280 characters with detail."
        ])
        
        # Select based on event type for some consistency
        event_type = self._categorize_event(event_data)
        if event_type == 'war':
            selected_focus = random.choice([focus_options[0], focus_options[3], focus_options[2]])
        elif event_type == 'politics': 
            selected_focus = random.choice([focus_options[1], focus_options[6], focus_options[7]])
        elif event_type == 'policy':
            selected_focus = random.choice([focus_options[5], focus_options[4], focus_options[6]])
        else:
            selected_focus = random.choice(focus_options)
        
        return f"FOCUS GUIDANCE: {selected_focus} {length_guidance}"

    def _select_persona(self, event_type: str, event_data: Dict, game_data: Dict) -> Dict:
        """Select an appropriate persona from the loaded personas"""
        
        # Try to determine relevant country from event data or game context
        target_country = self._determine_relevant_country(event_data, game_data)
        
        # Check if this event should force a leader
        force_leader = event_data.get('force_leader', False)
        
        if force_leader:
            # Force a leader persona selection
            persona = self._get_leader_persona(target_country, game_data)
        else:
            # Get persona based on event type, context, and game data
            persona = self.persona_loader.get_random_persona(
                event_type=event_type,
                category=None,  # Let it choose from any category
                country=target_country,
                game_data=game_data
            )
        
        return persona
    
    def _get_leader_persona(self, target_country: str, game_data: Dict) -> Dict:
        """Force selection of a leader persona"""
        if not target_country:
            # Pick a random major power if no specific country
            if game_data and 'countries' in game_data:
                major_powers = []
                for country in game_data['countries']:
                    country_data = country.get('data', {})
                    if country_data.get('major', False):
                        major_powers.append(country.get('tag'))
                if major_powers:
                    target_country = random.choice(major_powers)
                else:
                    target_country = 'GER'  # Ultimate fallback
            else:
                target_country = 'GER'  # Ultimate fallback
        
        # Try to get a leader template specifically
        leader_persona = self.persona_loader.get_templated_persona(
            'country_leader_official', 
            game_data, 
            target_country
        )
        
        return leader_persona
    
    def _generate_detailed_persona_guidance(self, persona: Dict) -> str:
        """Generate detailed guidance based on the selected persona"""
        guidance_parts = []
        
        # Basic persona info
        guidance_parts.append(f"PERSONA: You are {persona['name']} ({persona['handle']})")
        guidance_parts.append(f"ROLE: {persona['description']}")
        
        # Writing style and tone
        if 'writing_style' in persona:
            guidance_parts.append(f"WRITING STYLE: {persona['writing_style']}")
        if 'tone' in persona:
            guidance_parts.append(f"TONE: {persona['tone']}")
        
        # Country perspective if applicable
        if persona.get('country'):
            country_name = self._get_country_name(persona['country'])
            guidance_parts.append(f"PERSPECTIVE: Write from a {country_name} viewpoint")
        
        # Personality traits (use 1-2 random traits to keep focused)
        if 'personality_traits' in persona and persona['personality_traits']:
            selected_traits = random.sample(
                persona['personality_traits'], 
                min(2, len(persona['personality_traits']))
            )
            guidance_parts.append(f"PERSONALITY: {' '.join(selected_traits)}")
        
        return "\n".join(guidance_parts)
    
    def _determine_relevant_country(self, event_data: Dict, game_data: Dict) -> str:
        """Determine the most relevant country for persona selection"""
        
        # First, check if event data specifies a country
        if event_data and 'country' in event_data:
            return event_data['country']
        
        # Check event title/description for country mentions
        if event_data:
            title = event_data.get('title', '').lower()
            description = event_data.get('description', '').lower()
            event_text = f"{title} {description}"
            
            # Look for major power mentions in event text
            major_powers = ['germany', 'soviet', 'america', 'britain', 'france', 'italy', 'japan']
            country_mapping = {
                'germany': 'GER', 'german': 'GER',
                'soviet': 'SOV', 'russia': 'SOV', 'ussr': 'SOV', 
                'america': 'USA', 'united states': 'USA', 'american': 'USA',
                'britain': 'ENG', 'british': 'ENG', 'england': 'ENG', 'uk': 'ENG',
                'france': 'FRA', 'french': 'FRA',
                'italy': 'ITA', 'italian': 'ITA',
                'japan': 'JAP', 'japanese': 'JAP'
            }
            
            for keyword, country_code in country_mapping.items():
                if keyword in event_text:
                    return country_code
        
        # Fallback: select a random major power from the game data
        if game_data and 'countries' in game_data:
            major_powers = []
            for country in game_data['countries']:
                country_data = country.get('data', {})
                if country_data.get('major', False):
                    major_powers.append(country.get('tag'))
            
            if major_powers:
                return random.choice(major_powers)
        
        # Ultimate fallback: return None for international perspective
        return None

    def _categorize_event(self, event_data: Dict) -> str:
        """Categorize event for appropriate response tone"""
        if 'type' in event_data:
            return event_data['type']
            
        title = event_data.get('title', '').lower()
        
        if any(keyword in title for keyword in ['war', 'declare', 'attack', 'invade']):
            return 'war'
        elif any(keyword in title for keyword in ['focus', 'research', 'policy']):
            return 'policy'
        elif any(keyword in title for keyword in ['election', 'government', 'party']):
            return 'politics'
        elif any(keyword in title for keyword in ['crisis', 'tension', 'diplomatic']):
            return 'crisis'
        else:
            return 'general'