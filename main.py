import asyncio
import os
from telethon import TelegramClient, events
import logging
from excel_main import excel_main

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


async def main():
    # Создание клиента
    client = TelegramClient(session_name, api_id, api_hash)

    async with client:
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
            # Ждать 30 секунд перед следующей отправкой сообщения
            logging.info("Сплю на 30 секунд")
            await asyncio.sleep(30)

# Запуск клиента и выполнение задачи
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
