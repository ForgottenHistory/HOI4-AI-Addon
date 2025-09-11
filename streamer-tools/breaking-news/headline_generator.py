#!/usr/bin/env python3
"""
Breaking News Headline Generator - Refactored with GameEventService
Generates satirical "The Onion" style breaking news headlines from HOI4 game data
Uses centralized GameEventService for consistent data extraction across all generators
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
    from game_event_service import GameEventService, GameEvent
    AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI components not available: {e}")
    AI_AVAILABLE = False


class BreakingNewsGenerator:
    """Simplified breaking news generator using GameEventService"""
    
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
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"Loaded configuration from {self.config_path}")
                return config
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            # Default configuration
            return {
                "generation": {"interval_seconds": 30, "max_headlines_stored": 5},
                "content_settings": {"max_events_per_cycle": 3}
            }
    
    def load_game_data(self) -> Optional[Dict]:
        """Load game data from JSON file"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading game data: {e}")
        return None
    
    def get_random_events(self, current_data: Dict) -> List[GameEvent]:
        """Get random events using GameEventService - guaranteed to return events"""
        if not self.game_event_service:
            return []
        
        events = []
        max_events = self.config.get('content_settings', {}).get('max_events_per_cycle', 3)
        
        # Try to get different types of events
        event_attempts = [
            lambda: self.game_event_service.get_random_focus_event(current_data, prefer_majors=True),
            lambda: self.game_event_service.get_random_political_situation(current_data, prefer_majors=True), 
            lambda: self.game_event_service.get_random_world_situation(current_data),
            lambda: self.game_event_service.get_random_absurd_event(current_data)
        ]
        
        # Shuffle attempts to get variety
        random.shuffle(event_attempts)
        
        for attempt in event_attempts:
            if len(events) >= max_events:
                break
            
            event = attempt()
            if event:
                events.append(event)
        
        # Guarantee at least one event - this eliminates "no events found"
        if not events:
            event = self.game_event_service.get_any_random_event(current_data, prefer_majors=True)
            events.append(event)
        
        return events
    
    def generate_headline(self, event: GameEvent, game_data: Dict) -> Optional[Dict]:
        """Generate headline from a GameEvent"""
        if not self.ai_client:
            return self._generate_fallback_headline(event)
        
        try:
            prompt = self._create_headline_prompt(event, game_data)
            
            response = self.ai_client.generate_text(
                prompt=prompt,
                max_tokens=150,
                temperature=0.9,
                report_type="breaking_news_headline"
            )
            
            if response and response.strip():
                return self._parse_headline_response(response, event)
            else:
                return self._generate_fallback_headline(event)
                
        except Exception as e:
            print(f"Error generating headline: {e}")
            return self._generate_fallback_headline(event)
    
    def _progress_to_text(self, progress: float) -> str:
        """Convert progress percentage to descriptive text"""
        if progress <= 5:
            return "just beginning"
        elif progress <= 15:
            return "barely started"
        elif progress <= 30:
            return "early stages"
        elif progress <= 50:
            return "making progress"
        elif progress <= 70:
            return "well underway"
        elif progress <= 85:
            return "nearing completion"
        elif progress <= 95:
            return "almost finished"
        else:
            return "nearly complete"
    
    def _stability_to_text(self, stability: float) -> str:
        """Convert stability percentage to descriptive text"""
        # stability comes as a decimal (0.0-1.0), convert to percentage for thresholds
        stability_percent = stability * 100
        
        if stability_percent >= 80:
            return "very stable"
        elif stability_percent >= 65:
            return "stable"
        elif stability_percent >= 50:
            return "somewhat stable"
        elif stability_percent >= 35:
            return "unstable"
        elif stability_percent >= 20:
            return "very unstable"
        else:
            return "in complete chaos"
    
    def _create_headline_prompt(self, event: GameEvent, game_data: Dict) -> str:
        """Create prompt for headline generation using GameEvent data"""
        ideology_info = f"{event.ruling_party}"
        if event.specific_ideology:
            ideology_info = f"{event.specific_ideology} ({event.ruling_party})"
            
        # Get current date from game data
        current_date = "1936.01.01"
        if 'metadata' in game_data and 'date' in game_data['metadata']:
            current_date = game_data['metadata']['date']
            
        base_prompt = f"""You are writing satirical breaking news headlines in the style of The Onion newspaper.

EVENT DATA:
- Type: {event.event_type}
- Country: {event.country_name} ({event.country_tag})
- Leader: {event.leader_name}
- Ideology: {ideology_info}
- Priority: {event.priority}
- Date: {current_date}
"""

        # Add event-specific context
        if event.event_type.startswith('focus_'):
            if event.focus_name:
                base_prompt += f"- Focus: {event.focus_name}\n"
            if event.focus_description:
                base_prompt += f"- Focus Description: {event.focus_description}\n"
            if event.focus_progress is not None:
                progress_text = self._progress_to_text(event.focus_progress)
                base_prompt += f"- Progress: {progress_text}\n"
                
            if event.event_type == 'focus_completed':
                base_prompt += f"- Context: {event.leader_name} has completed the '{event.focus_name}' policy focus. Create a satirical headline about this political accomplishment.\n"
            elif event.event_type == 'focus_progressing':
                progress_text = self._progress_to_text(event.focus_progress)
                base_prompt += f"- Context: {event.leader_name} is working on '{event.focus_name}' policy ({progress_text}). Mock the slow pace or bureaucratic nature of government projects.\n"
            elif event.event_type == 'focus_just_started':
                base_prompt += f"- Context: {event.leader_name} just began '{event.focus_name}' policy initiative. Satirize overly ambitious political announcements.\n"
        
        elif event.event_type == 'political_situation':
            if event.political_situation:
                base_prompt += f"- Political Situation: {event.political_situation}\n"
            if event.stability is not None:
                stability_text = self._stability_to_text(event.stability)
                base_prompt += f"- Stability: {stability_text}\n"
            base_prompt += f"- Context: Political developments in {event.country_name}. Focus on government incompetence, political theater, or bureaucratic absurdity.\n"
        
        elif event.event_type == 'world_situation':
            if event.world_context:
                base_prompt += f"- World Context:\n{event.world_context}\n"
            base_prompt += f"- Context: Create headlines about ridiculous diplomatic incidents, silly international rivalries, absurd alliance negotiations, or comical misunderstandings between nations. Use {event.country_name} as the focal point but make it about international/global implications.\n"
        
        elif event.event_type == 'absurd_random':
            absurd_prompts = [
                "Leader dealing with ridiculous personal problems",
                "Bizarre national shortages or surpluses", 
                "Silly bureaucratic mix-ups",
                "Ridiculous citizen complaints",
                "Absurd diplomatic incidents over trivial matters",
                "Comical misunderstandings of modern concepts",
                "Weather-related governmental overreactions",
                "Minor celebrity phenomena causing major political responses",
                "Everyday objects becoming matters of national importance"
            ]
            selected_prompt = random.choice(absurd_prompts)
            base_prompt += f"- Context: Create a completely absurd, mundane daily life situation involving {event.leader_name} or {event.country_name}. Focus on: {selected_prompt}\n"

        base_prompt += f"""
Create a single satirical breaking news headline (no quotation marks, byline, or extra text). Make it:
- Absurdly exaggerated and ridiculous
- In the authentic style of The Onion newspaper
- 8-20 words long (can be longer if funnier)
- Use specific leader/country names when appropriate
- Mix historical context with absurd modern concerns

Onion-style examples:
"Chancellor Hitler Reportedly Frustrated Nobody Compliments His Landscape Paintings"
"Stalin Introduces Five-Year Plan for Personally High-Fiving Every Soviet Citizen"  
"Local Democracy Accidentally Elects Competent Leader, Unsure How to Proceed"
"Nation's Military Budget Mysteriously Doubled After Defense Minister's Nephew Opens Tank Dealership"

Your headline (use {event.country_name} and {event.leader_name} when appropriate):"""
        
        return base_prompt
    
    def _parse_headline_response(self, response: str, event: GameEvent) -> Dict:
        """Parse AI response and create headline data structure"""
        lines = response.strip().split('\n')
        headline_text = ""
        
        # Find the actual headline in the response
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Context:', 'Headline:', 'Breaking:', 'Note:')):
                headline_text = line
                break
        
        if not headline_text and lines:
            headline_text = lines[0].strip()
        
        # Clean up the headline
        headline_text = headline_text.strip('"\'').strip()
        
        return {
            'id': int(time.time() * 1000),
            'headline': headline_text,
            'country': event.country_tag,
            'event_type': event.event_type,
            'priority': event.priority,
            'created_at': time.time(),
            'display_duration': self._get_display_duration(event.priority)
        }
    
    def _generate_fallback_headline(self, event: GameEvent) -> Dict:
        """Generate a simple fallback headline when AI is not available"""
        fallback_headlines = {
            'focus_completed': [
                f"{event.country_name} Leaders 'Finally Finished' With Important Thing",
                f"Nation Celebrates Completion of Mysterious Government Project", 
                f"{event.leader_name} Declares Victory Over Bureaucracy"
            ],
            'focus_progressing': [
                f"{event.country_name} Still Working on That One Thing",
                f"National Progress Meter Shows 'Getting There'",
                f"{event.leader_name} Optimistic About Unnamed Initiative"
            ],
            'focus_just_started': [
                f"{event.country_name} Begins Ambitious New Something",
                f"Nation's Latest Project Already 'Going Well,' Say Officials",
                f"{event.leader_name} Excited About Fresh Start"
            ],
            'political_situation': [
                f"{event.country_name} Government Continues to Govern",
                f"Nation's Politics Described as 'Very Political'",
                f"{event.leader_name} Still in Charge of Things"
            ],
            'world_situation': [
                f"World Continues to Exist Despite {event.country_name}",
                f"International Community Still Figuring Things Out", 
                f"{event.leader_name} Has Opinions About Global Situation"
            ],
            'absurd_random': [
                f"{event.leader_name} Reportedly Dealing With Personal Issues",
                f"{event.country_name} Experiences Bizarre National Emergency",
                f"Citizens of {event.country_name} Confused by Latest Government Decision"
            ]
        }
        
        headlines = fallback_headlines.get(event.event_type, [
            f"{event.country_name} Experiences Events",
            "Local Nation Does Nation Things",
            "Breaking: Something Happening Somewhere"
        ])
        
        return {
            'id': int(time.time() * 1000),
            'headline': random.choice(headlines),
            'country': event.country_tag,
            'event_type': event.event_type,
            'priority': event.priority,
            'created_at': time.time(),
            'display_duration': self._get_display_duration(event.priority)
        }
    
    def _get_display_duration(self, priority: str) -> int:
        """Get how long headline should be displayed (in seconds)"""
        durations = {'high': 20, 'medium': 15, 'low': 10}
        return durations.get(priority, 15)
    
    def _save_current_headline(self, headline: Dict):
        """Save current headline to file for web interface"""
        try:
            output_file = Path(__file__).parent / 'current_headline.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(headline, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving headline: {e}")

    def run_headline_generation(self, interval: int = 30):
        """Run automatic headline generation - now guaranteed to always generate content"""
        print(f"Starting breaking news headline generation (interval: {interval}s)")
        print(f"Data path: {self.data_path}")
        print(f"GameEventService Available: {self.game_event_service is not None}")
        
        while True:
            try:
                current_data = self.load_game_data()
                
                if current_data:
                    # Get random events - guaranteed to return at least one
                    events = self.get_random_events(current_data)
                    
                    print(f"📊 Generated {len(events)} events")
                    
                    # Generate headlines from events
                    for event in events:
                        headline = self.generate_headline(event, current_data)
                        
                        if headline:
                            print(f"🚨 Generated headline: {headline.get('headline', '')}...")
                            
                            # Save headline to file for web interface
                            self._save_current_headline(headline)
                    
                    self.last_game_data = current_data
                    
                else:
                    print("❌ Could not load game data")
                
            except Exception as e:
                print(f"Error in headline generation: {e}")
            
            print(f"⏳ Sleeping for {interval} seconds...")
            time.sleep(interval)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Breaking News Headline Generator')
    parser.add_argument('--interval', type=int, default=30, help='Generation interval in seconds')
    parser.add_argument('--data-path', type=str, help='Path to game_data.json')
    
    args = parser.parse_args()
    
    generator = BreakingNewsGenerator(args.data_path)
    generator.run_headline_generation(args.interval)