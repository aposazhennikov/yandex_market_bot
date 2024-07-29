import re
import backoff
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import html
import json
from openai import OpenAI, RateLimitError
from PIL import Image
from io import BytesIO
import httpx

# Настройка прокси
proxy_url = os.getenv('OPENAI_PROXY_URL')
# Количество pictures которое ищем для каждой карточки!
image_count = int(os.getenv('IMAGE_COUNT', '15'))
# Настройка логирования
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# Логирование в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Добавление обработчиков
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)

# API ключ ChatGPT
api_key = os.getenv('OPENAI_API_KEY')

# Создание клиента OpenAI
# client = OpenAI(api_key=api_key)
client = OpenAI(api_key=api_key, http_client=httpx.Client(
    proxies=proxy_url)) if proxy_url else OpenAI(api_key=api_key)


class ImageSearcher:
    def __init__(self):
        self.base_url = "https://www.bing.com/images/search?q="

    def is_valid_image(self, url):
        try:
            # Проверка длины URL
            if len(url) > 512:
                logging.warning(f"URL слишком длинный: {url}")
                return False

            # Проверка соответствия URL стандарту RFC-1738
            rfc_1738_regex = re.compile(
                r'^(?:http|https)://'
                r'(?:\S+(?::\S*)?@)?'
                r'(?:[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*|'
                r'\[[0-9a-fA-F:.]+\])'
                r'(?::\d{2,5})?'
                r'(?:/[^\s]*)?$'
            )

            if not rfc_1738_regex.match(url):
                logging.warning(
                    f"URL не соответствует стандарту RFC-1738: {url}")
                return False

            # Проверка заголовков
            response = requests.head(url, timeout=10)
            content_type = response.headers.get('Content-Type')
            if content_type not in ['image/jpeg', 'image/png', 'image/webp']:
                return False

            content_length = int(response.headers.get('Content-Length', 0))
            if content_length > 10 * 1024 * 1024:  # Проверка размера
                return False

            # Проверка размеров изображения
            response = requests.get(url, timeout=10)
            img = Image.open(BytesIO(response.content))
            if img.width < 300 or img.height < 300:
                return False

            return True
        except Exception as e:
            logging.error(f"Ошибка при проверке изображения: {e}")
            return False

    def get_image_urls(self, query, image_count=image_count, retries=10):
        url = f"{self.base_url}{query.replace(' ', '+')}"
        all_images = []
        for attempt in range(retries):
            try:
                logging.info(f"Поиск изображений для: {
                             query}, попытка {attempt + 1}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                img_tags = soup.find_all('a', {'class': 'iusc'})
                if img_tags:
                    for img_tag in img_tags:
                        m = img_tag.get('m')
                        img_url = m.split('"murl":"')[1].split('"')[0]
                        if self.is_valid_image(img_url):
                            logging.info(
                                f"Изображение найдено и валидно: {img_url}")
                            all_images.append(img_url)
                            if len(all_images) >= image_count:
                                return all_images
                        else:
                            logging.warning(
                                f"Изображение не валидно: {img_url}")
                logging.warning(f"Изображения не найдены для: {
                                query}, попытка {attempt + 1}")
            except (requests.RequestException, IndexError) as e:
                logging.error(f"Ошибка при поиске изображений для: {
                              query}, попытка {attempt + 1}: {e}")
                time.sleep(1)
        logging.warning(f"Изображения не найдены для: {
                        query} после {retries} попыток")
        return all_images


