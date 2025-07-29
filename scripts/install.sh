#!/bin/bash
set -e

echo "🔧 Встановлення системних залежностей..."
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip git wget libgl1

echo "📦 Створення Python-середовища..."
python3.10 -m venv venv
source venv/bin/activate

echo "📥 Встановлення Python-залежностей..."
pip install --upgrade pip
pip install -r requirements.txt


echo "🛠️ Створення systemd unit..."
cat <<SERVICE | sudo tee /etc/systemd/system/nutriscan.service > /dev/null
[Unit]
Description=NutriScan FastAPI Server
After=network.target

[Service]
User=root
WorkingDirectory=/opt/NutriScan
ExecStart=/opt/NutriScan/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

echo "🔁 Перезапуск systemd..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable nutriscan
sudo systemctl restart nutriscan

echo "✅ Установка завершена. Сервер працює на http://<IP>:8000"

