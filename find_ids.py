import xml.etree.ElementTree as ET
import pandas as pd
import logging

# Этот скрипт предназначен для работы с XML и Excel файлами.
# Он выполняет следующие задачи:
# 1. Извлекает идентификаторы предложений (offer id) из XML-файла.
# 2. Сравнивает эти идентификаторы с идентификаторами из Excel-файла.
# 3. Удаляет из Excel-файла строки, идентификаторы которых отсутствуют в XML-файле.
# 4. Логирует все действия и изменения, выполняемые скриптом.

# Этот скрипт - костыль нужен для того чтобы насильно запустить работу скрипта, ведь при удалении строк из файла products.xlsx
# при  следующей итерации запуска основного скрипта он будет переименован в products_old.xlsx и результатом будет разница
# в файлах products.xlsx и products_old.xlsx, что в свою очередь запустит процесс генерации новых карточек(товаров) <offer>

# Настройка логирования
logging.basicConfig(filename='my.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

# Функция для извлечения offer id из XML-файла


def get_offer_ids(xml_file):
    logging.info("Загрузка offer id из XML файла")
    print("Загрузка offer id из XML файла...")

    # Загрузка данных из XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    offers = root.find('shop').find('offers')

    # Извлечение offer id
    offer_ids = {offer.find('offer_id').text for offer in offers if offer.find(
        'offer_id') is not None}

    return offer_ids

# Функция для удаления отсутствующих xmlid из Excel-файла


def remove_missing_xmlids(excel_file, offer_ids):
    logging.info("Начало удаления отсутствующих xmlid из Excel файла")
    print("Начало удаления отсутствующих xmlid из Excel файла...")

    # Загрузка данных из Excel
    excel_data = pd.read_excel(excel_file)

    # Проверка наличия столбца 'xmlid'
    if 'xmlid' not in excel_data.columns:
        logging.error("Столбец 'xmlid' не найден в Excel-файле.")
        print("Ошибка: столбец 'xmlid' не найден в Excel-файле.")
        return

    # Получение xmlid из Excel
    xml_ids = set(excel_data['xmlid'].tolist())

    # Находим xmlid, которые есть в Excel, но отсутствуют в offer_ids
    missing_ids = xml_ids - offer_ids
    missing_ids = list(missing_ids)[:10]

    # Выводим отсутствующие xmlid в консоль и логируем их
    if missing_ids:
        logging.info(
            f"Отсутствующие xmlid в products.xml offer id: {missing_ids}")
        print("Отсутствующие xmlid в products.xml offer id:", missing_ids)

        # Логируем и удаляем только первые 10 строк с отсутствующими xmlid
        deleted_count = 0
        rows_to_keep = []  # Будем хранить индексы строк, которые оставим

        for index, row in excel_data.iterrows():
            xmlid = row['xmlid']
            if xmlid in missing_ids:
                if deleted_count < 10:
                    logging.info(f"Удаление строки: {row.to_dict()}")
                    print(f"Удаление строки: {row.to_dict()}")
                    deleted_count += 1
                else:
                    rows_to_keep.append(index)
            else:
                rows_to_keep.append(index)

        # Сохраняем только выбранные строки
        excel_data = excel_data.loc[rows_to_keep]
        # Сохраняем изменения в Excel
        excel_data.to_excel(excel_file, index=False)
        print("Изменения сохранены в Excel файл.")
    else:
        logging.info("Нет отсутствующих xmlid в products.xml offer id.")
        print("Нет отсутствующих xmlid в products.xml offer id.")


if __name__ == "__main__":
    xml_file = 'products.xml'
    excel_file = 'products.xlsx'

    # Извлечение offer id из XML-файла
    # Удаляем только первые 10 айдишников которых нет в XML файле
    # (чтобы не перенапрягать за раз скрипт и проверить работает ли логика создания новых карточек товаров)
    offer_ids = get_offer_ids(xml_file)
    logging.info(f"Список 10 первых offer id из products.xml: {
                 list(offer_ids)[:10]}, Всего таких ID: {len(offer_ids)}")
    print("Список 10 первых offer id из products.xml:", list(
        offer_ids)[:10], "Всего таких ID:", len(offer_ids))

    # Удаление отсутствующих xmlid из Excel-файла
    remove_missing_xmlids(excel_file, offer_ids)
