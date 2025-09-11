@echo off
echo ========================================
echo    TTS Assistant Personality Reset
echo ========================================
echo.
if exist current_personality.json (
    echo Current personality found. Removing...
    del current_personality.json
    echo ✓ Personality reset successfully!
    echo.
    echo Next time you start the assistant, you'll get a new random personality.
) else (
    echo No current personality file found.
    echo Next startup will generate a new personality automatically.
)
echo.
echo ========================================
pause