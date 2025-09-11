#!/bin/bash

echo "Starting Breaking News Ticker System..."
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment should be used
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo
echo "Starting services..."
echo
echo "Web Server will be available at: http://localhost:5001"
echo "Add this URL to your OBS Browser Source"
echo
echo "Press Ctrl+C to stop both services"
echo

# Function to handle cleanup
cleanup() {
    echo
    echo "Stopping services..."
    kill $SERVER_PID $GENERATOR_PID 2>/dev/null
    wait $SERVER_PID $GENERATOR_PID 2>/dev/null
    echo "Services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the server in background
echo "Starting web server..."
python3 server.py --host 0.0.0.0 --port 5001 &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

# Start the headline generator in background
echo "Starting headline generator..."
python3 headline_generator.py --interval 30 &
GENERATOR_PID=$!

echo
echo "Both services started!"
echo
echo "- Server: http://localhost:5001 (for OBS)"
echo "- Generator: Running in background"
echo "- Server PID: $SERVER_PID"
echo "- Generator PID: $GENERATOR_PID"
echo
echo "Press Ctrl+C to stop both services"
echo

# Wait for both processes
wait $SERVER_PID $GENERATOR_PID