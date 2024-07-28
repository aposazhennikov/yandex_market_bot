import os
import time
import pandas as pd
import logging
from datetime import datetime
from xml.etree import ElementTree as ET
from xml.dom import minidom
from xml_converter import XMLGenerator, image_count
import re

# Настройка логирования
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
current_time = datetime.now().strftime("%Y_%m_%d_%H_%M")
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)


class ExcelComparator:
    def __init__(self, file_new, file_old):
        self.file_new = file_new
        self.file_old = file_old
        self.df_new = pd.read_excel(file_new, dtype={'xmlid': str})
        self.df_old = pd.read_excel(file_old, dtype={'xmlid': str})

    # Получение добавленных строк
    def get_added_rows(self):
        added_rows = self.df_new[~self.df_new['xmlid'].isin(
            self.df_old['xmlid'])]
        return added_rows

    # Получение удаленных строк
    def get_removed_rows(self):
        removed_rows = self.df_old[~self.df_old['xmlid'].isin(
            self.df_new['xmlid'])]
        return removed_rows

    # Получение обновленных цен
    def get_updated_price(self):
        merged = self.df_new.merge(
            self.df_old, on='xmlid', suffixes=('_new', '_old'))
        updated_price = merged[merged['price_new'] != merged['price_old']]
        return updated_price[['xmlid', 'price_new', 'price_old']]

    # Получение обновленных описаний
    def get_updated_description(self):
        merged = self.df_new.merge(
            self.df_old, on='xmlid', suffixes=('_new', '_old'))
        updated_description = merged[merged['description_new']
                                     != merged['description_old']]
        return updated_description[['xmlid', 'description_new', 'description_old']]

    # Генерация сводки изменений
    def generate_summary(self):
        added_rows = self.get_added_rows().to_dict(orient='records')
        removed_rows = self.get_removed_rows().to_dict(orient='records')
        updated_price = self.get_updated_price().to_dict(orient='records')
        updated_description = self.get_updated_description().to_dict(orient='records')

        summary = {
            "added_rows": added_rows if added_rows else "No changes",
            "removed_rows": removed_rows if removed_rows else "No changes",
            "updated_price": updated_price if updated_price else "No changes",
            "updated_description": updated_description if updated_description else "No changes"
        }

        return summary


def update_xml(file_xml, summary, products_file):
    xml_generator = XMLGenerator(products_file)

    tree = ET.parse(file_xml)
    root = tree.getroot()
    offers = root.find('shop').find('offers')

    # Удаление строк
    for removed in summary['removed_rows']:
        if isinstance(removed, dict):
            for offer in offers.findall('offer'):
                if offer.get('id') == removed['xmlid']:
                    logging.info(f"Удаление offer с ID {removed['xmlid']}")
                    offers.remove(offer)

    # Обновление цены
    for updated in summary['updated_price']:
        if isinstance(updated, dict):
            for offer in offers.findall('offer'):
                if offer.get('id') == updated['xmlid']:
                    price = offer.find('price')
                    if price is not None:
                        logging.info(f"Обновление цены для offer с ID {updated['xmlid']}: {
                                     price.text} -> {updated['price_new']}")
                        price.text = str(updated['price_new'])

    # Обновление описания
    for updated in summary['updated_description']:
        if isinstance(updated, dict):
            for offer in offers.findall('offer'):
                if offer.get('id') == updated['xmlid']:
                    description = offer.find('description')
                    if description is not None:
                        logging.info(f"Обновление описания для offer с ID {updated['xmlid']}: {
                                     description.text} -> {updated['description_new']}")
                        description.text = updated['description_new']

    # Добавление новых строк
    for added in summary['added_rows']:
        if isinstance(added, dict):
            logging.info(f"Добавление нового offer с ID {added['xmlid']}")
            product_data = xml_generator.process_product(added)
            if product_data:
                offer = ET.SubElement(
                    offers, "offer", id=str(product_data['xmlid']))
                name = ET.SubElement(offer, "name")
                name.text = product_data['name']
                vendor = ET.SubElement(offer, "vendor")
                vendor.text = product_data['vendor']
                count = ET.SubElement(offer, "count")
                count.text = "1"
                price = ET.SubElement(offer, "price")
                price.text = str(product_data['calculated_price'])
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
                warranty_days.text = "P1Y"
                service_life_days = ET.SubElement(offer, "service-life-days")
                service_life_days.text = "P1Y"
                dimensions = ET.SubElement(offer, "dimensions")
                dimensions.text = product_data['dimensions']
                weight = ET.SubElement(offer, "weight")
                weight.text = product_data['weight']

    # Удаление лишних пробелов и форматирование XML с отступами
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
    parsed_str = '\n'.join(
        [line for line in parsed_str.split('\n') if line.strip()])

    # Обновление даты в верхней строке
    current_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    parsed_str = re.sub(r'<yml_catalog date=".*?">',
                        f'<yml_catalog date="{current_date}">', parsed_str)

    with open(file_xml, "w", encoding="utf-8") as f:
        f.write(parsed_str)
    logging.info(f"XML файл успешно обновлен: {file_xml}")


def excel_main():
    if os.path.exists('products.xlsx') and os.path.exists('products_old.xlsx') and os.path.exists('products.xml'):
        file_new = 'products.xlsx'
        file_old = 'products_old.xlsx'
        file_xml = 'products.xml'

        comparator = ExcelComparator(file_new, file_old)
        summary = comparator.generate_summary()

        # Логирование сводки
        logger.info("Added Rows:")
        if summary['added_rows'] == "No changes":
            logger.info("No changes")
        else:
            for row in summary['added_rows']:
                logger.info(f"  {row}")

        logger.info("\nRemoved Rows:")
        if summary['removed_rows'] == "No changes":
            logger.info("No changes")
        else:
            for row in summary['removed_rows']:
                logger.info(f"  {row}")

        logger.info("\nUpdated Price:")
        if summary['updated_price'] == "No changes":
            logger.info("No changes")
        else:
            for row in summary['updated_price']:
                logger.info(f"  {row}")

        logger.info("\nUpdated Description:")
        if summary['updated_description'] == "No changes":
            logger.info("  No changes")
        else:
            for row in summary['updated_description']:
                logger.info(f"  {row}")

        if summary['removed_rows'] != "No changes" or summary['updated_price'] != "No changes" or summary['updated_description'] != "No changes":
            logger.info("Обнаружены изменения. Обновление XML файла.")
            update_xml(file_xml, summary, file_new)
        else:
            logger.info("Изменения не найдены.")

    else:
        logger.info(
            "Необходимые файлы не найдены. Запуск логики генерации XML файла.")
        start_time = time.time()
        generator = XMLGenerator("products.xlsx", image_count=image_count)
        products = generator.read_products()
        generator.generate_xml(products)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Скрипт выполнен за {total_time:.2f} секунд")


if __name__ == "__main__":
    excel_main()
