# Інструкція з налаштування сервера

1. **Встановіть Python 3.10+** та менеджер пакетів `pip`.
2. **Опціонально:** створіть віртуальне середовище:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Скопіюйте проект** на сервер, наприклад у каталог `/opt/nutriscan`:
   ```bash
   mkdir -p /opt
   git clone <repo> /opt/nutriscan
   cd /opt/nutriscan
   ```
4. **Встановіть залежності:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Завантажте ваги моделей:**
   ```bash
   python scripts/download_weights.py
   ```
6. **Запустіть сервер:**
   ```bash
   python run.py
   ```
   API буде доступний на `http://<server-ip>:8000`.

7. **Автоматична установка:** запустіть `sudo bash scripts/setup_server.sh`.

При необхідності налаштуйте reverse proxy (наприклад, Nginx) та службу systemd для автозапуску.
