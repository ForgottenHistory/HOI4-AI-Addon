#!/usr/bin/env python3
"""
Stream Integration for HOI4 Twitter Feed
Connects the existing HOI4 AI system with the live Twitter feed for streaming
"""

import json
import time
import os
from typing import Dict, List, Any
from pathlib import Path

# Import existing HOI4 AI components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

# Import the streaming-optimized generator instead of the old one
from stream_twitter_generator import StreamTwitterGenerator
from ai_client import AIClient

class StreamTwitterFeed:
    """Manages live Twitter feed for streaming with HOI4 events"""
    
    def __init__(self, game_data_path: str = None):
        self.game_data_path = game_data_path or "../game_data.json"
        self.twitter_generator = StreamTwitterGenerator()  # Use streaming-optimized generator
        self.ai_client = AIClient()
        self.last_processed_events = set()
        self.feed_data = {
            "tweets": [],
            "last_update": time.time()
        }
        
    def process_game_events(self) -> List[Dict]:
        """Process game data and generate new tweets for events"""
        try:
            # Load game data
            with open(self.game_data_path, 'r') as f:
                game_data = json.load(f)
            
            new_tweets = []
            
            # Check for recent events
            recent_events = game_data.get('metadata', {}).get('recent_events', [])
            
            for event in recent_events:
                event_id = self._get_event_id(event)
                
                if event_id not in self.last_processed_events:
                    # Generate tweets for this event
                    tweets = self._generate_event_tweets(event, game_data)
                    new_tweets.extend(tweets)
                    self.last_processed_events.add(event_id)
            
            # Check for focus completions and other state changes
            state_tweets = self._check_state_changes(game_data)
            new_tweets.extend(state_tweets)
            
            return new_tweets
            
        except FileNotFoundError:
            print(f"Game data not found at {self.game_data_path}")
            return []
        except json.JSONDecodeError:
            print(f"Invalid JSON in {self.game_data_path}")
            return []
    
    def _get_event_id(self, event) -> str:
        """Generate unique ID for event"""
        if isinstance(event, dict):
            return f"{event.get('title', '')}_{event.get('date', time.time())}"
        return str(hash(str(event)))
    
    def _format_event_data(self, event) -> Dict:
        """Format event for the streaming generator"""
        if isinstance(event, dict):
            return {
                'title': event.get('title', 'Event reported'),
                'description': event.get('description', ''),
                'type': event.get('type', 'general'),
                'country': event.get('country'),
                'date': event.get('date')
            }
        else:
            # Handle string events - try to parse some info
            event_str = str(event)
            
            # Try to extract country from event string
            country = None
            for country_name, tag in [
                ('Germany', 'GER'), ('Soviet', 'SOV'), ('Russia', 'SOV'), 
                ('America', 'USA'), ('Britain', 'ENG'), ('France', 'FRA'),
                ('Italy', 'ITA'), ('Japan', 'JAP'), ('China', 'CHI')
            ]:
                if country_name.lower() in event_str.lower():
                    country = tag
                    break
            
            # Determine event type from content
            event_type = 'general'
            if any(word in event_str.lower() for word in ['focus', 'policy', 'pursue']):
                event_type = 'focus_ongoing'
            elif any(word in event_str.lower() for word in ['war', 'attack', 'invade']):
                event_type = 'war'
            elif any(word in event_str.lower() for word in ['complete', 'finished']):
                event_type = 'focus_completed'
            
            return {
                'title': event_str,
                'description': '',
                'type': event_type,
                'country': country,
                'date': None
            }
    
    def _generate_event_tweets(self, event, game_data: Dict) -> List[Dict]:
        """Generate tweets for a specific event using AI"""
        try:
            # Format event data for the streaming generator
            event_data = self._format_event_data(event)
            
            # Use streaming twitter generator with proper event_data parameter
            prompt = self.twitter_generator.generate_prompt(
                game_data,
                event_data=event_data
            )
            
            # Generate AI response
            response = self.ai_client.generate_response(prompt, self.twitter_generator.get_max_tokens())
            
            # Parse response into individual tweets
            tweets = self._parse_ai_response(response, event)
            return tweets
            
        except Exception as e:
            print(f"Error generating tweets for event: {e}")
            return self._generate_fallback_tweets(event)
    
    def _parse_ai_response(self, response: str, event) -> List[Dict]:
        """Parse AI response into structured tweet data"""
        tweets = []
        lines = response.strip().split('\n')
        
        current_tweet = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for username pattern: @username: tweet content
            if line.startswith('@') and ': ' in line:
                # Save previous tweet if exists
                if current_tweet:
                    tweets.append(self._finalize_tweet(current_tweet, event))
                
                # Start new tweet
                username_part, content = line.split(': ', 1)
                username = username_part[1:]  # Remove @
                
                current_tweet = {
                    'username': self._format_username(username),
                    'handle': f'@{username}',
                    'content': content,
                    'timestamp': self._generate_timestamp(),
                    'event_id': self._get_event_id(event)
                }
            
            # Check for timestamp pattern
            elif line.endswith('ago') or 'h' in line or 'm' in line:
                if current_tweet:
                    current_tweet['timestamp'] = line
        
        # Don't forget the last tweet
        if current_tweet:
            tweets.append(self._finalize_tweet(current_tweet, event))
        
        return tweets[:6]  # Limit to 6 tweets per event
    
    def _finalize_tweet(self, tweet_data: Dict, event) -> Dict:
        """Add missing fields to tweet data"""
        tweet_data.update({
            'id': int(time.time() * 1000) + len(self.feed_data['tweets']),
            'avatar': self._determine_avatar_type(tweet_data['username']),
            'country': self._determine_country(tweet_data['username']),
            'isBreaking': self._is_breaking_event(event),
            'created_at': time.time()
        })
        return tweet_data
    
    def _determine_avatar_type(self, username: str) -> str:
        """Determine avatar type based on username"""
        username_lower = username.lower()
        
        if any(leader in username_lower for leader in ['hitler', 'stalin', 'roosevelt', 'churchill', 'mussolini']):
            return 'leader'
        elif any(title in username_lower for title in ['minister', 'secretary', 'ambassador']):
            return 'diplomat'  
        elif any(role in username_lower for role in ['correspondent', 'reporter', 'journalist', 'news']):
            return 'journalist'
        elif any(party in username_lower for party in ['party', 'communist', 'fascist', 'democratic']):
            return 'party'
        else:
            return 'citizen'
    
    def _determine_country(self, username: str) -> str:
        """Determine country code from username context"""
        username_lower = username.lower()
        
        country_mapping = {
            'german': 'ger', 'hitler': 'ger', 'hess': 'ger', 'goebbels': 'ger',
            'soviet': 'sov', 'stalin': 'sov', 'molotov': 'sov', 'russian': 'sov',
            'american': 'usa', 'roosevelt': 'usa', 'fdr': 'usa', 'hull': 'usa',
            'british': 'eng', 'churchill': 'eng', 'eden': 'eng', 'chamberlain': 'eng',
            'french': 'fra', 'french': 'fra', 'daladier': 'fra',
            'italian': 'ita', 'mussolini': 'ita',
            'japanese': 'jap', 'hirohito': 'jap',
            'chinese': 'chi', 'chiang': 'chi'
        }
        
        for keyword, country in country_mapping.items():
            if keyword in username_lower:
                return country
        
        return None
    
    def _is_breaking_event(self, event) -> bool:
        """Determine if event should be marked as breaking news"""
        if isinstance(event, dict):
            title = event.get('title', '').lower()
        else:
            title = str(event).lower()
            
        breaking_keywords = ['war', 'attack', 'invade', 'crisis', 'emergency', 'urgent', 'breaking']
        return any(keyword in title for keyword in breaking_keywords)
    
    def _generate_fallback_tweets(self, event) -> List[Dict]:
        """Generate simple fallback tweets when AI fails"""
        return [{
            'id': int(time.time() * 1000),
            'username': 'World News Today',
            'handle': '@WorldNews1936',
            'content': f"📰 {event.get('title', 'Major event reported')} #WorldNews #1936",
            'timestamp': 'now',
            'avatar': 'journalist',
            'country': None,
            'isBreaking': self._is_breaking_event(event),
            'event_id': self._get_event_id(event),
            'created_at': time.time()
        }]
    
    def _check_state_changes(self, game_data: Dict) -> List[Dict]:
        """Check for state changes that should generate tweets"""
        # This could check for focus completions, tech research, etc.
        # For now, return empty list - expand based on your needs
        return []
    
    def _format_username(self, username: str) -> str:
        """Format username for display"""
        # Convert @GermanChancellor to "German Chancellor"
        return username.replace('_', ' ').title()
    
    def _generate_timestamp(self) -> str:
        """Generate realistic timestamp"""
        import random
        if random.random() < 0.3:
            return 'now'
        elif random.random() < 0.6:
            return f'{random.randint(1, 59)}m'
        else:
            return f'{random.randint(1, 12)}h'
    
    def update_feed_json(self, new_tweets: List[Dict]):
        """Update JSON file that the web feed reads"""
        self.feed_data['tweets'].extend(new_tweets)
        
        # Keep only last 20 tweets
        self.feed_data['tweets'] = self.feed_data['tweets'][-20:]
        self.feed_data['last_update'] = time.time()
        
        # Write to JSON file
        feed_json_path = Path(__file__).parent / 'feed_data.json'
        with open(feed_json_path, 'w') as f:
            json.dump(self.feed_data, f, indent=2)
    
    def run_continuous(self, interval: int = 10):
        """Run continuous monitoring for stream"""
        print(f"Starting Twitter feed monitoring (checking every {interval}s)")
        
        while True:
            try:
                new_tweets = self.process_game_events()
                
                if new_tweets:
                    print(f"Generated {len(new_tweets)} new tweets")
                    self.update_feed_json(new_tweets)
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("Stopping Twitter feed monitoring")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(interval)

def main():
    """Main entry point for stream integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='HOI4 Twitter Feed Stream Integration')
    parser.add_argument('--game-data', help='Path to game_data.json file')
    parser.add_argument('--interval', type=int, default=10, help='Check interval in seconds')
    parser.add_argument('--test', action='store_true', help='Run single test update')
    
    args = parser.parse_args()
    
    feed = StreamTwitterFeed(args.game_data)
    
    if args.test:
        # Single test run
        tweets = feed.process_game_events()
        print(f"Generated {len(tweets)} tweets:")
        for tweet in tweets:
            print(f"@{tweet['handle']}: {tweet['content']}")
    else:
        # Continuous monitoring
        feed.run_continuous(args.interval)

if __name__ == "__main__":
    main()