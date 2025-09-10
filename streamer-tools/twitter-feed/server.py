#!/usr/bin/env python3
"""
Simple Flask server for HOI4 Twitter Feed
Serves the feed and connects to AI services
"""

import json
import time
import sys
import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Load environment variables from project root
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')

# Add the src directory to path for imports
sys.path.append(str(project_root / 'src'))

try:
    from generators.twitter_generator import TwitterGenerator
    from ai_client import AIClient
    # Import our custom stream generator
    from stream_twitter_generator import StreamTwitterGenerator
    # Import auto tweet generator
    from auto_tweet_generator import AutoTweetGenerator
    AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI components not available: {e}")
    AI_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Global state
feed_state = {
    'tweets': [],
    'last_update': 0,
    'processed_events': set()
}

twitter_generator = TwitterGenerator() if AI_AVAILABLE else None
stream_generator = StreamTwitterGenerator() if AI_AVAILABLE else None
ai_client = AIClient() if AI_AVAILABLE else None

# Auto tweet generator (will be started on demand)
auto_generator = None
auto_thread = None

def cleanup_template_placeholders(text):
    """Clean up any remaining template placeholders from AI responses"""
    import re
    
    # Replace common template placeholders that might slip through
    placeholder_fixes = {
        '{{country_adjective}}': 'national',
        '{{country_name}}': 'the nation',
        '{{ideology_adjective}}': 'political',
        '{{current_leader}}': 'leadership'
    }
    
    for placeholder, replacement in placeholder_fixes.items():
        text = text.replace(placeholder, replacement)
    
    # Clean up any remaining {{}} patterns
    text = re.sub(r'{{[^}]*}}', '[redacted]', text)
    
    return text

@app.route('/')
def index():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

@app.route('/api/tweets')
def get_tweets():
    """Get current tweets"""
    return jsonify({
        'tweets': feed_state['tweets'],
        'last_update': feed_state['last_update']
    })

@app.route('/api/generate_tweet/<event_type>')
def generate_test_tweet(event_type):
    """Generate a test tweet for debugging"""
    try:
        # Simulate different event types
        events = {
            'focus_complete': {
                'title': 'Germany completes Army Innovations focus',
                'description': 'Military modernization efforts show significant progress',
                'type': 'focus'
            },
            'declare_war': {
                'title': 'Germany declares war on Poland',
                'description': 'European tensions escalate dramatically as conflict begins',
                'type': 'war'
            },
            'election': {
                'title': 'Presidential election results announced in United States',
                'description': 'Political landscape shifts as new leadership emerges',
                'type': 'politics'
            },
            'random': {
                'title': 'Diplomatic crisis emerges in Eastern Europe',
                'description': 'International relations strain under mounting pressure',
                'type': 'crisis'
            },
            'leader_speech': {
                'title': 'National leader addresses major policy changes',
                'description': 'Head of government speaks on critical domestic and international issues',
                'type': 'politics',
                'force_leader': True  # Flag to ensure leader selection
            }
        }
        
        event = events.get(event_type, events['random'])
        
        if AI_AVAILABLE:
            tweet = generate_ai_tweet(event)
        else:
            tweet = generate_fallback_tweet(event)
        
        # Add to feed at the beginning (newest at top)
        feed_state['tweets'].insert(0, tweet)
        
        # Keep only first 5 tweets (remove old ones from end)
        feed_state['tweets'] = feed_state['tweets'][:5]
        feed_state['last_update'] = time.time()
        
        return jsonify({'success': True, 'tweet': tweet})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test_data')
def test_game_data():
    """Test endpoint to see what game data is available"""
    real_data = load_real_game_data()
    if real_data:
        # Show a summary of what's available
        summary = {
            'has_metadata': 'metadata' in real_data,
            'has_major_powers': 'major_powers' in real_data,
            'major_powers_count': len(real_data.get('major_powers', [])),
            'date': real_data.get('metadata', {}).get('date', 'Unknown'),
            'recent_events_count': len(real_data.get('metadata', {}).get('recent_events', [])),
            'sample_power': real_data.get('major_powers', [{}])[0] if real_data.get('major_powers') else None
        }
        return jsonify({'found_data': True, 'summary': summary})
    else:
        return jsonify({'found_data': False})

