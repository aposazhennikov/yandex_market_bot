#!/bin/bash
touch /var/log/screen.log
screen -dmS yandex_market_bot bash -c "source /opt/venv/bin/activate && python main.py > /var/log/screen.log 2>&1"
tail -f /var/log/screen.log
