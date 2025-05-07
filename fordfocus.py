import requests
from bs4 import BeautifulSoup
import os
from time import sleep
import csv
from urllib.parse import urljoin

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

def retry_request(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Помилка ({attempt+1}/{max_retries}): {e}")
            sleep(5)
    return None

def parse_item(item):
    try:
        # Назва товару
        name_tag = item.find('span', class_='cgname')
        name = name_tag.text.strip() if name_tag else 'Невідома назва'

        # Ціна
        price_element = item.find('span', class_='cgprice')
        price_text = price_element.text.replace('грн', '').replace('.', '').replace(',', '.').strip() if price_element else '0'
        try:
            price = float(price_text)
        except:
            price = 0.0

        # Наявність
        quantity_true = item.find('span', class_='quantity_true')
        quantity_false = item.find('span', class_='quantity_false')
        if quantity_true:
            availability = quantity_true.text.strip()
        elif quantity_false:
            availability = quantity_false.text.strip()
        else:
            availability = 'Невідомо'

        # Бренд, стан, артикул
        brand, status, code = "Невідомий бренд", "Невідомий стан", "Артикул не вказаний"

        # Отримаємо всі елементи властивостей (і <span>, і <div>)
        props = item.select('.cgproperty .property_value')

        for prop in props:
            value = prop.text.strip().lower()
            # Логіка визначення стану
            if 'нова' in value or 'new' in value:
                status = "Нова"
            elif 'б/в' in value or 'бу' in value or 'вживана' in value:
                status = "Б/В"
            # Логіка визначення бренду
            elif value.isalpha() and brand == "Невідомий бренд":
                brand = value.upper()
            # Логіка визначення коду (якщо це щось схоже на артикул)
            elif code == "Артикул не вказаний" and len(value) < 20:
                code = prop.text.strip()

        item_data = {
            'brand': brand,
            'code': code,
            'name': name,
            'price': round(price * 0.98, 2),  # 2% знижка
            'availability': availability,
            'used': status
        }

        print(f"Товар: {item_data}")  # Для дебагу
        return item_data

    except Exception as e:
        print(f"Помилка парсингу товару: {e}")
        return None

def parse_products_page(url):
    data = []
    page = 1

    while True:
        current_url = f"{url}?page={page}" if page > 1 else url
        print(f"  Обробляємо сторінку товарів: {current_url}")

        response = retry_request(current_url)
        if not response:
            print(f"Не вдалося отримати сторінку товарів {current_url}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        # Парсимо товари на сторінці
        items = soup.find_all('div', class_='catalogueGroupItem')
        if not items:
            print("  Товари не знайдені")
            break

        for item in items:
            item_data = parse_item(item)
            if item_data:
                data.append(item_data)

        # Пошук пагінації
        pagination = soup.find("div", class_="pagination")
        if pagination:
            next_button = None
            links = pagination.find_all("a")
            for link in links:
                if link.text.strip() == '>':
                    next_button = link
                    break

            if next_button:
                page += 1
                sleep(1)
                continue  # є наступна сторінка — переходимо далі
            else:
                break  # немає кнопки ">" — кінець пагінації
        else:
            break  # пагінація відсутня повністю

    return data

def parse_subcategories(base_url):
    data = []

    response = retry_request(base_url)
    if not response:
        print(f"Не вдалося отримати сторінку категорії {base_url}")
        return data

    soup = BeautifulSoup(response.text, 'html.parser')

    # Спочатку перевіряємо, чи є підкатегорії
    subcategories = soup.select('div.catalogueGroupList a.catalogueGroup.subgrp')
    if subcategories:
        print(f"Знайдено {len(subcategories)} підкатегорій")
        for subcat in subcategories:
            subcat_url = urljoin(base_url, subcat['href'])
            print(f"Обробляємо підкатегорію: {subcat_url}")
            data.extend(parse_subcategories(subcat_url))  # Рекурсивний виклик
            sleep(1)
    else:
        # Якщо підкатегорій немає - парсимо товари
        print("Підкатегорій не знайдено, переходимо до товарів")
        data.extend(parse_products_page(base_url))

    return data

def parse_model(url):
    print(f"\nПочинаємо обробку моделі: {url}")
    return parse_subcategories(url)

def main():
    base_url = "https://fordfocus.com.ua/"
    output_file = os.path.join(os.path.dirname(__file__), 'fordfocus.csv')

    print("Починаємо парсинг сайту ford-focus.com.ua")

    try:
        # Отримуємо головну сторінку для пошуку категорій
        response = retry_request(base_url)
        if not response:
            raise Exception("Не вдалося отримати головну сторінку")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Знаходимо всі моделі авто
        models = soup.select('div.under_h1 a.catalogue_group_main')
        if not models:
            raise Exception("Не знайдено жодної моделі авто")

        model_urls = [urljoin(base_url, model['href']) for model in models
                      if 'rozprodaj' not in model['href'].lower() and '#' not in model['href']]

        print(f"Знайдено {len(model_urls)} моделей для обробки")

        all_data = []
        for url in model_urls:
            model_data = parse_model(url)
            all_data.extend(model_data)
            print(f"Додано {len(model_data)} товарів з цієї моделі")
            sleep(2)  # Пауза між моделями

        # Записуємо результати у CSV
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Бренд', 'Код', 'Назва', 'Ціна', 'Кількість'])
            for item in all_data:
                if item['availability'].strip().lower() == 'є у наявності':
                    writer.writerow([
                        item['brand'],
                        item['code'],
                        item['name'],
                        item['price'],
                        1
                ])

        print(f"\nПарсинг завершено. Збережено {len(all_data)} товарів у файл {output_file}")

    except Exception as e:
        print(f"Критична помилка: {e}")

if __name__ == "__main__":
    main()
