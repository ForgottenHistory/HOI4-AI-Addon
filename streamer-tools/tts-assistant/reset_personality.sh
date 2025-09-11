#!/bin/bash
echo "========================================"
echo "   TTS Assistant Personality Reset"
echo "========================================"
echo

if [ -f "current_personality.json" ]; then
    echo "Current personality found. Removing..."
    rm current_personality.json
    echo "✓ Personality reset successfully!"
    echo
    echo "Next time you start the assistant, you'll get a new random personality."
else
    echo "No current personality file found."
    echo "Next startup will generate a new personality automatically."
fi

echo
echo "========================================"