#!/bin/bash
set -e

echo "🔧 Встановлення системних залежностей..."
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip git wget

echo "📦 Створення Python-середовища..."
python3.10 -m venv venv
source venv/bin/activate

echo "📥 Встановлення Python-залежностей..."
pip install --upgrade pip
pip install -r requirements.txt

echo "⬇️ Завантаження моделей..."
bash scripts/download_models.sh

echo "✅ Установка завершена"
