#!/bin/bash
set -e

APP_DIR="/opt/NutriScan"
APP_USER="nutriscan"

echo "=== NutriScan v2 Install ==="

# Create service user (no login)
if ! id "$APP_USER" &>/dev/null; then
    echo "Creating user $APP_USER..."
    sudo useradd --system --no-create-home --shell /usr/sbin/nologin "$APP_USER"
fi

# Python venv
echo "Setting up Python environment..."
python3 -m venv "$APP_DIR/venv"
source "$APP_DIR/venv/bin/activate"
pip install --upgrade pip --quiet
pip install -r "$APP_DIR/requirements.txt" --quiet

# Directories
mkdir -p "$APP_DIR/data" "$APP_DIR/logs"
chown -R "$APP_USER:$APP_USER" "$APP_DIR/data" "$APP_DIR/logs"

# API service
echo "Creating systemd services..."
cat <<'SERVICE' | sudo tee /etc/systemd/system/nutriscan.service > /dev/null
[Unit]
Description=NutriScan API v2
After=network.target

[Service]
Type=exec
User=nutriscan
WorkingDirectory=/opt/NutriScan
EnvironmentFile=/opt/NutriScan/.env
ExecStart=/opt/NutriScan/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

# Bot service
cat <<'SERVICE' | sudo tee /etc/systemd/system/nutriscan-bot.service > /dev/null
[Unit]
Description=NutriScan Telegram Bot v2
After=network.target nutriscan.service

[Service]
Type=exec
User=nutriscan
WorkingDirectory=/opt/NutriScan
EnvironmentFile=/opt/NutriScan/.env
ExecStart=/opt/NutriScan/venv/bin/python -m bot.telegram
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable nutriscan nutriscan-bot
sudo systemctl restart nutriscan nutriscan-bot

echo "=== Done ==="
echo "API: http://127.0.0.1:8000"
echo "Health: http://127.0.0.1:8000/health"
echo "Test page: http://127.0.0.1:8000/"
echo "Dashboard: http://127.0.0.1:8000/stats/dashboard"
