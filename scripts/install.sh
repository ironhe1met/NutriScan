#!/bin/bash
set -e

echo "🔧 Installing system packages..."
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip

echo "📦 Creating virtual environment..."
python3.10 -m venv venv
source venv/bin/activate

echo "📥 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# echo "📁 Завантаження моделей..."
# bash scripts/download_models.sh

echo "✅ Installation complete"
