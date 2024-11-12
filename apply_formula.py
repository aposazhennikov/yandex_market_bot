import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd
import logging


# Этот скрипт - костыль для сиюминутного обновления цен в тофарах, если мы например изменили формулу.
# ЧТобы не осталось товаров со старой ценой
# Далее будут более подробные комменты, смотри ниже


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        # Логирование в файл
        logging.FileHandler("apply_formula.log", mode='w'),
        logging.StreamHandler()  # Логирование в консоль
    ]
)
# Функция для высчитывания цены в итоговом файле Products.xml


def calculate_price(price):
    if price < 10000:
        return price * 1.45
    elif 10000 <= price < 11000:
        return price * 1.43
    elif 11000 <= price < 13000:
        return price * 1.42
    elif 13000 <= price < 15000:
        return price * 1.41
    elif 15000 <= price < 18000:
        return price * 1.395
    elif 18000 <= price < 20000:
        return price * 1.387
    elif 20000 <= price < 30000:
        return price * 1.36
    elif 30000 <= price < 40000:
        return price * 1.35
    elif 40000 <= price < 50000:
        return price * 1.34
    elif 50000 <= price < 60000:
        return price * 1.33
    elif 60000 <= price < 70000:
        return price * 1.325
    elif 70000 <= price < 80000:
        return price * 1.318
    elif 80000 <= price < 90000:
        return price * 1.315
    elif 90000 <= price < 100000:
        return price * 1.308
    elif price >= 100000:
        return price * 1.305


def load_prices_from_excel(excel_file):
    logging.info(f"Загрузка данных из Excel-файла: {excel_file}")
    df = pd.read_excel(excel_file, dtype={'xmlid': str, 'price': float})
    prices_dict = {row['xmlid']: row['price'] for _, row in df.iterrows()}
    logging.info(f"Загружено {len(prices_dict)} товаров из Excel.")
    return prices_dict


def update_prices_in_xml(file_xml, prices_from_excel):
    logging.info(f"Обновление цен в XML-файле: {file_xml}")
    tree = ET.parse(file_xml)
    root = tree.getroot()

    # Ищем в структуре XML файла <offer>, в нем цену, получаем цену из EXCEL и сравниваем с нашей формулой, если не совпадает ->
    # меняеем цену в XML файле в данном конкретном <offer> </offer>
    # Также если товар есть в Products.xml но нет в excel(ищем по ID) то ставим цену товару '100' и архивируем/отключаем
    # И за одно проверяем нет ли никаких товаров с ценой 100, которые не были почеуму-то заархивированы и выключены, если такие есть
    # то архивируем и отключаем еще и их.
    for offer in root.find('shop').find('offers').findall('offer'):

        price_element = offer.find('price')

        if price_element is not None:
            xmlid = offer.get('id')

            if xmlid in prices_from_excel:
                # Получаем исходную цену из Excel
                original_price = prices_from_excel[xmlid]
                # Пересчитываем цену по новой формуле
                new_price = calculate_price(original_price)
                # Обновляем цену в XML
                price_element.text = f"{new_price:.2f}"
                logging.info(f"Обновлена цена для offer с ID {xmlid}: {
                             original_price} -> {new_price:.2f}")
            else:
                # Если xmlid нет в Excel, устанавливаем цену на "100" и архивируем товар
                price_element.text = "100.00"
                logging.info(f"Цена для offer с ID {
                             xmlid} установлена на 100, так как его нет в Excel.")

                # Архивирование товара
                archived = offer.find('archived')
                if archived is not None:
                    archived.text = 'true'
                    logging.info(f"archived.text = true для offer с ID {
                                 xmlid} так как его нет в Excel.")
                else:
                    archived = ET.SubElement(offer, "archived")
                    archived.text = 'true'
                    logging.info(f"archived.text = true для offer с ID {
                                 xmlid} так как его нет в Excel.")

                disabled = offer.find('disabled')
                if disabled is not None:
                    disabled.text = 'true'
                    logging.info(f"disabled.text = true для offer с ID {
                                 xmlid} так как его нет в Excel.")
                else:
                    disabled = ET.SubElement(offer, "disabled")
                    disabled.text = 'true'
                    logging.info(f"disabled.text = true для offer с ID {
                        xmlid} так как его нет в Excel.")
        # Дополнительная проверка: если цена уже 100, но archived и disabled не true
        if price_element.text == "100.00":
            archived = offer.find('archived')
            disabled = offer.find('disabled')
            if (archived is None or archived.text != 'true') or (disabled is None or disabled.text != 'true'):
                logging.info(f"Архивирование и отключение offer с ID {
                             xmlid}, так как цена уже 100.")
                if archived is None:
                    archived = ET.SubElement(offer, "archived")
                archived.text = 'true'
                if disabled is None:
                    disabled = ET.SubElement(offer, "disabled")
                disabled.text = 'true'

    # Форматирование и сохранение XML с отступами
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
    parsed_str = '\n'.join(
        [line for line in parsed_str.split('\n') if line.strip()])

    with open(file_xml, "w", encoding="utf-8") as f:
        f.write(parsed_str)

    logging.info(f"Цены в файле {file_xml} успешно обновлены.")


# Загрузка цен из Excel
prices_from_excel = load_prices_from_excel('products.xlsx')

# Обновление цен в XML
update_prices_in_xml('products.xml', prices_from_excel)

logging.info("Скрипт завершен.")
