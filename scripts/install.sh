#!/bin/bash

echo "🔧 Встановлення залежностей..."
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip git

echo "📦 Створення venv..."
python3.10 -m venv venv
source venv/bin/activate

echo "📥 Встановлення requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📁 Завантаження моделей..."
bash scripts/download_models.sh

echo "✅ Установка завершена"
