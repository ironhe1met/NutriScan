#!/bin/bash
set -e

echo "📁 Перехід до проєкту..."
cd /opt/NutriScan

echo "🔄 Оновлення репозиторію..."
git pull origin main

echo "🐍 Активація віртуального середовища..."
source venv/bin/activate

echo "📦 Оновлення залежностей..."
pip install -r requirements.txt

echo "🚀 Перезапуск FastAPI-сервера..."
# Якщо використовуєш systemd:
# systemctl restart nutricsan.service

# Або через скрипт:
bash scripts/run_server.sh
