#!/bin/bash
# setup.sh — Run once on your Raspberry Pi to set up the project
# Usage: bash setup.sh

set -e

echo "========================================"
echo "  LD2410S Human Detection System Setup"
echo "========================================"

# 1. Install pyserial via apt (safe for Pi OS)
echo ""
echo "[1/3] Installing python3-serial..."
sudo apt update -qq
sudo apt install -y python3-serial

# 2. Add current user to dialout group (for UART access without sudo)
echo ""
echo "[2/3] Adding $USER to dialout group..."
sudo usermod -aG dialout "$USER"

# 3. Make main.py executable
echo ""
echo "[3/3] Setting permissions..."
chmod +x src/main.py

echo ""
echo "========================================"
echo "  Setup complete!"
echo ""
echo "  IMPORTANT NEXT STEPS:"
echo "  1. Configure /boot/config.txt (see docs/uart_config.md)"
echo "  2. Reboot: sudo reboot"
echo "  3. After reboot, verify: ls /dev/ttyAMA*"
echo "  4. Run: python3 src/main.py"
echo "========================================"
