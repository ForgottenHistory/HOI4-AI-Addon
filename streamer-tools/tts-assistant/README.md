# TTS Assistant for HOI4 Streaming

A fun AI-powered German assistant with dynamic personalities that provides gameplay commentary and responds to voice commands during Hearts of Iron 4 streaming sessions.

## Features

### 🎭 Dynamic Personalities
- **Random Generation**: Each session generates a unique German assistant (Fritz, Hans, Wilhelm, etc.)
- **8 Personality Types**: Scared, Overeager, Sarcastic, Confused, Dramatic, Pedantic, Lazy, Superstitious
- **Persistent**: Same personality until you restart the script completely
- **Unique Quirks**: Each assistant has 2-4 random quirks (mentions mother's cooking, counts in threes, etc.)

### 🎮 Game Integration
- **Live Game Data**: Reads current HOI4 game state from `data/game_data.json`
- **Change Detection**: Notices when focuses change, politics shift, etc.
- **Contextual Responses**: References current game situation in conversations
- **Auto-Commentary**: Unprompted commentary about game developments

### 🗣️ AI-Powered Conversations
- **Personality-Driven**: Each assistant type has unique response patterns
- **Game-Aware**: Incorporates current game state into responses
- **Context Memory**: Remembers recent conversation for continuity
- **Fallback Responses**: Works even without AI API access

## Quick Start

### 🖱️ Easy Way (Use Scripts)

**Windows:**
- `start_assistant.bat` - Start interactive chat
- `reset_personality.bat` - Get new personality  
- `test_personalities.bat` - See personality examples
- `extract_names.bat` - Update character names from HOI4

**Linux/Mac:**
- `./start_assistant.sh` - Start interactive chat
- `./reset_personality.sh` - Get new personality
- `./test_personalities.sh` - See personality examples  
- `./extract_names.sh` - Update character names from HOI4

### ⌨️ Manual Way (Direct Commands)

```bash
cd streamer-tools/tts-assistant

# Start interactive chat
python interactive_chat.py

# Test personality generation
python personality_generator.py

# Reset personality (get new one)
rm current_personality.json

# Update names from HOI4 files
python name_extractor.py
```

## Example Personalities

### Fritz (Scared)
- **Traits**: Nervous, anxious, pessimistic, cautious, paranoid
- **Sample**: "Oh nein, invading France? That seems very dangerous... Are you sure this is wise?"
- **Quirks**: Always mentions his mother's cooking, has irrational fear of tanks

### Wilhelm (Overeager) 
- **Traits**: Excited, optimistic, energetic, naive, loyal
- **Sample**: "Ja ja ja! Excellent idea! This will be glorious! What an amazing strategy!"
- **Quirks**: Counts everything in threes, speaks in football metaphors

### Otto (Sarcastic)
- **Traits**: Witty, cynical, intelligent, condescending, blunt  
- **Sample**: "Oh yes, that sounds brilliant... What could possibly go wrong?"
- **Quirks**: Constantly adjusts his glasses, has conspiracy theories about everything

## Interactive Commands

When using `interactive_chat.py`:

- `/help` - Show available commands
- `/personality` - View current assistant details
- `/reset` - Generate completely new personality
- `/commentary` - Toggle auto-commentary on/off
- `/status` - Show system status and game data
- `/game` - Request immediate game commentary
- `/quit` - Exit chat

## Configuration

Edit `config.json` to customize:

```json
{
  "response_settings": {
    "max_response_length": 200,
    "personality_strength": 0.8,
    "include_game_context": true
  },
  "commentary_settings": {
    "auto_commentary_interval": 30,
    "commentary_style": "reactive"
  },
  "voice_settings": {
    "speaking_rate": 1.0,
    "personality_emphasis": true
  }
}
```

## Game Data Integration

The assistant automatically:
1. Loads game data from `../../data/game_data.json`
2. Tracks changes between updates
3. References current situation in responses
4. Provides commentary on developments

### Supported Game Data
- **Current Focus**: What Germany is researching
- **Political Situation**: Stability, war support, ruling party
- **Leader Information**: Current leader name
- **Game Date**: Current in-game date
- **Major Changes**: Focus completions, political shifts

## Personality System

### 8 Core Types
1. **Scared** - Worried about everything, constantly nervous
2. **Overeager** - Extremely enthusiastic about all plans
3. **Sarcastic** - Dry wit and barely contained disdain  
4. **Confused** - Never quite understands what's happening
5. **Dramatic** - Everything is theatrical and over-the-top
6. **Pedantic** - Obsessed with rules and technical details
7. **Lazy** - Would rather be doing anything else
8. **Superstitious** - Believes in omens and luck

### Personality Features
- **Unique Names**: 23 different German names
- **Custom Traits**: 5 traits per personality type
- **Backstories**: Randomly generated backgrounds
- **Quirks**: 15+ possible quirks, 2-4 per assistant
- **Catchphrases**: Type-specific phrases and expressions
- **Voice Styles**: Personality-appropriate speaking patterns

## Dependencies

- **Python 3.7+**
- **OpenRouter API** (optional - has fallback responses)
- **Game Data**: Requires `../../data/game_data.json` from HOI4 parser
- **Environment**: `.env` file with `OPENROUTER_API_KEY`

## File Structure

```
tts-assistant/
├── tts_assistant.py          # Main assistant service
├── personality_generator.py  # Personality generation system  
├── interactive_chat.py       # Text-based testing interface
├── config.json              # Configuration settings
├── current_personality.json # Persistent personality data
└── README.md               # This file
```

## Usage Tips

### For Development/Testing
- Use `interactive_chat.py` for testing conversations
- Use `/reset` command to test different personalities
- Enable auto-commentary to see unprompted responses

### For Live Streaming (Future)
- Integrate with voice recognition for speech input
- Add TTS engine for voice output
- Create push-to-talk keybind integration
- Set up OBS overlay for assistant responses

### For Content Creation
- Each personality creates different entertainment value
- Scared assistants provide cautious commentary
- Overeager assistants encourage aggressive plays
- Sarcastic assistants provide comedic relief

## Example Session

```
=== TTS Assistant Interactive Chat ===
Connected to: Fritz (scared)
Backstory: Fritz is a former accountant who got drafted but is terrified of making mistakes.

You: Should we invade France?
[Fritz]: Oh mein Gott, invade France? That sounds very dangerous... Are you absolutely certain this is wise? My mother always said to avoid unnecessary conflicts...

You: What about our current focus?
[Fritz]: According to the game data, we're working on "Army Innovations"... but what if the enemy discovers our plans? I'm not sure about this, mein Herr...
```

## Future Enhancements

- **Voice Recognition**: Real speech input via microphone
- **Text-to-Speech**: AI voice output with personality-appropriate inflection
- **OBS Integration**: Overlay graphics with assistant avatar
- **Hotkey Support**: Push-to-talk controls for streamers
- **Multi-Language**: Support for other nationalities/languages
- **Advanced AI**: More sophisticated conversation and memory