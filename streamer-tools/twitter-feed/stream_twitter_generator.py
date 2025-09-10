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
        
        # Load ALL localization files for complete coverage - speed is not important
        import glob
        from pathlib import Path
        locale_dir = Path(__file__).parent.parent.parent / 'locale'
        
        print(f"Loading all localization files from {locale_dir}")
        all_locale_files = glob.glob(str(locale_dir / '*_l_english.yml'))
        
        # Sort files to load base files first, then DLC files
        base_files = []
        dlc_files = []
        
        for locale_file in all_locale_files:
            filename = Path(locale_file).name
            # Prioritize core game files
            if any(core in filename for core in ['countries_', 'focus_', 'events_', 'core_']):
                base_files.append(filename)
            else:
                dlc_files.append(filename)
        
        # Load base files first
        for filename in sorted(base_files):
            try:
                self.localizer.load_localization_file(filename)
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}")
        
        # Then load all DLC files
        for filename in sorted(dlc_files):
            try:
                self.localizer.load_localization_file(filename)
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}")
        
        print(f"Loaded {len(self.localizer.translations)} total translations")
        
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
        
        # Add enhanced focus information if available
        if 'focus_id' in event_data:
            focus_id = event_data['focus_id']
            country_tag = event_data.get('country', '')
            progress = event_data.get('progress', 0)
            
            # Get better focus description using our enhanced method
            enhanced_description = self._get_focus_description(focus_id, country_tag)
            if enhanced_description and enhanced_description.lower() != description.lower():
                context_parts.append(f"POLICY DETAILS: {enhanced_description}")
            
            if progress > 0:
                context_parts.append(f"PROGRESS: {progress:.0f}% complete")
        
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
                country_data = country.get('data', {})
                
                # Get ideological country name and leader info
                ideological_country_name = self.persona_loader.template_processor._get_ideological_country_name(country_data, country_tag)
                
                # Political situation
                politics = country_data.get('politics', {})
                parties = politics.get('parties', {})
                stability = country_data.get('stability', 1.0)
                political_power = politics.get('political_power', 0)
                ruling_party = politics.get('ruling_party', 'unknown')
                
                # Get current leader name
                current_leader = self.persona_loader.template_processor._get_current_leader(country_data, country_tag)
                
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
        
        # Handle different focus ID formats that might be passed in
        # Sometimes we get "Sov Gain Support From Party Members" instead of "SOV_gain_support_from_party_members"
        normalized_focus_id = focus_id
        
        # If the focus_id contains spaces and starts with a country name, convert to proper format
        if ' ' in focus_id:
            parts = focus_id.split(' ', 1)
            if len(parts) == 2:
                country_part, focus_part = parts
                # Convert country name back to tag if needed
                country_map = {
                    'russia': 'SOV', 'soviet': 'SOV', 'sov': 'SOV',
                    'germany': 'GER', 'german': 'GER', 'ger': 'GER',
                    'america': 'USA', 'american': 'USA', 'usa': 'USA',
                    'britain': 'ENG', 'british': 'ENG', 'england': 'ENG', 'eng': 'ENG',
                    'france': 'FRA', 'french': 'FRA', 'fra': 'FRA',
                    'italy': 'ITA', 'italian': 'ITA', 'ita': 'ITA',
                    'japan': 'JAP', 'japanese': 'JAP', 'jap': 'JAP'
                }
                
                country_key = country_part.lower()
                if country_key in country_map:
                    country_tag = country_map[country_key]
                    # Convert focus part to proper underscore format
                    focus_part_normalized = focus_part.lower().replace(' ', '_')
                    normalized_focus_id = f"{country_tag}_{focus_part_normalized}"
        
        # Try to get the focus name from localization with the normalized ID
        localized_name = self.localizer.get_localized_text(normalized_focus_id)
        
        # If we got a localized name that's different from the focus_id, use it
        if localized_name != normalized_focus_id and localized_name != focus_id:
            return localized_name.lower()
        
        # Try original focus_id as well
        if normalized_focus_id != focus_id:
            localized_original = self.localizer.get_localized_text(focus_id)
            if localized_original != focus_id:
                return localized_original.lower()
        
        # Fallback to contextual descriptions based on keywords
        focus_lower = focus_id.lower()
        
        # Enhanced keyword matching for better descriptions
        if any(keyword in focus_lower for keyword in ['party', 'support', 'members', 'political_power']):
            return "consolidating party support"
        elif any(keyword in focus_lower for keyword in ['purge', 'eliminate', 'opposition']):
            return "eliminating political opposition"  
        elif any(keyword in focus_lower for keyword in ['army', 'military', 'rearm', 'doctrine', 'officer']):
            return "military modernization"
        elif any(keyword in focus_lower for keyword in ['industry', 'production', 'factory', 'five_year']):
            return "industrial development"
        elif any(keyword in focus_lower for keyword in ['collectiv', 'agricultural', 'farming', 'rural']):
            return "agricultural collectivization"
        elif any(keyword in focus_lower for keyword in ['diplomatic', 'alliance', 'trade', 'foreign']):
            return "diplomatic initiatives"
        elif any(keyword in focus_lower for keyword in ['research', 'technology', 'innovation']):
            return "technological advancement"
        elif any(keyword in focus_lower for keyword in ['naval', 'fleet', 'submarine', 'navy']):
            return "naval expansion"
        elif any(keyword in focus_lower for keyword in ['air', 'aviation', 'bomber', 'fighter']):
            return "air force development"
        elif any(keyword in focus_lower for keyword in ['infrastructure', 'construction', 'building']):
            return "infrastructure development"
        elif any(keyword in focus_lower for keyword in ['propaganda', 'media', 'information']):
            return "propaganda campaigns"
        else:
            # Clean up the focus name for display - handle both formats
            if normalized_focus_id != focus_id:
                # Use the normalized version for cleaning
                clean_name = normalized_focus_id.replace(f"{country_tag.lower()}_", "").replace("_", " ")
            else:
                # Clean the original
                clean_name = focus_id.replace(f"{country_tag.lower()}_", "").replace("_", " ").replace(f"{country_tag} ", "")
            
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
        
        # Store context for template processing
        self._last_game_data = game_data
        self._last_target_country = target_country
        
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
        # Process any remaining template variables in the persona
        processed_persona = self._ensure_persona_templates_processed(persona)
        
        guidance_parts = []
        
        # Basic persona info
        guidance_parts.append(f"PERSONA: You are {processed_persona['name']} ({processed_persona['handle']})")
        guidance_parts.append(f"ROLE: {processed_persona['description']}")
        
        # Writing style and tone
        if 'writing_style' in processed_persona:
            guidance_parts.append(f"WRITING STYLE: {processed_persona['writing_style']}")
        if 'tone' in processed_persona:
            guidance_parts.append(f"TONE: {processed_persona['tone']}")
        
        # Country perspective if applicable
        if processed_persona.get('country'):
            country_name = self._get_country_name(processed_persona['country'])
            guidance_parts.append(f"PERSPECTIVE: Write from a {country_name} viewpoint")
        
        # Personality traits (use 1-2 random traits to keep focused)
        if 'personality_traits' in processed_persona and processed_persona['personality_traits']:
            selected_traits = random.sample(
                processed_persona['personality_traits'], 
                min(2, len(processed_persona['personality_traits']))
            )
            guidance_parts.append(f"PERSONALITY: {' '.join(selected_traits)}")
        
        return "\n".join(guidance_parts)
    
    def _ensure_persona_templates_processed(self, persona: Dict) -> Dict:
        """Ensure that any template variables in persona are properly processed"""
        # Check if persona contains template variables
        persona_str = str(persona)
        if '{{' not in persona_str:
            return persona  # No templates to process
        
        # We need to process templates - but we need context
        # Get context from last known game data (this is a fallback)
        if hasattr(self, '_last_game_data') and hasattr(self, '_last_target_country'):
            # Process with known context
            return self.persona_loader.template_processor.process_persona_template(
                persona, self._last_game_data, self._last_target_country
            )
        else:
            # Clean up templates with fallback values
            import re
            processed_persona = {}
            for key, value in persona.items():
                if isinstance(value, str):
                    # Replace common template variables with fallbacks
                    processed_value = value
                    processed_value = re.sub(r'\{\{country_name\}\}', 'International', processed_value)
                    processed_value = re.sub(r'\{\{country_tag\}\}', 'INT', processed_value)
                    processed_value = re.sub(r'\{\{country_adjective\}\}', 'international', processed_value)
                    processed_value = re.sub(r'\{\{current_leader\}\}', 'leadership', processed_value)
                    processed_value = re.sub(r'\{\{ruling_ideology\}\}', 'political', processed_value)
                    processed_value = re.sub(r'\{\{ideology_adjective\}\}', 'political', processed_value)
                    processed_value = re.sub(r'\{\{current_focus\}\}', 'national priorities', processed_value)
                    processed_value = re.sub(r'\{\{[^}]+\}\}', '[details]', processed_value)  # Any remaining
                    processed_persona[key] = processed_value
                else:
                    processed_persona[key] = value
            return processed_persona
    
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
        """Categorize event for appropriate response tone - broad categories for variety"""
        if 'type' in event_data:
            event_type = event_data['type']
            # Map specific focus events to broader categories for more persona variety
            if event_type.startswith('focus_'):
                return 'politics'  # Focus events are political decisions
            return event_type
            
        title = event_data.get('title', '').lower()
        
        if any(keyword in title for keyword in ['war', 'declare', 'attack', 'invade']):
            return 'war'
        elif any(keyword in title for keyword in ['focus', 'research', 'policy', 'pursue']):
            return 'politics'  # Broader politics category instead of restrictive "policy"
        elif any(keyword in title for keyword in ['election', 'government', 'party']):
            return 'politics'
        elif any(keyword in title for keyword in ['crisis', 'tension', 'diplomatic']):
            return 'crisis'
        else:
            return 'general'