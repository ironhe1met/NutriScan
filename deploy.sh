#!/bin/bash
set -e

APP_DIR="/opt/NutriScan"

echo "Updating repository..."
cd "$APP_DIR"
git pull origin main

echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet

echo "Restarting services..."
sudo systemctl restart nutriscan
sudo systemctl restart nutriscan-bot

echo "Done. Checking status..."
sudo systemctl is-active nutriscan
sudo systemctl is-active nutriscan-bot
