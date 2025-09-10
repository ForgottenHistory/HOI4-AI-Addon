# HOI4 Twitter Feed - Stream Overlay

A live Twitter-like feed system for Hearts of Iron 4 streams, showing real-time tweets from world leaders, diplomats, and journalists reacting to game events.

## Features

- **Live Event Processing**: Automatically generates tweets when HOI4 events occur
- **Historical Personas**: Authentic 1930s world leaders and figures
- **Stream-Ready Design**: Clean, overlay-friendly interface
- **Debug Mode**: Test events without running the game
- **Real-time Updates**: Polls for game data every 10 seconds
- **Breaking News**: Special styling for major events

## Quick Start

### 1. Install Dependencies
```bash
cd HOI4-AI-Addon/streamer-tools/twitter-feed
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python server.py
```

### 3. For Streaming (OBS Integration)
Add as Browser Source in OBS with these settings:
- **URL**: `http://localhost:5000` (or your codespace URL)
- **Width**: 400px
- **Height**: 600px
- **Custom CSS**: Add transparency if needed

### 4. For Development/Testing
- **Debug Mode**: `http://localhost:5000/?debug=true`
- Use debug buttons to simulate events and test AI integration
- Check console for connection status and errors

### 5. GitHub Codespace Setup
```bash
# Start the server
python server.py

# The server will be available on your codespace's forwarded port
# Use the forwarded URL in OBS Browser Source
```

## Integration with HOI4 AI System

### Automatic Mode (Game Running)

The feed automatically connects to your existing HOI4 AI system:

```bash
# Start the stream integration
cd HOI4-AI-Addon/streamer-tools/twitter-feed
python stream_integration.py

# Or with custom settings
python stream_integration.py --interval 5 --game-data ../../game_data.json
```

### Manual Testing

```bash
# Test tweet generation without game data
python stream_integration.py --test
```

## File Structure

```
twitter-feed/
├── index.html          # Main feed display
├── styles.css          # Twitter-like styling
├── feed.js            # Frontend JavaScript
├── stream_integration.py # Backend integration
├── feed_data.json     # Live tweet data (auto-generated)
└── README.md          # This file
```

## Customization

### Personas and Characters

Edit `feed.js` to modify the available personas:

```javascript
const personas = {
    war: [
        { username: 'Adolf Hitler', handle: '@GermanChancellor', avatar: 'leader', country: 'ger' },
        // Add your own personas here
    ]
}
```

### Tweet Templates

Modify tweet generation in `stream_integration.py`:

```python
def generateTweetContent(self, event, persona):
    # Add your own tweet templates
    templates = {
        'war': [
            'Template for war events...',
            # Add more templates
        ]
    }
```

### Styling

Customize the look in `styles.css`:

- Change colors, fonts, sizes
- Modify animations and transitions
- Add your own branding

## Advanced Features

### Event Categories

The system categorizes events into:
- **War**: Military conflicts, attacks
- **Policy**: Focus completions, research
- **Politics**: Elections, government changes
- **Crisis**: Diplomatic tensions, emergencies
- **General**: Other world events

### Breaking News

Events marked as "breaking" get special treatment:
- Red accent border
- 🚨 emoji in username
- Priority positioning

### Country Flags

Automatic flag detection for major powers:
- 🇩🇪 Germany (GER)
- 🇷🇺 Soviet Union (SOV)  
- 🇺🇸 United States (USA)
- 🇬🇧 Britain (ENG)
- 🇫🇷 France (FRA)
- 🇮🇹 Italy (ITA)
- 🇯🇵 Japan (JAP)

## Troubleshooting

### No Tweets Appearing

1. Check if `game_data.json` exists in the parent directory
2. Verify the stream integration is running
3. Enable debug mode to test with simulated events

### Tweets Not Updating

1. Check browser console for errors
2. Verify the feed data JSON is being updated
3. Ensure the polling interval isn't too high

### OBS Integration Issues

1. Use absolute file paths in Browser Source URL
2. Set proper width/height (400x800 recommended)
3. Enable "Shutdown source when not visible" for better performance

## Future Enhancements

- [ ] Sound notifications for breaking news
- [ ] Tweet reactions and retweets
- [ ] Historical tweet archive
- [ ] Multiple feed themes
- [ ] Integration with Twitch chat
- [ ] Custom persona builder
- [ ] Event priority system
- [ ] Multi-language support

## Contributing

Feel free to submit issues and enhancement requests! This tool is designed to grow with your streaming needs.