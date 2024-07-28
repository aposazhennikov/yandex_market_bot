#!/bin/bash

# Создание файла логов
touch /var/log/screen.log

# Запуск скрипта в screen сессии в фоновом режиме
screen -dmS yandex_market_bot bash -c "source /opt/venv/bin/activate && python main.py > /var/log/screen.log 2>&1"

# Отображение логов в реальном времени
tail -f /var/log/screen.log
