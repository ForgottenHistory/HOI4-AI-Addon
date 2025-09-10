@echo off
echo ==========================================
echo HOI4 AUTOSAVE PARSER - TEST RUN
echo ==========================================
echo This will parse your latest autosave once for testing
echo.

cd /d "%~dp0"

python parse_latest_autosave.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Parsing failed. Check the messages above.
    echo Make sure you have HOI4 save games and the parser is built.
) else (
    echo.
    echo [SUCCESS] Test completed! You can now run live_hoi4_parser.bat
)

echo.
pause