#!/bin/bash

echo "Starting transcription server, meeting microservice & desktop app"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start the transcription server in a new terminal
echo "Starting transcription server..."
cd "$SCRIPT_DIR/../src/transcription"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e "tell application \"Terminal\" to do script \"cd '$PWD' && echo 'Starting transcription server...' && python3 server.py\""
else
    # Linux
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd '$PWD' && echo 'Starting transcription server...' && python3 server.py; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$PWD' && echo 'Starting transcription server...' && python3 server.py; exec bash" &
    else
        echo "No supported terminal found. Please run manually:"
        echo "  cd $PWD && python3 server.py"
    fi
fi

# Start the meeting microservice in a new terminal
echo "Starting meeting microservice..."
cd "$SCRIPT_DIR/../../MeetingAssistant"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e "tell application \"Terminal\" to do script \"cd '$PWD' && echo 'Starting meeting microservice...' && python3 meeting_microservice.py\""
else
    # Linux
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd '$PWD' && echo 'Starting meeting microservice...' && python3 meeting_microservice.py; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$PWD' && echo 'Starting meeting microservice...' && python3 meeting_microservice.py; exec bash" &
    else
        echo "No supported terminal found. Please run manually:"
        echo "  cd $PWD && python3 meeting_microservice.py"
    fi
fi

# Start the desktop app in a new terminal
echo "Starting desktop app..."
cd "$SCRIPT_DIR/../src"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e "tell application \"Terminal\" to do script \"cd '$PWD' && echo 'Starting desktop app...' && python3 main.py\""
else
    # Linux
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd '$PWD' && echo 'Starting desktop app...' && python3 main.py; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$PWD' && echo 'Starting desktop app...' && python3 main.py; exec bash" &
    else
        echo "No supported terminal found. Please run manually:"
        echo "  cd $PWD && python3 main.py"
    fi
fi

echo "All three processes started in separate terminals"
