#!/usr/bin/env python3
"""
Breaking News Server
Serves the HTML overlay and provides API endpoints for headline updates
"""

import json
import time
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
CURRENT_DIR = Path(__file__).parent
HEADLINE_FILE = CURRENT_DIR / 'current_headline.json'

@app.route('/')
def index():
    """Serve the main overlay HTML"""
    try:
        with open(CURRENT_DIR / 'overlay.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content
    except FileNotFoundError:
        return "Overlay file not found", 404

@app.route('/overlay')
def overlay():
    """Alternative route for the overlay"""
    return index()

@app.route('/styles.css')
def styles():
    """Serve the CSS file"""
    return send_from_directory(CURRENT_DIR, 'styles.css', mimetype='text/css')

@app.route('/current-headline')
def get_current_headline():
    """Get the current headline"""
    try:
        if HEADLINE_FILE.exists():
            with open(HEADLINE_FILE, 'r', encoding='utf-8') as f:
                headline = json.load(f)
            
            # Check if headline is too old (older than 2 minutes)
            if time.time() - headline.get('created_at', 0) > 120:
                return jsonify(get_fallback_headline())
            
            return jsonify(headline)
        else:
            return jsonify(get_fallback_headline())
            
    except Exception as e:
        print(f"Error reading headline file: {e}")
        return jsonify(get_fallback_headline())

@app.route('/api/status')
def status():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'timestamp': time.time(),
        'headline_file_exists': HEADLINE_FILE.exists()
    })

@app.route('/api/test-headline')
def test_headline():
    """Generate a test headline for testing purposes"""
    test_headlines = [
        "Local Dictator Reportedly 'Just Trying to Help'",
        "Nation's Army Runs Out of Marching Songs",
        "Breaking: Country Discovers It Has Been Country All Along",
        "Local Leaders Confused by Own Policies",
        "Nation's Flag Committee Still Arguing About Colors"
    ]
    
    import random
    headline = {
        'id': int(time.time() * 1000),
        'headline': random.choice(test_headlines),
        'country': 'TEST',
        'event_type': 'test',
        'priority': random.choice(['high', 'medium', 'low']),
        'created_at': time.time(),
        'display_duration': 15
    }
    
    # Save test headline
    try:
        with open(HEADLINE_FILE, 'w', encoding='utf-8') as f:
            json.dump(headline, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving test headline: {e}")
    
    return jsonify(headline)

def get_fallback_headline():
    """Return a fallback headline when no current headline is available"""
    return {
        'id': int(time.time() * 1000),
        'headline': "Breaking News System Online and Ready",
        'country': 'SYSTEM',
        'event_type': 'system',
        'priority': 'low',
        'created_at': time.time(),
        'display_duration': 10
    }

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Breaking News Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting Breaking News Server on {args.host}:{args.port}")
    print(f"Overlay URL: http://{args.host}:{args.port}/")
    print(f"API URL: http://{args.host}:{args.port}/current-headline")
    print(f"Test URL: http://{args.host}:{args.port}/api/test-headline")
    
    app.run(host=args.host, port=args.port, debug=args.debug)