#!/bin/bash
# Run this ONCE on the Pi to configure CarPi to launch on boot.
# Usage: bash scripts/setup-autostart.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/carpi.desktop"

echo "Setting up CarPi autostart..."
echo "Project path: $PROJECT_DIR"

# Make start.sh executable
chmod +x "$SCRIPT_DIR/start.sh"

# Create XDG autostart directory if it doesn't exist
mkdir -p "$AUTOSTART_DIR"

# Write the .desktop autostart entry
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=CarPi
Comment=CarPlay-style dashboard
Exec=bash $SCRIPT_DIR/start.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo ""
echo "Done! CarPi will launch automatically on next boot."
echo ""
echo "To test right now without rebooting:"
echo "  bash $SCRIPT_DIR/start.sh"
echo ""
echo "To disable autostart later:"
echo "  rm $DESKTOP_FILE"