class XMLGenerator:
    def __init__(self, products_file, image_count=image_count):
        self.products_file = products_file
        self.image_searcher = ImageSearcher()
        self.image_count = image_count

    def read_products(self):
        logging.info(f"Чтение данных из файла: {self.products_file}")
        return pd.read_excel(self.products_file, usecols=['xmlid', 'description', 'price'], dtype={'xmlid': str})

    def calculate_price(self, price):
        if price < 20000:
            return price * 1.32
        elif 20000 <= price < 35000:
            return price * 1.31
        elif 35000 <= price < 60000:
            return price * 1.30
        elif 60000 <= price < 85000:
            return price * 1.29
        elif 85000 <= price < 105000:
            return price * 1.28
        else:
            return price * 1.275

    def extract_vendor(self, description):
        words = description.split()
        for word in words:
            if word.isalpha() and not word.endswith('.'):
                return word
        return "NULL"

    @staticmethod
    def get_product_details_from_gpt(product_description, max_retries=10):
        assistant_id = os.getenv('ASSISTANT_ID')
        attempt = 0

        while attempt < max_retries:
            attempt += 1
            try:
                # Создание потока сообщений
                thread = client.beta.threads.create(
                    messages=[
                        {"role": "user", "content": product_description}
                    ]
                )
                logging.info(f"Thread created: {thread.id}")

                # Создание и выполнение запуска
                run = client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=assistant_id,
                )
                logging.info(f"Run created: {run.id}")

                status = run.status

                while status not in ['completed', 'failed', 'cancelled']:
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(
                        thread_id=thread.id, run_id=run.id)
                    status = run.status
                    logging.info(f"Run status: {status}")

                messages = client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                logging.info(f"Messages retrieved: {len(messages.data)}")

                for message in messages.data:
                    logging.info(f"Message role: {message.role}")
                    if message.role == 'assistant':
                        content = ''.join(
                            [content_block.text.value for content_block in message.content if content_block.type == 'text'])
                        logging.info(f"Assistant response content: {content}")
                        response_data = json.loads(content)
                        dimensions = response_data.get("dimensions", "")
                        weight = response_data.get("weight", "")
                        vendor = response_data.get("vendor", "")
                        categoryId = response_data.get("categoryId", "")
                        name = response_data.get("name", "")
                        description = response_data.get("description", "")

                        logging.info(f"Ответ GPT получен: {
                                     dimensions, weight, vendor, categoryId, name, description}\n")
                        return dimensions, weight, vendor, categoryId, name, description

                logging.error(f"Ответ для GPT НЕ получен!! {
                              messages.data}\n\nОшибка GPT:{messages}")

            except Exception as e:
                logging.error(f"Ошибка при попытке {attempt}: {str(e)}")

        logging.error(f"Все {max_retries} попытки завершились неудачей")
        return None, None, None, None, None, None

    @backoff.on_exception(backoff.expo, RateLimitError)
    def process_product(self, row):
        if "обменка" in row['description'].lower():
            logging.info(f"Пропуск товара с ID: {
                         row['xmlid']} из-за слова 'обменка'")
            return None
        result_from_gpt = self.get_product_details_from_gpt(
            f'json: {row["description"]}')
        product_data = {}
        product_data['xmlid'] = row['xmlid']

        if result_from_gpt[4] != "" and result_from_gpt[4] != None:
            product_data['name'] = result_from_gpt[4]
        else:
            product_data['name'] = html.unescape(row['description'])

        if result_from_gpt[5] != "" and result_from_gpt[5] != None:
            product_data['description'] = result_from_gpt[5]
        else:
            product_data['description'] = html.unescape(row['description'])

        if result_from_gpt[2] != "" and result_from_gpt[2] != None:
            product_data['vendor'] = result_from_gpt[2]
        else:
            product_data['vendor'] = self.extract_vendor(
                html.unescape(row['description']))
        product_data['price'] = row['price']
        product_data['calculated_price'] = self.calculate_price(row['price'])

        all_images = self.image_searcher.get_image_urls(result_from_gpt[4] if result_from_gpt[4] not in [
                                                        "", None] else row['description'], self.image_count)

        product_data['pictures'] = all_images
        product_data['dimensions'] = result_from_gpt[0]
        product_data['weight'] = result_from_gpt[1]
        product_data['categoryId'] = result_from_gpt[3]

        time.sleep(0.06)
        return product_data

    def generate_xml(self, products):
        logging.info("Генерация XML файла")
        yml_catalog = ET.Element(
            "yml_catalog", date=datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"))
        shop = ET.SubElement(yml_catalog, "shop")
        name = ET.SubElement(shop, "name")
        name.text = "smart-dostup"
        categories_dict = {
            1: "Uncategorized",
            2: "СМАРТФОНЫ",
            3: "ПЛАНШЕТЫ",
            4: "ЧАСЫ",
            5: "НАУШНИКИ",
            6: "КОЛОНКИ",
            7: "АКСЕССУАРЫ",
            8: "ИГРОВЫЕ КОНСОЛИ",
            9: "GO PRO",
            10: "ТЕЛЕФОНЫ ПРОТИВОУДАРНЫЕ",
            11: "ТЕЛЕФОНЫ КНОПОЧНЫЕ",
            12: "НОУТБУКИ",
            13: "ФЕН СТАЙЛЕР",
            14: "ПЫЛЕСОСЫ"
        }

        categories = ET.SubElement(shop, "categories")
        for i in range(1, 15):
            category = ET.SubElement(categories, "category", id=str(i))
            category.text = categories_dict[i]

        offers = ET.SubElement(shop, "offers")
        product_count = 0
        total_products = len(products)
        start_time = time.time()

        # Определение количества потоков
        # num_cores = os.cpu_count()
        # max_workers = num_cores * 2  # Для I/O задач можно увеличить количество потоков
        if os.cpu_count() <= 4:
            max_workers = os.cpu_count() * 4
        else:
            max_workers = os.cpu_count() * 2

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_product = {
                executor.submit(self.process_product, row): row for index, row in products.iterrows()
            }
            for future in as_completed(future_to_product):
                product_count += 1
                row = future_to_product[future]
                try:
                    product_data = future.result()
                    if product_data is None:
                        continue
                    logging.info(f"Обработка товара с ID: {product_data['xmlid']} ({
                                 product_count}/{total_products}), осталось {total_products - product_count}")
                    logging.info(f"Цена для товара ID {product_data['xmlid']} до наценки: {
                                 product_data['price']}, после наценки: {product_data['calculated_price']}")

                    offer = ET.SubElement(
                        offers, "offer", id=str(product_data['xmlid']))
                    name = ET.SubElement(offer, "name")
                    name.text = product_data['name']
                    vendor = ET.SubElement(offer, "vendor")
                    vendor.text = product_data['vendor']
                    count = ET.SubElement(offer, "count")
                    count.text = "1"
                    archived = ET.SubElement(offer, "archived")
                    archived.text = "false"
                    disabled = ET.SubElement(offer, "disabled")
                    disabled.text = "false"
                    price = ET.SubElement(offer, "price")
                    price.text = str(
                        round(product_data['calculated_price'], 2))
                    categoryId = ET.SubElement(offer, "categoryId")
                    categoryId.text = product_data['categoryId'] if product_data['categoryId'] else "1"
                    currencyId = ET.SubElement(offer, "currencyId")
                    currencyId.text = "RUR"
                    description = ET.SubElement(offer, "description")
                    description.text = product_data['description']

                    for image_url in product_data.get('pictures', []):
                        picture = ET.SubElement(offer, "picture")
                        picture.text = image_url

                    warranty_days = ET.SubElement(offer, "warranty-days")
                    # Один год значение от Яндекс Маркет
                    warranty_days.text = "P1Y"
                    service_life_days = ET.SubElement(
                        offer, "service-life-days")
                    # Один год значение от Яндекс Маркет
                    service_life_days.text = "P1Y"
                    dimensions = ET.SubElement(offer, "dimensions")
                    dimensions.text = product_data['dimensions']
                    weight = ET.SubElement(offer, "weight")
                    weight.text = product_data['weight']

                except Exception as exc:
                    logging.error(f"Ошибка обработки товара с ID: {
                                  row['xmlid']}: {exc}")

                offer_end_time = time.time()
                average_time_per_offer = (
                    offer_end_time - start_time) / product_count
                estimated_time_remaining = average_time_per_offer * \
                    (total_products - product_count)
                logging.info(f"Среднее время на обработку одного товара: {
                             average_time_per_offer:.2f} секунд. Примерное оставшееся время: {estimated_time_remaining:.2f} секунд.")

        # Форматирование XML с отступами
        xml_str = ET.tostring(yml_catalog, encoding='utf-8')
        parsed_str = minidom.parseString(xml_str).toprettyxml(indent="  ")

        output_file = "products.xml"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(parsed_str)

        logging.info(f"XML файл успешно создан: {output_file}")
        logging.info(f"Обработано товаров: {product_count}")


if __name__ == "__main__":
    start_time = time.time()
    generator = XMLGenerator("products.xlsx", image_count=image_count)
    products = generator.read_products()
    generator.generate_xml(products)
    end_time = time.time()
    total_time = end_time - start_time
    logging.info(f"Скрипт выполнен за {total_time:.2f} секунд")
