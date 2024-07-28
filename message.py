import asyncio
import json
import logging
from openai import OpenAI, RateLimitError
import backoff

# Настройка логгирования
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Установите ваш API ключ
api_key = ''

# Создание клиента OpenAI
client = OpenAI(api_key=api_key)


@backoff.on_exception(backoff.expo, RateLimitError)
async def get_product_details_from_gpt(product_description):
    assistant_id = ''

    try:
        logging.debug('Создание потока сообщений')
        # Создание потока сообщений
        thread = await asyncio.to_thread(client.beta.threads.create,
                                         messages=[
                                             {"role": "user",
                                                 "content": product_description}
                                         ]
                                         )
        logging.debug(f'Поток сообщений создан: {thread.id}')

        logging.debug('Создание и выполнение запуска')
        # Создание и выполнение запуска
        run = await asyncio.to_thread(client.beta.threads.runs.create,
                                      thread_id=thread.id,
                                      assistant_id=assistant_id,
                                      )
        logging.debug(f'Запуск создан: {run.id}')

        status = run.status

        while status not in ['completed', 'failed', 'cancelled']:
            logging.debug(f'Статус выполнения: {
                          status}. Ожидание завершения...')
            await asyncio.sleep(1)
            run = await asyncio.to_thread(client.beta.threads.runs.retrieve,
                                          thread_id=thread.id, run_id=run.id)
            status = run.status

        logging.debug(f'Запуск завершен со статусом: {status}')

        logging.debug('Получение сообщений из потока')
        messages = await asyncio.to_thread(client.beta.threads.messages.list,
                                           thread_id=thread.id
                                           )

        for message in messages.data:
            if message.role == 'assistant':
                logging.debug('Сообщение от ассистента получено')
                content = ''.join(
                    [content_block.text.value for content_block in message.content if content_block.type == 'text'])
                logging.debug(f'Содержимое сообщения: {content}')
                response_data = json.loads(content)
                dimensions = response_data.get("dimensions", "")
                weight = response_data.get("weight", "")
                vendor = response_data.get("vendor", "")
                categoryId = response_data.get("categoryId", "")
                name = response_data.get("name", "")
                description = response_data.get("description", "")

                return dimensions, weight, vendor, categoryId, name, description
            else:
                logging.warning('Сообщение от ассистента не получено')
                return None, None, None, None, None, None
        else:
            logging.error('Сообщение от ассистента не найдено')
            return None, None, None, None, None, None
    except Exception as e:
        logging.error(f'Ошибка во время выполнения: {e}', exc_info=True)
        return None, None, None, None, None, None

product_description = "json: Apple iPad Pro 12.9 M2 128Gb Wi-Fi Silver"
dimensions, weight, vendor, categoryId, name, description = asyncio.run(
    get_product_details_from_gpt(product_description))
print(dimensions, weight, vendor, categoryId, name, description)
