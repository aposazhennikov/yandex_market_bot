import asyncio
import os
from telethon import TelegramClient, events
import logging
from excel_main import excel_main
from flask import Flask, render_template, request, jsonify
import json
import threading

# Настройки логирования
logging.basicConfig(level=logging.INFO)

# Получение значений из переменных окружения
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone_number = os.getenv('PHONE_NUMBER')
chat_id = int(os.getenv('CHAT_ID', '-6567723695'))

# Время в секундах через которое автоматически перезапускать скрипт
delay_time = int(os.getenv('DELAY_TIME', '30'))
session_name = 'session_name'

# Имя пользователя вашего бота
bot_username = os.getenv('BOT_USERNAME', 'pavilion89bot')

app = Flask(__name__)
rules_file = 'rules.json'


def load_rules():
    if not os.path.exists(rules_file):
        save_rules({})
    with open(rules_file, 'r') as file:
        return json.load(file)


def save_rules(rules):
    with open(rules_file, 'w') as file:
        json.dump(rules, file)


@app.before_request
def before_request():
    if request.headers.get('X-Script-Name'):
        url_prefix = request.headers['X-Script-Name']
        if request.path.startswith(url_prefix):
            request.environ['SCRIPT_NAME'] = url_prefix
            request.environ['PATH_INFO'] = request.path[len(url_prefix):]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_rules', methods=['GET'])
def get_rules():
    rules = load_rules()
    return jsonify(rules)


@app.route('/add_rule', methods=['POST'])
def add_rule():
    data = request.get_json()
    rules = load_rules()
    for rule in data:
        rules[rule['id']] = rule['price']
    save_rules(rules)
    return jsonify(success=True)


@app.route('/delete_all_rules', methods=['POST'])
def delete_all_rules():
    save_rules({})
    return jsonify(success=True)


@app.route('/delete_rule/<rule_id>', methods=['POST'])
def delete_rule(rule_id):
    rules = load_rules()
    if rule_id in rules:
        del rules[rule_id]
        save_rules(rules)
    return jsonify(success=True)


@app.route('/edit_rule', methods=['POST'])
def edit_rule():
    data = request.get_json()
    rules = load_rules()
    rules[data['id']] = data['price']
    save_rules(rules)
    return jsonify(success=True)


async def telegram_client():
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        if event.document:
            # Если файл уже существует, переименовать его
            if os.path.exists('products.xlsx'):
                if os.path.exists('products_old.xlsx'):
                    os.remove('products_old.xlsx')
                os.rename('products.xlsx', 'products_old.xlsx')

            # Скачать документ и сохранить его в файл
            file_path = await event.download_media(file='products.xlsx')
            logging.info(f"Файл скачан и сохранен по пути: {file_path}")
            # Запуск скрипта сравнения и обновления XML
            excel_main()

    while True:
        logging.info("Отправка сообщения боту для получения Excel файла")
        await client.send_message(bot_username, 'Получить Excel-файл')
        logging.info("Сплю на 30 секунд")
        await asyncio.sleep(delay_time)


def start_flask_app():
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)


if __name__ == '__main__':
    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.start()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(telegram_client())
