import xml.etree.ElementTree as ET
import pandas as pd

# Этот скрипт предназначен для извлечения данных из XML-файла и создания на их основе Excel-файла.
# Он парсит XML-файл, извлекает информацию о товарах, таких как ID, цена и описание,
# и записывает эти данные в Excel-файл. Архивированные товары пропускаются.


def create_excel_from_xml(xml_file, excel_file):
    # Парсинг XML файла
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Список для хранения данных
    data = []

    # Проход по всем предложениям (offer) в XML
    for offer in root.find('shop').find('offers').findall('offer'):
        # Проверка, является ли товар архивированным
        archived = offer.find('archived')
        if archived is not None and archived.text == 'true':
            continue  # Пропуск архивированных товаров

        # Извлечение ID товара
        xmlid = offer.get('id')
        # Извлечение цены товара, если она указана
        price = offer.find('price').text if offer.find(
            'price') is not None else ''
        # Извлечение описания товара, если оно указано
        description = offer.find('name').text if offer.find(
            'name') is not None else ''

        # Добавление данных о товаре в список
        data.append({
            'xmlid': xmlid,
            'description': description,
            'price': price
        })

    # Создание DataFrame из собранных данных и запись в Excel
    df = pd.DataFrame(data)
    df.to_excel(excel_file, index=False)


# Использование функции для создания Excel-файла из XML
create_excel_from_xml('products.xml', 'products.xlsx')
