#!/bin/bash

echo "Starting server & desktop app"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start the server in a new terminal
echo "Starting server..."
cd "$SCRIPT_DIR/../transcriptions"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e "tell application \"Terminal\" to do script \"cd '$PWD' && echo 'Starting server...' && python3 server.py\""
else
    # Linux
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd '$PWD' && echo 'Starting server...' && python3 server.py; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$PWD' && echo 'Starting server...' && python3 server.py; exec bash" &
    else
        echo "No supported terminal found. Please run manually:"
        echo "  cd $PWD && python3 server.py"
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

echo "Both processes started in separate terminals"
