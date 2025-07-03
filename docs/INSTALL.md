# Встановлення NutriScan

## 1. Клонування проєкту
```bash
git clone https://github.com/ironhe1met/NutriScan.git
cd NutriScan
```
## 2. Запуск інсталятора
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```
## 3. Запуск сервера
```bash
./scripts/run_server.sh
```
## 4. Тестування
```bash
pytest tests/
```

## 🛠 **scripts/install.sh** — встановлення сервісу (на кожному етапі оновлюється)

```bash
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
```
