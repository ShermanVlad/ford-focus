import requests
import csv

# URL для запиту
url = "https://api.bm.parts/prices/list"

# Заголовки
headers = {
    "Authorization": "9d00d0d2-0c95-419c-ab1f-3ba6582661b8.tvpzYLTKHs4PF44DfpOyLpyki3Q",
    "Content-Type": "application/json"
}

# Тіло запиту
data = {
    "currency": "A358000C2947F7AE11E23F5617780B16",  # Валюта - гривня
    "warehouses": ["92F5005056BA7D7A11EF8A2FD6A72E28", "816D000C2999A7E611E6EC6B4A1915AF", "ACF9000C2947F7AE11E28A2B02C4AD32", "816F000C2999A7E611E6FF21C30463AF"],
    "format": "csv"
}

# Запит на сервер
response = requests.post(url, headers=headers, json=data)

# Перевірка відповіді та збереження CSV
input_file = "price_list.csv"
if response.status_code == 200:
    with open(input_file, "wb") as file:
        file.write(response.content)
    print("Файл з прайсом збережено як price_list.csv")
else:
    print("Помилка:", response.status_code)
    print(response.json())
    exit()

# Шлях до вихідного файлу
output_file = "all_price_list.csv"

# Функція для перевірки та заміни значення "кількість"
def clean_quantity(value):
    try:
        quantity = int(value)
        return max(quantity, 1)  # Якщо значення <=0, замінити на 1
    except ValueError:
        return 1  # Заміна некоректних значень на 1

# Обробка файлу
with open(input_file, mode="r", encoding="utf-8") as infile, open(output_file, mode="w", encoding="utf-8", newline="") as outfile:
    reader = csv.DictReader(infile)
    writer = csv.writer(outfile)

    # Запис заголовків
    writer.writerow(["Производитель", "Код", "Описание", "Цена", "Кількість", "БУ"])

    # Обробка рядків
    for row in reader:
        try:
            manufacturer = row["Бренд"]
            code = row["Артикул"]
            description = row["Назва"]
            price = round(float(row["Ціна ГРН"]) * 1.15, 2)

            # Пріоритет кількості: спробуємо взяти значення для складу у Львові, інакше використовуємо інший склад
            quantity = clean_quantity(row.get("Львів Зелена ДАГ") or row.get("Львів ДАГ") or row.get("Київ Борщагівка ДАГ") or row.get("Луцьк ДАГ", "1"))
            used = ""  # Порожнє значення для колонки "БУ"

            # Запис у вихідний файл
            writer.writerow([manufacturer, code, description, price, quantity, used])

        except ValueError:
            # Пропускаємо рядок, якщо значення ціни не є числом
            print(f"Пропущено рядок через помилку в конвертації: {row}")

print(f"Файл збережено як {output_file}")
