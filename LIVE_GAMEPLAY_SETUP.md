# HOI4 Live Gameplay Twitter Stream Setup

This guide will help you set up the Twitter stream to work with your actual HOI4 gameplay!

## 🎮 How It Works

1. **Live Parsing**: Every 5 minutes, the system checks for your latest HOI4 autosave
2. **Data Extraction**: Parses focus progress, country status, leaders, and politics  
3. **Tweet Generation**: Creates tweets based on current game state with real leaders
4. **Real-time Updates**: Your stream overlay updates with what's happening in your game

## 🚀 Quick Start

### Step 1: Test the Parser
Run the test to make sure everything works:
```bash
test_parse_autosave.bat
```

This will:
- Find your HOI4 saves directory
- Parse your latest autosave
- Create `data/game_data.json` with current game state

### Step 2: Start Live Parsing
Once the test works, start the live parser:
```bash
live_hoi4_parser.bat
```

This runs in the background, updating your game data every 5 minutes.

### Step 3: Start the Twitter Stream
In another window, start the streaming server:
```bash
cd streamer-tools/twitter-feed
python server.py
```

### Step 4: Start Auto-Generation
Visit `http://localhost:5000` and click "Start Auto Generation"

## 🛠️ Troubleshooting

### "HOI4 saves directory not found"
- Make sure Hearts of Iron IV is installed
- Check that you have save games in: `Documents/Paradox Interactive/Hearts of Iron IV/save games`
- Verify you've played at least one game that created autosaves

### "Parser not found"
The Rust parser needs to be built:
```bash
cd hoi4_parser
cargo build --release
```

### "No autosave files found"
- Make sure HOI4 is creating autosaves (check game settings)
- Play for a few minutes to generate an autosave
- Check that autosave files exist in your saves directory

### "Permission denied" 
- Run the batch files as Administrator if needed
- Make sure HOI4 isn't locking the save files (pause the game)

## ⚡ Performance Tips

### For Smooth Gameplay:
- Set parsing interval to 10-15 minutes for slower updates
- Use the test parser during breaks to check current state
- The parser works even while HOI4 is running

### For Active Streaming:
- Use 5-minute intervals for frequent updates
- Set Twitter generation to 15-30 seconds for active feed
- Enable debug mode to monitor what's happening

## 🎭 Live Stream Features

When connected to your real game, you'll see:

### Real Leaders Tweeting:
- **Adolf Hitler** tweeting about German Reich expansion
- **Winston Churchill** commenting on British Empire developments  
- **Joseph Stalin** discussing Soviet Union progress
- **Franklin Roosevelt** announcing American preparations

### Dynamic Country Names:
- Countries appear with ideological names based on current government
- "German Reich" vs "German Republic" depending on ruling party
- Real-time political changes reflected in tweets

### Actual Focus Progress:
- Leaders comment on focuses you're actually completing
- Citizens react to policies you're implementing  
- Journalists report on your diplomatic actions

### Live Political Situation:
- World powers status reflects current game state
- Stability, war support, and political power shown
- Military preparations and alliances tracked

## 📝 Configuration for Live Play

Edit `streamer-tools/twitter-feed/config.json`:

### Active Streaming:
```json
{
  "stream_settings": {
    "auto_generation_interval": 15
  },
  "persona_selection": {
    "leader_selection_chance": 0.8,
    "journalist_avoid_chance": 0.9
  }
}
```

### Commentary Mode:
```json
{
  "persona_selection": {
    "citizen_boost_chance": 0.6,
    "satirical_persona_chance": 0.3
  }
}
```

## 🔄 Workflow for Streaming

1. **Pre-Stream**: Run `test_parse_autosave.bat` to verify setup
2. **Start Stream**: Launch `live_hoi4_parser.bat` (keep running)  
3. **Start Server**: Launch Twitter server and enable auto-generation
4. **Play HOI4**: Every 5 minutes, tweets update with your current situation
5. **Monitor**: Watch your overlay for reactions to your political decisions

## 💡 Tips

- **Pause for Updates**: Pause HOI4 briefly when parsing runs for clean saves
- **Save Frequently**: Manual saves work too - the parser finds the newest file
- **Multiple Games**: Switch between campaigns - parser always finds latest
- **Multiplayer**: Works in multiplayer games if you're the host
- **Mods**: Should work with most mods that don't change save format

## 🎯 What Makes This Special

Unlike the static test data, live gameplay gives you:
- **Real consequences**: Citizens react to your actual decisions
- **Dynamic narrative**: Story evolves with your campaign 
- **Authentic reactions**: Leaders comment on real diplomatic situations
- **Emergent comedy**: Satirical personas respond to unexpected events
- **Historical immersion**: Famous leaders tweet about your alternate history

Your viewers will see an authentic "social media feed" from your alternate 1936 world, with real historical figures reacting to the chaos you're creating! 🎉