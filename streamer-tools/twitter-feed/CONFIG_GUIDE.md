# Twitter Stream Tool Configuration Guide

The Twitter Stream Tool now supports comprehensive configuration through the `config.json` file. This allows you to customize behavior without editing code.

## Configuration File Location

The configuration file is located at:
```
streamer-tools/twitter-feed/config.json
```

## Configuration Sections

### 🚀 Stream Settings
Controls core streaming behavior:
- `auto_generation_interval`: Time between auto-generated tweets (seconds)
- `max_tweets_stored`: Maximum number of tweets to keep in memory
- `server_port`: Port for the web server (default: 5000)
- `debug_mode`: Enable debug logging

### 🎭 Persona Selection
Controls what types of personas appear in tweets:
- `citizen_boost_chance`: Probability of selecting citizen personas (0.0-1.0)
- `journalist_avoid_chance`: Probability of avoiding journalist personas (0.0-1.0)  
- `leader_selection_chance`: Probability of selecting leader personas (0.0-1.0)
- `official_selection_chance`: Probability of selecting official personas (0.0-1.0)
- `country_specific_boost`: Probability of using country-specific personas (0.0-1.0)
- `satirical_persona_chance`: Probability of using satirical personas (0.0-1.0)

### 📝 Content Generation
Controls what information appears in tweets and world summaries:
- `enable_ideological_country_names`: Use names like "German Reich" instead of "Germany"
- `show_leader_names`: Show actual leader names (e.g., "Adolf Hitler")
- `show_ideology_in_summary`: Include ideology in world power status
- `max_world_powers_displayed`: How many major powers to show
- `max_minor_powers_displayed`: How many minor powers to show
- `include_recent_focuses`: Show recently completed national focuses

### 🤖 AI Generation
Controls the AI model and generation parameters:
- `model_name`: AI model to use (e.g., "gpt-4o-mini")
- `max_tokens`: Maximum tokens per generation
- `temperature`: AI creativity level (0.0-2.0)
- `enable_ai_logs`: Save AI prompts and responses for debugging
- `ai_log_directory`: Where to store AI logs

### 🎨 Satirical Settings
Enable/disable specific satirical persona types:
- `peasant_personas_enabled`: Confused peasants with phones
- `time_traveler_enabled`: Time travelers from 2024
- `drunk_philosopher_enabled`: Intoxicated philosophers 
- `conspiracy_pigeon_enabled`: Government surveillance pigeons
- `method_actor_enabled`: Actors thinking they're in a drama
- `literal_translator_enabled`: Overly literal translators
- `telegraph_operator_enabled`: Confused telegraph operators
- `lost_tourist_enabled`: Hopelessly lost tourists

### 📂 Paths
File and directory locations:
- `game_data_file`: Path to parsed game data JSON
- `persona_directory`: Directory containing persona templates
- `locale_directory`: Directory containing localization files
- `hoi4_installation`: Path to HOI4 game installation

## Common Configuration Examples

### More Leaders, Fewer Journalists
```json
{
  "persona_selection": {
    "citizen_boost_chance": 0.3,
    "journalist_avoid_chance": 0.9,
    "leader_selection_chance": 0.8,
    "official_selection_chance": 0.5
  }
}
```

### Maximum Comedy Mode
```json
{
  "persona_selection": {
    "satirical_persona_chance": 0.4
  },
  "satirical_settings": {
    "peasant_personas_enabled": true,
    "time_traveler_enabled": true,
    "drunk_philosopher_enabled": true,
    "conspiracy_pigeon_enabled": true,
    "method_actor_enabled": true,
    "literal_translator_enabled": true,
    "telegraph_operator_enabled": true,
    "lost_tourist_enabled": true
  }
}
```

### Fast Generation for Testing
```json
{
  "stream_settings": {
    "auto_generation_interval": 10,
    "debug_mode": true
  }
}
```

### Historical Accuracy Mode
```json
{
  "content_generation": {
    "enable_ideological_country_names": true,
    "show_leader_names": true,
    "show_ideology_in_summary": true
  },
  "persona_selection": {
    "journalist_avoid_chance": 0.3,
    "leader_selection_chance": 0.2,
    "satirical_persona_chance": 0.0
  }
}
```

## Configuration Management

### Programmatic Access
```python
from config_loader import get_config, get_citizen_boost, get_auto_interval

# Get the full config object
config = get_config()

# Get specific values with dot notation
value = config.get('persona_selection.citizen_boost_chance')

# Use convenience functions
boost = get_citizen_boost()
interval = get_auto_interval()
```

### Reloading Configuration
The configuration is loaded at startup. To reload after making changes:
```python
from config_loader import reload_config
reload_config()
```

### Testing Configuration
To test the configuration loader:
```bash
cd streamer-tools/twitter-feed
python config_loader.py
```

## Tips

1. **Start Small**: Modify one section at a time and test
2. **Backup**: Keep a copy of working configuration before major changes
3. **Debug Mode**: Enable `debug_mode` to see detailed logging
4. **Realistic Values**: Keep probabilities between 0.0 and 1.0
5. **Performance**: Lower `auto_generation_interval` for faster testing, higher for production

## Troubleshooting

- **Config not loading**: Check JSON syntax with an online validator
- **No changes**: Restart the server after configuration changes  
- **Import errors**: Ensure `config_loader.py` is in the same directory
- **Default values**: If config fails, the system falls back to hardcoded defaults

The configuration system is designed to be robust - if there are any issues loading the config, the system will continue working with default values.