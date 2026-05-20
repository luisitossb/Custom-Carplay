#!/bin/bash
# CarPi startup script
# Runs on boot via XDG autostart after the desktop loads.
# Attempts iPhone reconnect, then launches the app.
# Restarts the app automatically if it crashes.

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IPHONE_MAC="A0:4E:CF:79:28:38"

# Wait for Bluetooth stack and desktop to be fully ready
sleep 8

# Try to reconnect iPhone (non-blocking — phone may not be nearby yet)
bluetoothctl connect "$IPHONE_MAC" 2>/dev/null &

# Activate venv
source "$PROJECT_DIR/carpi-env/bin/activate"
cd "$PROJECT_DIR"

python main.py
