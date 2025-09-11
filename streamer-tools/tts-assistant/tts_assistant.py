#!/usr/bin/env python3
"""
TTS Assistant for HOI4 Streaming
AI-powered German assistant with dynamic personality that provides gameplay commentary
and responds to voice commands with context-aware assistance
"""

import json
import time
import sys
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict

# Add src directory to path for game data integration
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

try:
    from ai_client import AIClient
    from game_data_loader import GameDataLoader
    from localization import HOI4Localizer
    from game_event_service import GameEventService, GameEvent
    AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI components not available: {e}")
    AI_AVAILABLE = False

from personality_generator import PersonalityGenerator, AssistantPersonality

class TTSAssistant:
    """Main TTS Assistant service with personality and game data integration"""
    
    def __init__(self, data_path: str = None, config_path: str = None):
        if data_path is None:
            data_path = project_root / 'data' / 'game_data.json'
        if config_path is None:
            config_path = Path(__file__).parent / 'config.json'
        
        self.data_path = Path(data_path)
        self.config_path = Path(config_path)
        self.personality_file = Path(__file__).parent / 'current_personality.json'
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize personality (persistent across sessions)
        self.personality = self._load_or_generate_personality()
        
        # Initialize game data components
        self.game_data_loader = None
        self.localization = None
        self.current_game_data = None
        
        if AI_AVAILABLE:
            self.ai_client = AIClient()
            self.game_data_loader = GameDataLoader(str(self.data_path))
            self.localization = HOI4Localizer()
            # Load all localization files for complete coverage
            print(f"[{self.personality.name}] Loading all localization files...")
            self.localization.load_all_files()
            print(f"[{self.personality.name}] Localization loaded!")
            self.game_event_service = GameEventService(self.localization)
            print(f"[{self.personality.name}] AI components initialized successfully!")
            # Try to load game data immediately
            try:
                self.load_game_data()  # Use our direct loading method
                if self.current_game_data:
                    print(f"[{self.personality.name}] Game data loaded successfully!")
                else:
                    print(f"[{self.personality.name}] Could not load game data")
            except Exception as e:
                print(f"[{self.personality.name}] Could not load game data: {e}")
        else:
            self.ai_client = None
            self.game_event_service = None
            print(f"[{self.personality.name}] AI components not available - using fallback responses")
        
        # Conversation context for continuity
        self.conversation_history = []
        self.max_history = 10
        
        # Chat logging
        self.chat_log_file = project_root / 'data' / 'tts_chat_log.txt'
        self.prompt_log_file = project_root / 'data' / 'tts_prompt_log.txt'
        
        # Game state tracking
        self.last_game_state = {}
        self.notable_changes = []
        
        print(f"\n=== TTS Assistant Initialized ===")
        print(f"Name: {self.personality.name}")
        print(f"Personality: {self.personality.personality_type}")
        print(f"Backstory: {self.personality.backstory}")
        print(f"Voice Style: {self.personality.voice_style}")
        print(f"Sample Catchphrase: \"{random.choice(self.personality.catchphrases)}\"")
        print("=" * 40)
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                "response_settings": {
                    "max_response_length": 200,
                    "personality_strength": 0.8,
                    "include_game_context": True
                },
                "voice_settings": {
                    "speaking_rate": 1.0,
                    "personality_emphasis": True
                }
            }
    
    def _load_or_generate_personality(self) -> AssistantPersonality:
        """Load existing personality or generate new one"""
        # Check if personality file exists
        if self.personality_file.exists():
            try:
                with open(self.personality_file, 'r', encoding='utf-8') as f:
                    personality_data = json.load(f)
                    
                personality = AssistantPersonality(**personality_data)
                print(f"Loaded existing personality: {personality.name} ({personality.personality_type})")
                return personality
                
            except Exception as e:
                print(f"Error loading personality: {e}")
        
        # Generate new personality
        generator = PersonalityGenerator()
        personality = generator.generate_personality()
        
        # Save for persistence
        self._save_personality(personality)
        print(f"Generated new personality: {personality.name} ({personality.personality_type})")
        
        return personality
    
    def _save_personality(self, personality: AssistantPersonality):
        """Save personality to file for persistence"""
        try:
            with open(self.personality_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(personality), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving personality: {e}")
    
    def load_game_data(self) -> Optional[Dict]:
        """Load game data from JSON file directly"""
        try:
            # Use direct JSON loading like other streaming tools
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.current_game_data = json.load(f)
                
                if hasattr(self, 'notable_changes'):
                    self.notable_changes.append("Game data loaded for the first time")
                return self.current_game_data
            else:
                print(f"Game data file not found: {self.data_path}")
                return None
                
        except Exception as e:
            print(f"Error loading game data: {e}")
            return None
    
    def analyze_game_changes(self, new_data: Dict) -> List[str]:
        """Analyze what has changed in the game since last check"""
        changes = []
        
        if not self.last_game_state:
            self.last_game_state = new_data
            return ["Game data loaded for the first time"]
        
        # Check for major country changes (handle different data structures)
        if 'countries' in new_data and 'countries' in self.last_game_state:
            try:
                # Handle dict structure: {"countries": {"GER": {...}}}
                if isinstance(new_data['countries'], dict) and isinstance(self.last_game_state['countries'], dict):
                    for country_tag, country_data in new_data['countries'].items():
                        if country_tag in self.last_game_state['countries']:
                            old_country = self.last_game_state['countries'][country_tag]
                            self._check_country_changes(country_tag, country_data, old_country, changes)
                
                # Handle list structure: {"countries": [{"tag": "GER", "data": {...}}]}
                elif isinstance(new_data['countries'], list) and isinstance(self.last_game_state['countries'], list):
                    # Convert lists to dicts for comparison
                    old_countries = {c.get('tag'): c.get('data') for c in self.last_game_state['countries'] if c.get('tag')}
                    new_countries = {c.get('tag'): c.get('data') for c in new_data['countries'] if c.get('tag')}
                    
                    for country_tag, country_data in new_countries.items():
                        if country_tag in old_countries:
                            old_country = old_countries[country_tag]
                            self._check_country_changes(country_tag, country_data, old_country, changes)
                            
            except Exception as e:
                print(f"Error analyzing game changes: {e}")
                # Continue without changes
        
        self.last_game_state = new_data
        return changes
    
    def _check_country_changes(self, country_tag: str, country_data: dict, old_country: dict, changes: list):
        """Helper method to check for changes in a country's data"""
        try:
            # Check for focus changes
            if 'national_focus' in country_data and 'national_focus' in old_country:
                old_focus = old_country['national_focus'].get('current_focus')
                new_focus = country_data['national_focus'].get('current_focus')
                
                if old_focus != new_focus and new_focus:
                    country_name = country_data.get('name', country_tag)
                    changes.append(f"{country_name} is now working on: {new_focus}")
            
            # Also check alternative focus structure
            elif 'focus' in country_data and 'focus' in old_country:
                old_focus = old_country['focus'].get('current')
                new_focus = country_data['focus'].get('current')
                
                if old_focus != new_focus and new_focus:
                    country_name = country_data.get('name', country_tag)
                    changes.append(f"{country_name} is now working on: {new_focus}")
            
            # Check for political changes
            if 'ruling_party' in country_data and 'ruling_party' in old_country:
                if old_country['ruling_party'] != country_data['ruling_party']:
                    country_name = country_data.get('name', country_tag)
                    changes.append(f"{country_name} changed ruling party to {country_data['ruling_party']}")
        except Exception as e:
            print(f"Error checking changes for {country_tag}: {e}")
    
    def get_game_context_summary(self) -> str:
        """Get a summary of current game state for AI context"""
        if not self.current_game_data:
            return "No game data available"
        
        context_parts = []
        
        try:
            # Add date
            if isinstance(self.current_game_data, dict) and 'metadata' in self.current_game_data:
                metadata = self.current_game_data['metadata']
                if isinstance(metadata, dict) and 'date' in metadata:
                    context_parts.append(f"Date: {metadata['date']}")
        except Exception as e:
            print(f"Debug: Error getting date: {e}")
        
        # Add player country info
        player_data = None
        player_tag = None
        
        try:
            # Get player tag from metadata
            if isinstance(self.current_game_data, dict) and 'metadata' in self.current_game_data:
                metadata = self.current_game_data['metadata']
                if isinstance(metadata, dict):
                    player_tag = metadata.get('player')
            
            # Find player country data
            if player_tag and isinstance(self.current_game_data, dict) and 'countries' in self.current_game_data:
                countries = self.current_game_data['countries']
                
                if isinstance(countries, dict):
                    # Structure: {"countries": {"TAG": {...}}}
                    player_data = countries.get(player_tag)
                elif isinstance(countries, list):
                    # Structure: {"countries": [{"tag": "TAG", "data": {...}}]}
                    for country in countries:
                        if isinstance(country, dict) and country.get('tag') == player_tag:
                            player_data = country.get('data')
                            break
        except Exception as e:
            print(f"Debug: Error getting country data: {e}")
        
        try:
            if player_data and isinstance(player_data, dict):
                # Try to get leader name from politics data
                leader = 'Unknown Leader'
                
                try:
                    politics = player_data.get('politics', {})
                    if isinstance(politics, dict) and 'parties' in politics:
                        parties = politics['parties']
                        ruling_party = politics.get('ruling_party')
                        
                        if ruling_party and ruling_party in parties:
                            party_data = parties[ruling_party]
                            if 'country_leader' in party_data and isinstance(party_data['country_leader'], list):
                                if len(party_data['country_leader']) > 0:
                                    leader_data = party_data['country_leader'][0]
                                    if 'character' in leader_data and 'name' in leader_data['character']:
                                        leader = leader_data['character']['name']
                except Exception as e:
                    print(f"Debug: Error getting leader: {e}")
                
                if isinstance(leader, str) and leader != 'Unknown Leader' and player_tag:
                    # Localize leader name
                    localized_leader = self.localization.get_localized_text(leader) if hasattr(self, 'localization') else leader
                    # Localize country name
                    country_name = self.localization.get_localized_text(player_tag) if hasattr(self, 'localization') else player_tag
                    context_parts.append(f"{country_name} Leader: {localized_leader}")
                
                # Try to get current focus
                try:
                    current_focus = None
                    if isinstance(player_data.get('national_focus'), dict):
                        current_focus = player_data['national_focus'].get('current_focus')
                    elif isinstance(player_data.get('focus'), dict):
                        current_focus = player_data['focus'].get('current')
                    
                    if current_focus and isinstance(current_focus, str):
                        # Localize focus name
                        localized_focus = self.localization.get_localized_text(current_focus) if hasattr(self, 'localization') else current_focus
                        context_parts.append(f"Current Focus: {localized_focus}")
                except Exception as e:
                    print(f"Debug: Error getting focus: {e}")
                
                # Try to get political data
                try:
                    stability = player_data.get('stability')
                    war_support = player_data.get('war_support')
                    
                    if (stability is not None and war_support is not None and 
                        isinstance(stability, (int, float)) and isinstance(war_support, (int, float))):
                        # Convert to percentage if needed (data might already be 0-1 or 0-100)
                        # Convert to descriptive text instead of percentages
                        if stability > 0.6:
                            stability_text = "stable"
                        elif stability > 0.4:
                            stability_text = "somewhat unstable"
                        else:
                            stability_text = "unstable"
                        
                        if war_support > 0.6:
                            war_text = "strong war support"
                        elif war_support > 0.4:
                            war_text = "mixed war support"
                        else:
                            war_text = "war-weary"
                            
                        context_parts.append(f"Situation: {stability_text}, {war_text}")
                except Exception as e:
                    print(f"Debug: Error getting politics: {e}")
                    
        except Exception as e:
            print(f"Debug: Error processing player data: {e}")
        
        # Add recent changes
        try:
            if self.notable_changes and isinstance(self.notable_changes, list):
                recent_changes = [str(change) for change in self.notable_changes[-3:] if change]
                if recent_changes:
                    context_parts.append(f"Recent changes: {', '.join(recent_changes)}")
        except Exception as e:
            print(f"Debug: Error getting recent changes: {e}")
        
        return " | ".join(context_parts) if context_parts else "Basic game state available"
    
    def _get_detailed_game_context(self) -> str:
        """Get detailed game context focused on player nation"""
        if not self.current_game_data:
            return "No game data available"
        
        context_lines = []
        metadata = self.current_game_data.get('metadata', {})
        
        # Add current date
        if 'date' in metadata:
            context_lines.append(f"Current Date: {metadata['date']}")
        
        # Focus on player nation
        player_tag = metadata.get('player')
        if player_tag:
            # Find player nation data
            player_country = None
            if 'countries' in self.current_game_data:
                for country in self.current_game_data['countries']:
                    if country.get('tag') == player_tag:
                        player_country = country.get('data', {})
                        break
            
            if player_country:
                # Get localized country name
                country_name = self.localization.get_localized_text(player_tag) if hasattr(self, 'localization') else player_tag
                context_lines.append(f"\n=== YOUR NATION: {country_name} ===")
                
                # Get leader info
                politics = player_country.get('politics', {})
                if politics and 'parties' in politics:
                    ruling_party = politics.get('ruling_party')
                    if ruling_party and ruling_party in politics['parties']:
                        party_data = politics['parties'][ruling_party]
                        if 'country_leader' in party_data and party_data['country_leader']:
                            leader_data = party_data['country_leader'][0]
                            if 'character' in leader_data and 'name' in leader_data['character']:
                                leader_name_key = leader_data['character']['name']
                                # Try to get localized leader name
                                leader_name = self.localization.get_localized_text(leader_name_key) if hasattr(self, 'localization') else leader_name_key
                                ideology = leader_data.get('ideology', ruling_party)
                                # Localize ideology
                                ideology_localized = self.localization.get_localized_text(ideology) if hasattr(self, 'localization') else ideology
                                context_lines.append(f"Leader: {leader_name}")
                                context_lines.append(f"Government: {ideology_localized}")
                
                # Current focus
                focus_data = player_country.get('focus', {})
                if focus_data and 'current' in focus_data:
                    current_focus = focus_data['current']
                    # Get localized focus name and description
                    focus_name = self.localization.get_localized_text(current_focus) if hasattr(self, 'localization') else current_focus
                    focus_desc_key = f"{current_focus}.desc"
                    focus_desc = self.localization.get_localized_text(focus_desc_key) if hasattr(self, 'localization') else ""
                    
                    progress = focus_data.get('progress', 0)
                    if progress < 25:
                        progress_text = "just started"
                    elif progress < 50:
                        progress_text = "making progress"
                    elif progress < 75:
                        progress_text = "halfway complete"
                    else:
                        progress_text = "nearly finished"
                    
                    context_lines.append(f"Current Focus: {focus_name} ({progress_text})")
                    if focus_desc and focus_desc != focus_desc_key:
                        context_lines.append(f"Focus Goal: {focus_desc}")
                
                # Political situation (text instead of numbers)
                stability = player_country.get('stability')
                war_support = player_country.get('war_support')
                
                if stability is not None:
                    if stability > 0.8:
                        stability_text = "very stable"
                    elif stability > 0.6:
                        stability_text = "stable"
                    elif stability > 0.4:
                        stability_text = "somewhat unstable"
                    elif stability > 0.2:
                        stability_text = "unstable"
                    else:
                        stability_text = "very unstable"
                    context_lines.append(f"Political Stability: {stability_text}")
                
                if war_support is not None:
                    if war_support > 0.8:
                        war_text = "strong war support"
                    elif war_support > 0.6:
                        war_text = "moderate war support"
                    elif war_support > 0.4:
                        war_text = "mixed feelings about war"
                    elif war_support > 0.2:
                        war_text = "war-weary population"
                    else:
                        war_text = "strong anti-war sentiment"
                    context_lines.append(f"Public Opinion: {war_text}")
                
                # National spirits (localized with descriptions, limit to 2-3 most important)
                ideas = politics.get('ideas', [])
                if ideas and isinstance(ideas, list):
                    spirit_descriptions = []
                    for idea in ideas[:3]:
                        if isinstance(idea, str):
                            # Try to get the spirit name/title
                            spirit_name = self.localization.get_localized_text(idea) if hasattr(self, 'localization') else idea
                            # Try to get the spirit description
                            spirit_desc_key = f"{idea}.desc"
                            spirit_desc = self.localization.get_localized_text(spirit_desc_key) if hasattr(self, 'localization') else ""
                            
                            # Use description if available, otherwise use name
                            if spirit_desc and spirit_desc != spirit_desc_key:
                                spirit_descriptions.append(spirit_desc)
                            elif spirit_name != idea:
                                spirit_descriptions.append(spirit_name)
                            elif len(spirit_descriptions) == 0:  # Always include at least one
                                spirit_descriptions.append(idea)
                    
                    if spirit_descriptions:
                        context_lines.append(f"National Situation: {'; '.join(spirit_descriptions)}")
        
        # Add brief world overview (just major power count)
        if isinstance(self.current_game_data, dict) and 'countries' in self.current_game_data:
            countries = self.current_game_data['countries']
            if isinstance(countries, list):
                major_count = sum(1 for c in countries if isinstance(c, dict) and c.get('data', {}).get('major'))
                context_lines.append(f"\nWorld Status: {major_count} major powers active")
        
        return "\n".join(context_lines) if context_lines else "Basic game state available"
    
    def respond_to_user(self, user_input: str) -> str:
        """Generate AI response to user input with personality and game context"""
        if not self.ai_client:
            return self._generate_fallback_response(user_input)
        
        # Load current game data
        self.load_game_data()
        
        # Analyze game changes (temporarily disabled for debugging)
        if self.current_game_data:
            try:
                changes = self.analyze_game_changes(self.current_game_data)
                self.notable_changes.extend(changes)
                # Keep only recent changes
                self.notable_changes = self.notable_changes[-10:]
            except Exception as e:
                print(f"Debug: Error in analyze_game_changes: {e}")
                # Continue without game analysis
        
        # Build context for AI
        try:
            game_context = self._get_detailed_game_context()
            if not game_context or game_context.strip() == "Basic game state available":
                print(f"Debug: GameEventService returned basic context, trying fallback")
                game_context = self.get_game_context_summary()
        except Exception as e:
            print(f"Debug: Error in get_detailed_game_context: {e}")
            # Try fallback context
            try:
                game_context = self.get_game_context_summary()
            except Exception as e2:
                print(f"Debug: Error in fallback context: {e2}")
                game_context = "Game context unavailable"
        
        # Create personality-driven prompt
        prompt = self._create_response_prompt(user_input, game_context)
        
        try:
            # Log the prompt
            self._log_prompt(user_input, prompt, game_context)
            
            response = self.ai_client.generate_text(
                prompt=prompt,
                max_tokens=self.config.get('response_settings', {}).get('max_response_length', 200),
                temperature=0.9,
                report_type="tts_assistant_response"
            )
            
            if response and response.strip():
                # Clean the response to remove any actions
                cleaned_response = self._clean_actions_from_response(response.strip())
                # Add to conversation history
                self._add_to_history(user_input, cleaned_response)
                # Log the chat exchange
                self._log_chat(user_input, cleaned_response)
                return cleaned_response
            else:
                fallback = self._generate_fallback_response(user_input)
                cleaned_fallback = self._clean_actions_from_response(fallback)
                self._log_chat(user_input, cleaned_fallback, is_fallback=True)
                return cleaned_fallback
                
        except Exception as e:
            print(f"Error generating AI response: {e}")
            fallback = self._generate_fallback_response(user_input)
            cleaned_fallback = self._clean_actions_from_response(fallback)
            self._log_chat(user_input, cleaned_fallback, is_fallback=True)
            return cleaned_fallback
    
    def _create_response_prompt(self, user_input: str, game_context: str) -> str:
        """Create AI prompt with personality and context"""
        
        # Build personality context
        personality_context = f"""
ASSISTANT PERSONALITY:
- Name: {self.personality.name}
- Type: {self.personality.personality_type}
- Traits: {', '.join(self.personality.traits)}
- Backstory: {self.personality.backstory}
- Voice Style: {self.personality.voice_style}
- Response Style: {self.personality.response_style}
- Quirks: {', '.join(self.personality.quirks)}
- Typical Phrases: {', '.join(self.personality.catchphrases[:3])}
"""
        
        # Recent conversation context
        conversation_context = ""
        if self.conversation_history:
            recent = self.conversation_history[-3:]  # Last 3 exchanges
            conversation_context = "RECENT CONVERSATION:\n"
            for user_msg, assistant_msg in recent:
                conversation_context += f"User: {user_msg}\nAssistant: {assistant_msg}\n"
        
        prompt = f"""You are {self.personality.name}, a German military assistant in 1936 with the personality type '{self.personality.personality_type}'.

{personality_context}

CURRENT GAME SITUATION:
{game_context}

{conversation_context}

USER: "{user_input}"

CRITICAL INSTRUCTIONS FOR {self.personality.name.upper()}:
- You must ONLY provide spoken dialogue - pure speech only
- NEVER use asterisks (*action*), brackets [action], or parentheses (action)  
- NEVER describe actions, gestures, sounds, or physical movements
- Do NOT whistle, count, tilt head, squint, or any other actions
- Simply speak your response as dialogue only
- Stay in character as {self.personality.personality_type}: {', '.join(self.personality.traits)}
- Reference the current game situation when relevant
- Use your typical speech patterns: "{random.choice(self.personality.catchphrases)}"
- Maximum 1-2 sentences of pure spoken dialogue
- Example: "Ja, but which enemy are we fighting again?" NOT "*counts fingers* Ja, but..."

{self.personality.name} responds with pure speech:"""
        
        return prompt
    
    def _clean_actions_from_response(self, response: str) -> str:
        """Remove any action descriptions from AI response to keep only dialogue"""
        import re
        
        # Remove content in asterisks: *action*
        response = re.sub(r'\*[^*]*\*', '', response)
        
        # Remove content in brackets: [action]
        response = re.sub(r'\[[^\]]*\]', '', response)
        
        # Remove content in parentheses that looks like actions: (action)
        # But keep normal parentheses with speech content
        response = re.sub(r'\([^)]*(?:whistle|count|tilt|squint|gesture|nod|shrug|sigh)[^)]*\)', '', response, flags=re.IGNORECASE)
        
        # Remove common action patterns even without brackets
        action_patterns = [
            r'\b(?:whistles?|whistling)\b[^.!?]*',
            r'\b(?:counts?|counting)\b[^.!?]*fingers?[^.!?]*',
            r'\b(?:tilts?|tilting)\b[^.!?]*head[^.!?]*',
            r'\b(?:squints?|squinting)\b[^.!?]*',
            r'\b(?:adjusts?|adjusting)\b[^.!?]*glasses[^.!?]*',
            r'\b(?:gestures?|gesturing)\b[^.!?]*',
            r'\b(?:nods?|nodding)\b[^.!?]*',
            r'\b(?:shrugs?|shrugging)\b[^.!?]*',
            r'\b(?:sighs?|sighing)\b[^.!?]*'
        ]
        
        for pattern in action_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # Clean up extra spaces and punctuation
        response = re.sub(r'\s+', ' ', response)  # Multiple spaces to single
        response = re.sub(r'\s+([.!?])', r'\1', response)  # Space before punctuation
        response = re.sub(r'([.!?])\s*([.!?])', r'\1', response)  # Multiple punctuation
        
        # Remove leading/trailing whitespace and empty quotes
        response = response.strip()
        response = response.strip('"\'')
        
        return response
    
    def _generate_fallback_response(self, user_input: str) -> str:
        """Generate fallback response when AI is not available"""
        # Use personality-based templates
        fallback_responses = {
            "scared": [
                f"Oh mein Gott, {user_input}? That sounds very dangerous...",
                "I'm not sure about this, but if you insist...",
                "Are you absolutely certain this is wise?"
            ],
            "overeager": [
                f"Ja ja! {user_input} sounds absolutely brilliant!",
                "What an excellent idea! I am so excited!",
                "This will be glorious, mein commander!"
            ],
            "sarcastic": [
                f"Oh yes, {user_input}... how wonderfully original...",
                "What a fascinating request... of course...",
                "Certainly, that sounds like a brilliant plan..."
            ],
            "confused": [
                f"Wait, {user_input}? I don't quite understand...",
                "Could you explain that again? I'm a bit lost...",
                "Which part of the war does this relate to?"
            ],
            "dramatic": [
                f"Ach! {user_input}! What magnificent drama!",
                "The gods themselves witness your strategy!",
                "This shall be remembered in the annals of history!"
            ],
            "pedantic": [
                f"Regarding {user_input}, we must follow proper protocol...",
                "According to regulations, we should...",
                "That's not technically how we're supposed to..."
            ],
            "lazy": [
                f"*yawn* {user_input}? Do we really have to?",
                "That sounds like a lot of work...",
                "Can't we just... take a break first?"
            ],
            "superstitious": [
                f"The omens are unclear about {user_input}...",
                "We should consult the signs first...",
                "I sense bad luck in this plan..."
            ]
        }
        
        responses = fallback_responses.get(
            self.personality.personality_type,
            [f"Interesting, {user_input}... let me think about this..."]
        )
        
        return random.choice(responses)
    
    def _add_to_history(self, user_input: str, assistant_response: str):
        """Add exchange to conversation history"""
        self.conversation_history.append((user_input, assistant_response))
        
        # Keep only recent history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def _log_chat(self, user_input: str, assistant_response: str, is_fallback: bool = False):
        """Log chat exchange to file"""
        try:
            # Ensure data directory exists
            self.chat_log_file.parent.mkdir(exist_ok=True)
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            fallback_marker = " [FALLBACK]" if is_fallback else ""
            
            with open(self.chat_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n[{timestamp}] === Chat Exchange ===\n")
                f.write(f"Assistant: {self.personality.name} ({self.personality.personality_type})\n")
                f.write(f"User: {user_input}\n")
                f.write(f"Assistant{fallback_marker}: {assistant_response}\n")
                f.write("-" * 50 + "\n")
        except Exception as e:
            print(f"Error logging chat: {e}")
    
    def _log_prompt(self, user_input: str, prompt: str, game_context: str):
        """Log AI prompt to file for debugging"""
        try:
            # Ensure data directory exists
            self.prompt_log_file.parent.mkdir(exist_ok=True)
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.prompt_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n[{timestamp}] === AI Prompt ===\n")
                f.write(f"Assistant: {self.personality.name} ({self.personality.personality_type})\n")
                f.write(f"User Input: {user_input}\n")
                f.write(f"Game Context: {game_context}\n")
                f.write(f"Full Prompt:\n{prompt}\n")
                f.write("=" * 80 + "\n")
        except Exception as e:
            print(f"Error logging prompt: {e}")
    
    def provide_game_commentary(self) -> Optional[str]:
        """Generate unprompted commentary about current game state"""
        self.load_game_data()
        
        if not self.current_game_data:
            return None
        
        # Check for interesting developments
        changes = self.analyze_game_changes(self.current_game_data)
        
        if not changes:
            # Generate general commentary
            return self._generate_general_commentary()
        
        # Comment on specific changes
        change = random.choice(changes)
        
        if self.ai_client:
            return self.respond_to_user(f"I notice that {change}. What do you think about this?")
        else:
            personality_reactions = {
                "scared": f"Oh no! {change}... this makes me very nervous...",
                "overeager": f"Excellent! {change}! This is going perfectly!",
                "sarcastic": f"Oh wonderful... {change}... how delightful...",
                "confused": f"Wait, {change}? I don't understand why this happened...",
                "dramatic": f"Behold! {change}! What a momentous development!",
                "pedantic": f"According to my records, {change}. This requires documentation...",
                "lazy": f"So {change}... do we really need to do anything about it?",
                "superstitious": f"The spirits warned me... {change} was foretold..."
            }
            
            return personality_reactions.get(
                self.personality.personality_type,
                f"I see that {change}. How interesting..."
            )
    
    def _generate_general_commentary(self) -> str:
        """Generate general commentary when no specific changes occurred"""
        general_comments = {
            "scared": [
                "Everything seems quiet... too quiet... I don't like it...",
                "Are we sure we're not missing something important?",
                "This peaceful moment makes me very nervous..."
            ],
            "overeager": [
                "What should we conquer next? I'm so excited!",
                "The war machine is running smoothly! Magnificent!",
                "I can barely contain my enthusiasm for our next move!"
            ],
            "sarcastic": [
                "How thrilling... another peaceful moment in our glorious campaign...",
                "Oh good, we're just... sitting here... how strategic...",
                "I'm sure the enemy is terrified of our inactivity..."
            ],
            "confused": [
                "What exactly are we waiting for again?",
                "Is this the part where we invade someone?",
                "I've forgotten what our main objective was..."
            ],
            "dramatic": [
                "The calm before the storm... I can feel it in my bones!",
                "Destiny awaits us in the shadows of tomorrow!",
                "What epic tales shall unfold from this moment!"
            ],
            "pedantic": [
                "All systems are operating within normal parameters...",
                "Current status: awaiting further orders as per protocol...",
                "Everything is properly documented and filed..."
            ],
            "lazy": [
                "Nice and quiet... this is perfect for a little nap...",
                "No urgent business... excellent... time to relax...",
                "Maybe we can just... not do anything for a while?"
            ],
            "superstitious": [
                "The stars are aligned... but for what purpose?",
                "I sense great changes coming on the winds...",
                "The ancestors whisper of momentous events ahead..."
            ]
        }
        
        comments = general_comments.get(self.personality.personality_type, ["All seems well..."])
        return random.choice(comments)
    
    def reset_personality(self):
        """Generate a completely new personality (for testing/restart)"""
        if self.personality_file.exists():
            self.personality_file.unlink()  # Delete current personality file
        
        generator = PersonalityGenerator()
        self.personality = generator.generate_personality()
        self._save_personality(self.personality)
        
        # Clear conversation history
        self.conversation_history = []
        self.notable_changes = []
        
        print(f"\n=== NEW PERSONALITY GENERATED ===")
        print(f"Name: {self.personality.name}")
        print(f"Type: {self.personality.personality_type}")
        print(f"Backstory: {self.personality.backstory}")
        print("=" * 40)

def test_assistant():
    """Test the TTS Assistant"""
    assistant = TTSAssistant()
    
    print(f"\n=== Testing {assistant.personality.name} ===")
    
    test_inputs = [
        "What should I do next?",
        "Should we invade France?",
        "How are things looking?",
        "What do you think about our current strategy?",
        "Any suggestions for our military?"
    ]
    
    for user_input in test_inputs:
        print(f"\nUser: {user_input}")
        response = assistant.respond_to_user(user_input)
        print(f"{assistant.personality.name}: {response}")
        time.sleep(1)  # Brief pause between responses
    
    print(f"\n=== Commentary Test ===")
    commentary = assistant.provide_game_commentary()
    if commentary:
        print(f"{assistant.personality.name}: {commentary}")

if __name__ == '__main__':
    test_assistant()