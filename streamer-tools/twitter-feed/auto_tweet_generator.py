#!/usr/bin/env python3
"""
Automatic Tweet Generator for Live Streaming
Generates tweets every 15 seconds based on real game data events
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
    from stream_twitter_generator import StreamTwitterGenerator
    from ai_client import AIClient
    from localization import HOI4Localizer
    AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI components not available: {e}")
    AI_AVAILABLE = False

class AutoTweetGenerator:
    """Generates tweets automatically based on game state changes"""
    
    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = project_root / 'data' / 'game_data.json'
        
        self.data_path = Path(data_path)
        self.last_game_data = None
        self.processed_events = set()
        
        # Initialize AI components and use existing localizer
        if AI_AVAILABLE:
            self.stream_generator = StreamTwitterGenerator()
            self.ai_client = AIClient()
            # Use the localizer from stream_generator that already has ALL files loaded
            self.localizer = self.stream_generator.localizer
            print(f"AutoTweetGenerator using localizer with {len(self.localizer.translations)} translations")
        else:
            self.stream_generator = None
            self.ai_client = None
            self.localizer = None
    
    def load_game_data(self) -> Optional[Dict]:
        """Load current game data"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading game data: {e}")
        return None
    
    def find_new_events(self, current_data: Dict, previous_data: Dict = None) -> List[Dict]:
        """Find interesting current events to tweet about"""
        # Always look for interesting current state, regardless of changes
        events = self._extract_current_situation_events(current_data)
        return events
    
    def _extract_current_situation_events(self, game_data: Dict) -> List[Dict]:
        """Extract interesting events from current game state"""
        events = []
        
        if 'countries' not in game_data:
            return events
        
        # Look at major powers first, then some minors
        major_powers = []
        minor_powers = []
        
        for country in game_data['countries']:
            country_data = country.get('data', {})
            if country_data.get('major', False):
                major_powers.append(country)
            else:
                minor_powers.append(country)
        
        # Process all majors + random minors
        countries_to_check = major_powers + random.sample(minor_powers, min(3, len(minor_powers)))
        
        for country in countries_to_check:
            country_tag = country.get('tag')
            country_data = country.get('data', {})
            
            # Focus events - always include if there's an ongoing focus
            focus = country_data.get('focus', {})
            current_focus = focus.get('current')
            progress = focus.get('progress', 0)
            
            if current_focus:
                # Get proper focus information using the localization system
                focus_name = self._get_focus_name_for_display(current_focus, country_tag)
                focus_description = self._get_focus_description(current_focus, country_tag)
                
                if progress > 80:
                    events.append({
                        'type': 'focus_completing',
                        'country': country_tag,
                        'title': f'{self._get_country_name(country_tag)} nears completion of {focus_name}',
                        'description': focus_description,
                        'priority': 'high' if country_data.get('major') else 'medium',
                        'focus_id': current_focus,  # Include original focus ID for better processing
                        'progress': progress
                    })
                elif progress > 50:
                    events.append({
                        'type': 'focus_advancing',
                        'country': country_tag,
                        'title': f'{self._get_country_name(country_tag)} makes progress on {focus_name}',
                        'description': focus_description,
                        'priority': 'medium' if country_data.get('major') else 'low',
                        'focus_id': current_focus,
                        'progress': progress
                    })
                else:
                    events.append({
                        'type': 'focus_ongoing', 
                        'country': country_tag,
                        'title': f'{self._get_country_name(country_tag)} pursues {focus_name}',
                        'description': focus_description,
                        'priority': 'medium' if country_data.get('major') else 'low',
                        'focus_id': current_focus,
                        'progress': progress
                    })
            
            # Look for events data if available
            events_data = country_data.get('events', [])
            if events_data and random.random() < 0.3:  # 30% chance to include event
                # Sample a recent event
                recent_event = random.choice(events_data[-5:])  # Last 5 events
                if isinstance(recent_event, dict):
                    event_id = recent_event.get('id', 'unknown_event')
                    events.append({
                        'type': 'country_event',
                        'country': country_tag,
                        'title': f'{self._get_country_name(country_tag)} experiences significant developments',
                        'description': f'Recent developments shape national direction',
                        'priority': 'medium' if country_data.get('major') else 'low',
                        'event_data': recent_event
                    })
        
        # Randomly shuffle and return a selection to ensure variety
        random.shuffle(events)
        
        # Sort by priority but keep some randomness
        high_priority = [e for e in events if e.get('priority') == 'high']
        medium_priority = [e for e in events if e.get('priority') == 'medium'] 
        low_priority = [e for e in events if e.get('priority') == 'low']
        
        # Return mix of priorities with randomness
        selected_events = []
        if high_priority:
            selected_events.extend(random.sample(high_priority, min(2, len(high_priority))))
        if medium_priority:
            selected_events.extend(random.sample(medium_priority, min(2, len(medium_priority))))
        if low_priority and len(selected_events) < 3:
            selected_events.extend(random.sample(low_priority, min(1, len(low_priority))))
        
        return selected_events[:3]  # Return up to 3 events for selection
    
    def _find_focus_changes(self, current_data: Dict, previous_data: Dict) -> List[Dict]:
        """Find focus completions and new focus starts"""
        events = []
        
        current_countries = {c['tag']: c for c in current_data.get('countries', [])}
        previous_countries = {c['tag']: c for c in previous_data.get('countries', [])}
        
        for tag, current_country in current_countries.items():
            if tag not in previous_countries:
                continue
                
            previous_country = previous_countries[tag]
            
            current_focus = current_country.get('data', {}).get('focus', {})
            previous_focus = previous_country.get('data', {}).get('focus', {})
            
            current_focus_name = current_focus.get('current')
            previous_focus_name = previous_focus.get('current')
            
            # Focus completed
            if previous_focus_name and not current_focus_name:
                focus_name = self._clean_focus_name(previous_focus_name, tag)
                events.append({
                    'type': 'focus_complete',
                    'country': tag,
                    'title': f'{self._get_country_name(tag)} completes {focus_name}',
                    'description': f'Major national focus achievement unlocks new possibilities',
                    'priority': 'high' if current_country.get('data', {}).get('major') else 'medium'
                })
            
            # New focus started
            elif current_focus_name and current_focus_name != previous_focus_name:
                focus_name = self._clean_focus_name(current_focus_name, tag)
                events.append({
                    'type': 'focus_start',
                    'country': tag,
                    'title': f'{self._get_country_name(tag)} begins {focus_name}',
                    'description': f'New national priority shifts governmental focus',
                    'priority': 'medium' if current_country.get('data', {}).get('major') else 'low'
                })
        
        return events
    
    def _find_political_changes(self, current_data: Dict, previous_data: Dict) -> List[Dict]:
        """Find significant political changes"""
        events = []
        # This could be expanded to detect party popularity changes,
        # new elections, etc. For now, keep it simple.
        return events
    
    def _clean_focus_name(self, focus_id: str, country_tag: str) -> str:
        """Clean up focus names for display"""
        # Remove country prefix
        clean = focus_id.replace(f"{country_tag.lower()}_", "")
        # Replace underscores with spaces and title case
        clean = clean.replace("_", " ").title()
        return clean
    
    def _get_focus_name_for_display(self, focus_id: str, country_tag: str) -> str:
        """Get proper focus name for display, preferring localized names"""
        if not self.localizer:
            return self._clean_focus_name(focus_id, country_tag)
        
        # Try to get localized focus name first
        localized_name = self.localizer.get_localized_text(focus_id)
        if localized_name != focus_id and localized_name:
            return localized_name
        
        # Try uppercase variation
        localized_upper = self.localizer.get_localized_text(focus_id.upper())
        if localized_upper != focus_id.upper() and localized_upper:
            return localized_upper
        
        # Fall back to cleaned name
        return self._clean_focus_name(focus_id, country_tag)
    
    def _get_country_name(self, country_tag: str) -> str:
        """Get readable country name"""
        if self.localizer:
            return self.localizer.get_country_name(country_tag)
        elif self.stream_generator and hasattr(self.stream_generator, 'localizer'):
            return self.stream_generator.localizer.get_country_name(country_tag)
        
        # Fallback mapping
        country_names = {
            'GER': 'Germany', 'USA': 'America', 'SOV': 'Soviet Union', 
            'ENG': 'Britain', 'FRA': 'France', 'ITA': 'Italy', 'JAP': 'Japan',
            'POL': 'Poland', 'SPA': 'Spain', 'HOL': 'Netherlands'
        }
        return country_names.get(country_tag, country_tag)
    
    def _get_focus_description(self, focus_id: str, country_tag: str) -> str:
        """Get focus description from localization with case conversion handling"""
        if not self.localizer:
            return self._clean_focus_name(focus_id, country_tag)
        
        # Try multiple variations to find the description
        variations = [
            focus_id,  # Original case (e.g. ger_fuhrerprinzip)
            focus_id.upper(),  # All uppercase (e.g. GER_FUHRERPRINZIP) 
            f"{country_tag.upper()}_{focus_id.split('_', 1)[1] if '_' in focus_id else focus_id}"  # Uppercase country prefix
        ]
        
        for variant in variations:
            desc_key = f"{variant}_desc"
            description = self.localizer.get_localized_text(desc_key)
            
            # If we got back the same key, no description was found
            if description != desc_key and description:
                # Check if this is a placeholder (ends with "Desc" and is short)
                if description.endswith(" Desc") and len(description) < 50:
                    continue  # Skip placeholder, try next variation
                
                # Clean up description - remove dynamic text markers but don't truncate
                import re
                description = re.sub(r'\[.*?\]', '', description)  # Remove bracketed content
                description = re.sub(r'§[A-Za-z]', '', description)  # Remove color codes
                description = description.strip()
                
                return description
        
        # Fall back to focus name with same variations
        for variant in variations:
            focus_name = self.localizer.get_localized_text(variant)
            if focus_name and focus_name != variant:
                return focus_name
        
        # Final fallback to cleaned name
        return self._clean_focus_name(focus_id, country_tag)
    
    def generate_tweet_for_event(self, event: Dict, game_data: Dict) -> Optional[Dict]:
        """Generate a tweet for a specific event"""
        if not AI_AVAILABLE:
            return self._generate_fallback_tweet(event)
        
        try:
            # Use the stream generator
            prompt = self.stream_generator.generate_prompt(game_data, event_data=event)
            response = self.ai_client.generate_text(
                prompt, 
                self.stream_generator.get_max_tokens(), 
                report_type="auto_stream_twitter"
            )
            
            # Parse response into tweet format
            tweet = self._parse_ai_response(response, event)
            return tweet
            
        except Exception as e:
            print(f"Error generating AI tweet: {e}")
            return self._generate_fallback_tweet(event)
    
    def _parse_ai_response(self, response: str, event: Dict) -> Dict:
        """Parse AI response into tweet structure"""
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        
        for line in lines:
            if line.startswith('@') and ': ' in line:
                username_part, content = line.split(': ', 1)
                username = username_part[1:]  # Remove @
                
                # Clean up template placeholders
                content = self._cleanup_placeholders(content)
                
                return {
                    'id': int(time.time() * 1000),
                    'username': username.replace('_', ' ').title(),
                    'handle': f'@{username}',
                    'content': content.strip(),
                    'timestamp': self._generate_timestamp(),
                    'avatar': self._determine_avatar_type(username),
                    'country': event.get('country'),
                    'isBreaking': event.get('priority') == 'high',
                    'created_at': time.time()
                }
        
        # Fallback if parsing fails
        return self._generate_fallback_tweet(event)
    
    def _cleanup_placeholders(self, text: str) -> str:
        """Clean up any remaining template placeholders"""
        import re
        placeholder_fixes = {
            '{{country_adjective}}': 'national',
            '{{country_name}}': 'the nation',
            '{{ideology_adjective}}': 'political',
            '{{current_leader}}': 'leadership'
        }
        
        for placeholder, replacement in placeholder_fixes.items():
            text = text.replace(placeholder, replacement)
        
        text = re.sub(r'{{[^}]*}}', '[details]', text)
        return text
    
    def _generate_fallback_tweet(self, event: Dict) -> Dict:
        """Generate a simple fallback tweet"""
        personas = [
            {'username': 'World Reporter', 'handle': '@WorldNews1936', 'avatar': 'journalist'},
            {'username': 'Diplomatic Observer', 'handle': '@DipWatch', 'avatar': 'diplomat'},
            {'username': 'European Correspondent', 'handle': '@EuropeNews', 'avatar': 'journalist'}
        ]
        
        persona = random.choice(personas)
        
        return {
            'id': int(time.time() * 1000),
            'username': persona['username'],
            'handle': persona['handle'],
            'content': f"📰 {event.get('title', 'Breaking developments reported')} #WorldNews #1936",
            'timestamp': self._generate_timestamp(),
            'avatar': persona['avatar'],
            'country': event.get('country'),
            'isBreaking': event.get('priority') == 'high',
            'created_at': time.time()
        }
    
    def _determine_avatar_type(self, username: str) -> str:
        """Determine avatar type from username"""
        username_lower = username.lower()
        
        if any(title in username_lower for title in ['führer', 'president', 'secretary', 'minister']):
            return 'leader'
        elif any(title in username_lower for title in ['diplomat', 'ambassador', 'foreign']):
            return 'diplomat'
        elif any(role in username_lower for role in ['correspondent', 'reporter', 'news']):
            return 'journalist'
        else:
            return 'citizen'
    
    def _generate_timestamp(self) -> str:
        """Generate realistic timestamp"""
        if random.random() < 0.4:
            return 'now'
        elif random.random() < 0.7:
            return f'{random.randint(1, 59)}m'
        else:
            return f'{random.randint(1, 6)}h'
    
    def run_auto_generation(self, interval: int = 15):
        """Run automatic tweet generation"""
        print(f"Starting automatic tweet generation (interval: {interval}s)")
        print(f"Data path: {self.data_path}")
        print(f"AI Available: {AI_AVAILABLE}")
        
        while True:
            try:
                # Load current game data
                current_data = self.load_game_data()
                
                if current_data:
                    # Find interesting current events
                    events = self.find_new_events(current_data, self.last_game_data)
                    
                    if events:
                        # Randomly pick an event from available ones
                        selected_event = random.choice(events)
                        
                        print(f"📰 Processing: {selected_event.get('title', 'Unknown event')}")
                        
                        # Generate tweet
                        tweet = self.generate_tweet_for_event(selected_event, current_data)
                        
                        if tweet:
                            print(f"🐦 Generated tweet: {tweet.get('username', 'Unknown')} - {tweet.get('content', '')[:100]}...")
                            
                            # Here you could post the tweet to your feed API
                            # For now, just print it
                        
                    else:
                        print("⏳ No interesting events found, waiting...")
                    
                    # Update last state (still useful for context)
                    self.last_game_data = current_data
                    
                else:
                    print("❌ Could not load game data")
                
            except Exception as e:
                print(f"Error in auto generation: {e}")
            
            # Wait for next interval
            time.sleep(interval)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto Tweet Generator')
    parser.add_argument('--interval', type=int, default=15, help='Generation interval in seconds')
    parser.add_argument('--data-path', type=str, help='Path to game_data.json')
    
    args = parser.parse_args()
    
    generator = AutoTweetGenerator(args.data_path)
    generator.run_auto_generation(args.interval)