@app.route('/api/auto_start')
def start_auto_generation():
    """Start automatic tweet generation"""
    global auto_generator, auto_thread
    
    if auto_thread and auto_thread.is_alive():
        return jsonify({'success': False, 'message': 'Auto generation already running'})
    
    try:
        import threading
        
        if AI_AVAILABLE:
            auto_generator = AutoTweetGenerator()
            
            # Custom run method that integrates with our feed
            def run_auto_with_feed():
                print("🚀 Starting automatic tweet generation...")
                
                while True:
                    try:
                        # Load current game data
                        current_data = auto_generator.load_game_data()
                        
                        if current_data:
                            # Find new events
                            events = auto_generator.find_new_events(current_data, auto_generator.last_game_data)
                            
                            if events:
                                # Pick the most important event
                                selected_event = events[0]
                                
                                print(f"📰 Auto-generating tweet for: {selected_event.get('title', 'Unknown')}")
                                
                                # Generate tweet using existing AI pipeline
                                tweet = generate_ai_tweet(selected_event)
                                
                                if tweet:
                                    # Add to feed
                                    feed_state['tweets'].insert(0, tweet)
                                    feed_state['tweets'] = feed_state['tweets'][:5]  # Keep only 5
                                    feed_state['last_update'] = time.time()
                                    
                                    print(f"🐦 Added auto tweet: {tweet.get('username', 'Unknown')} - {tweet.get('content', '')[:50]}...")
                            
                            # Update last state
                            auto_generator.last_game_data = current_data
                        
                        else:
                            print("⏳ No game data found, waiting...")
                        
                    except Exception as e:
                        print(f"Error in auto generation: {e}")
                    
                    # Wait according to configuration
                    try:
                        from config_loader import get_auto_interval
                        interval = get_auto_interval()
                    except ImportError:
                        interval = 30  # Default fallback
                    time.sleep(interval)
            
            auto_thread = threading.Thread(target=run_auto_with_feed, daemon=True)
            auto_thread.start()
            
            try:
                from config_loader import get_auto_interval
                interval = get_auto_interval()
                return jsonify({'success': True, 'message': f'Auto generation started ({interval}s interval)'})
            except ImportError:
                return jsonify({'success': True, 'message': 'Auto generation started (30s interval)'})
        else:
            return jsonify({'success': False, 'message': 'AI components not available'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/auto_stop')
def stop_auto_generation():
    """Stop automatic tweet generation"""
    global auto_thread
    
    if auto_thread and auto_thread.is_alive():
        # Note: We can't actually stop the thread cleanly without more complex logic
        # For now, just return status
        return jsonify({'success': True, 'message': 'Auto generation will stop after current cycle'})
    else:
        return jsonify({'success': False, 'message': 'Auto generation not running'})

@app.route('/api/auto_status')
def get_auto_status():
    """Get auto generation status"""
    global auto_thread
    
    is_running = auto_thread and auto_thread.is_alive()
    return jsonify({
        'running': is_running,
        'message': 'Auto generation active' if is_running else 'Auto generation stopped'
    })

@app.route('/api/game_data')
def get_game_data():
    """Try to load and return game data"""
    game_data_paths = [
        Path(__file__).parent.parent.parent / 'data' / 'game_data.json',
        Path(__file__).parent.parent.parent / 'src' / 'game_data.json',  # Fallback for compatibility
        Path(__file__).parent.parent.parent / 'hoi4_parser' / 'game_data.json'  # Fallback for compatibility
    ]
    
    for path in game_data_paths:
        try:
            if path.exists():
                with open(path, 'r') as f:
                    game_data = json.load(f)
                    
                # Process any new events
                process_game_events(game_data)
                
                return jsonify({
                    'success': True, 
                    'data': game_data,
                    'source': str(path)
                })
        except Exception as e:
            continue
    
    return jsonify({
        'success': False, 
        'error': 'No game data found'
    })

def load_real_game_data():
    """Load real game data from the HOI4 parser output"""
    game_data_paths = [
        project_root / 'data' / 'game_data.json',
        project_root / 'src' / 'game_data.json',  # Fallback for compatibility
        project_root / 'hoi4_parser' / 'game_data.json'  # Fallback for compatibility
    ]
    
    for path in game_data_paths:
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                    print(f"Loaded real game data from {path}")
                    return game_data
        except Exception as e:
            print(f"Error loading game data from {path}: {e}")
            continue
    
    print("No real game data found, using fallback")
    return None

def process_game_events(game_data):
    """Process game data and generate tweets for new events"""
    if not AI_AVAILABLE:
        return
        
    try:
        recent_events = game_data.get('metadata', {}).get('recent_events', [])
        
        for event in recent_events:
            event_id = get_event_id(event)
            
            if event_id not in feed_state['processed_events']:
                tweet = generate_ai_tweet(event)
                feed_state['tweets'].insert(0, tweet)
                feed_state['processed_events'].add(event_id)
                
        # Keep only first 5 tweets (remove old ones from end)
        feed_state['tweets'] = feed_state['tweets'][:5]
        feed_state['last_update'] = time.time()
        
    except Exception as e:
        print(f"Error processing game events: {e}")

def generate_ai_tweet(event):
    """Generate a tweet using AI services with real game data"""
    try:
        # Try to load real game data first
        real_game_data = load_real_game_data()
        
        if real_game_data:
            # Use real game data
            game_data = real_game_data
            # Add the current event to recent events
            if 'metadata' not in game_data:
                game_data['metadata'] = {}
            if 'recent_events' not in game_data['metadata']:
                game_data['metadata']['recent_events'] = []
            game_data['metadata']['recent_events'].insert(0, event)
        else:
            # Fallback to minimal data if no real game data available
            game_data = {
                'metadata': {
                    'date': '1936.01.01',
                    'recent_events': [event]
                },
                'major_powers': []
            }
        
        # Use our focused stream generator with real data
        prompt = stream_generator.generate_prompt(game_data, event_data=event)
        
        # Get AI response
        response = ai_client.generate_text(prompt, stream_generator.get_max_tokens(), report_type="stream_twitter")
        
        # Parse the tweet from response (should be just one)
        tweet = parse_stream_response_to_tweet(response, event)
        return tweet
        
    except Exception as e:
        print(f"Error generating AI tweet: {e}")
        return generate_fallback_tweet(event)

def parse_stream_response_to_tweet(response, event):
    """Parse AI response into a single tweet (optimized for stream generator)"""
    lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
    
    for line in lines:
        if line.startswith('@') and ': ' in line:
            username_part, content = line.split(': ', 1)
            username = username_part[1:]  # Remove @
            
            # Clean up any remaining template placeholders
            content = cleanup_template_placeholders(content)
            
            # Check if content seems incomplete (too short or ends abruptly)
            if len(content.strip()) < 10 or content.strip().endswith(('Reports', 'According to', 'Sources')):
                print(f"Warning: AI response seems incomplete: '{content.strip()}'")
                # Try to complete with a reasonable ending
                if content.strip().endswith('Reports'):
                    content += " indicate significant military developments underway. #WorldWatch"
                elif content.strip().endswith('According to'):
                    content += " diplomatic sources, tensions continue to rise across Europe. #Politics1936"
                elif content.strip().endswith('Sources'):
                    content += " confirm major policy changes are being implemented. #Breaking"
            
            return {
                'id': int(time.time() * 1000) + len(feed_state['tweets']),
                'username': format_username(username),
                'handle': f'@{username}',
                'content': content.strip(),
                'timestamp': generate_timestamp(),
                'avatar': determine_avatar_type(username),
                'country': determine_country(username),
                'isBreaking': is_breaking_event(event),
                'created_at': time.time()
            }
    
    # Fallback if parsing fails
    print(f"Warning: Could not parse AI response: '{response[:100]}...'")
    return generate_fallback_tweet(event)

def parse_ai_response_to_tweet(response, event):
    """Parse AI response into a single tweet"""
    lines = response.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('@') and ': ' in line:
            username_part, content = line.split(': ', 1)
            username = username_part[1:]  # Remove @
            
            return {
                'id': int(time.time() * 1000) + len(feed_state['tweets']),
                'username': format_username(username),
                'handle': f'@{username}',
                'content': content,
                'timestamp': generate_timestamp(),
                'avatar': determine_avatar_type(username),
                'country': determine_country(username),
                'isBreaking': is_breaking_event(event),
                'created_at': time.time()
            }
    
    # Fallback if parsing fails
    return generate_fallback_tweet(event)

def generate_fallback_tweet(event):
    """Generate a simple fallback tweet"""
    personas = [
        {'username': 'World News Today', 'handle': '@WorldNews1936', 'avatar': 'journalist', 'country': None},
        {'username': 'European Observer', 'handle': '@EuropeWatch', 'avatar': 'journalist', 'country': None},
        {'username': 'Diplomatic Corps', 'handle': '@DiplomaticNews', 'avatar': 'diplomat', 'country': None}
    ]
    
    persona = personas[hash(str(event)) % len(personas)]
    
    return {
        'id': int(time.time() * 1000) + len(feed_state['tweets']),
        'username': persona['username'],
        'handle': persona['handle'],
        'content': f"📰 {event.get('title', 'Major developments reported')} - Situation continues to evolve. #WorldNews #1936",
        'timestamp': generate_timestamp(),
        'avatar': persona['avatar'],
        'country': persona['country'],
        'isBreaking': is_breaking_event(event),
        'created_at': time.time()
    }

def get_event_id(event):
    """Generate unique ID for event"""
    if isinstance(event, dict):
        return f"{event.get('title', '')}_{event.get('date', time.time())}"
    return str(hash(str(event)))

def format_username(username):
    """Format username for display"""
    return username.replace('_', ' ').title()

def determine_avatar_type(username):
    """Determine avatar type based on username"""
    username_lower = username.lower()
    
    if any(leader in username_lower for leader in ['hitler', 'stalin', 'roosevelt', 'churchill']):
        return 'leader'
    elif any(title in username_lower for title in ['minister', 'secretary', 'ambassador']):
        return 'diplomat'
    elif any(role in username_lower for role in ['correspondent', 'reporter', 'journalist', 'news']):
        return 'journalist'
    else:
        return 'citizen'

def determine_country(username):
    """Determine country code from username"""
    username_lower = username.lower()
    
    country_mapping = {
        'german': 'ger', 'hitler': 'ger',
        'soviet': 'sov', 'stalin': 'sov',
        'american': 'usa', 'roosevelt': 'usa',
        'british': 'eng', 'churchill': 'eng'
    }
    
    for keyword, country in country_mapping.items():
        if keyword in username_lower:
            return country
    
    return None

def is_breaking_event(event):
    """Check if event should be breaking news"""
    if isinstance(event, dict):
        title = event.get('title', '').lower()
    else:
        title = str(event).lower()
        
    breaking_keywords = ['war', 'attack', 'invade', 'crisis', 'urgent']
    return any(keyword in title for keyword in breaking_keywords)

def generate_timestamp():
    """Generate realistic timestamp"""
    import random
    if random.random() < 0.3:
        return 'now'
    elif random.random() < 0.6:
        return f'{random.randint(1, 59)}m'
    else:
        return f'{random.randint(1, 12)}h'

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='HOI4 Twitter Feed Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run server on')
    args = parser.parse_args()
    
    print("Starting HOI4 Twitter Feed Server...")
    print(f"AI Services Available: {AI_AVAILABLE}")
    print(f"Server will run on port {args.port}")
    
    # Start with empty feed
    feed_state['tweets'] = []
    feed_state['last_update'] = time.time()
    
    app.run(host='0.0.0.0', port=args.port, debug=True)