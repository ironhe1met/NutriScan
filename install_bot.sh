#!/bin/bash

# Встановлюємо шлях до сервісу
SERVICE_FILE="nutriscan-bot.service"
TARGET_PATH="/etc/systemd/system/${SERVICE_FILE}"

# Перевірка існування .env і витяг BOT_TOKEN
if [ ! -f .env ]; then
  echo "❌ Файл .env не знайдено. Створи його та додай BOT_TOKEN перед запуском."
  exit 1
fi

BOT_TOKEN=$(grep ^BOT_TOKEN .env | cut -d '=' -f2)

if [ -z "$BOT_TOKEN" ]; then
  echo "❌ BOT_TOKEN у .env не знайдено або порожній."
  exit 1
fi

# Створюємо сервіс-файл тимчасово
echo "🔧 Генеруємо systemd сервіс..."
cat > /tmp/${SERVICE_FILE} <<EOF
[Unit]
Description=NutriScan Telegram Bot
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=$(pwd)
ExecStart=$(which python3) bot/telegram_bot.py
Restart=on-failure
Environment=BOT_TOKEN=${BOT_TOKEN}

[Install]
WantedBy=multi-user.target
EOF

# Копіюємо сервіс
sudo cp /tmp/${SERVICE_FILE} ${TARGET_PATH}
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable nutriscan-bot
sudo systemctl restart nutriscan-bot

echo "✅ Сервіс nutriscan-bot встановлено та запущено."
