@echo off
echo Starting Breaking News Ticker System...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment should be used
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install requirements if needed
if not exist "requirements_installed.flag" (
    echo Installing requirements...
    pip install -r requirements.txt
    if errorlevel 0 (
        echo. > requirements_installed.flag
    ) else (
        echo Failed to install requirements
        pause
        exit /b 1
    )
)

echo.
echo Starting services...
echo.
echo Web Server will be available at: http://localhost:5001
echo Add this URL to your OBS Browser Source
echo.
echo Press Ctrl+C to stop both services
echo.

REM Start both services
start "Breaking News Server" cmd /k "python server.py --host 0.0.0.0 --port 5001"
timeout /t 3 /nobreak >nul

start "Headline Generator" cmd /k "python headline_generator.py --interval 30"

echo Both services started!
echo.
echo - Server: http://localhost:5001 (for OBS)
echo - Generator: Running in background
echo.
echo Close both windows to stop the services.
pause