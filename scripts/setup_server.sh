#!/bin/bash
# Автоматичне налаштування сервера для NutriScan
set -e

# Оновлення списку пакетів і встановлення Python
apt update
apt install -y python3 python3-venv python3-pip

# Створення та активація віртуального середовища
python3 -m venv venv
source venv/bin/activate

# Встановлення залежностей
pip install -r requirements.txt

# Завантаження ваг моделей
python scripts/download_weights.py

# Запуск сервера
python run.py
