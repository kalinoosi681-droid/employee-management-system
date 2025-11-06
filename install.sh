#!/bin/sh
set -e
echo "Updating Termux packages..."
pkg update -y && pkg upgrade -y
echo "Installing Python and Git..."
pkg install -y python git
echo "Installing required Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Installation complete."
