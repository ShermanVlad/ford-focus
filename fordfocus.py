import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
import os
from time import sleep
import csv


headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}


def retry_request(url, headers, timeout=30, max_retries=3):
    for _ in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Ошибка: {e}. Повтор соединения...")
            sleep(5)
    raise Exception(f"Не получилось после {max_retries} попыток.")


data_name = []
def card_links(url):
    response = retry_request(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    print("===page card===", url)
    # sleep(0.5)


    if soup.find("div", class_="right catGroupsItems").find("a", class_="catalogueGroup subgrp"):
        for el in soup.find("div", class_="right catGroupsItems").find_all("a", class_="catalogueGroup subgrp"):
            links = 'https://fordfocus.com.ua/' + el["href"]
            card_links(links)
            # print(links)
    else:
        for el in soup.find("div", class_="catalogueGroupItems").find_all("div", class_="catalogueGroupItem"):
            # link = 'https://fordfocus.com.ua/' + el.find('a')["href"]

            if el.find('span', class_="cgquantity").find('span', class_="quantity_true"):
                available = el.find('span', class_="cgquantity").find('span', class_="quantity_true").text.strip()
            else:
                continue
            # print(available)

            code = el.find('span', class_="cgproperty").find('div', class_="property_value").text.strip()
            if code == '':
                continue

            if len(el.find('span', class_="cgproperty").find_all('span', class_="property_value")) == 2:
                brand = el.find('span', class_="cgproperty").find_all('span', class_="property_value")[1].text.strip()
                new_or_not = el.find('span', class_="cgproperty").find_all('span', class_="property_value")[0].text.strip()
                if new_or_not == 'Б/У':
                    new_or_not = 1
                else:
                    new_or_not = ''
            
            name = el.find('span', class_="cgname").text.strip()
            # print(name)

            price = el.find('span', class_="cgprice")
            if not price.find('span', class_="old_price"):
                final_price = round(float(price.text.strip().replace(' грн.', '')) - (float(price.text.strip().replace(' грн.', '')) * 0.02), 2)
            else:
                price.find('span', class_="old_price").decompose()
                if float(price.text.strip().replace(' грн.', '')) == 0:
                    return
                final_price = round(float(price.text.strip().replace(' грн.', '')) - (float(price.text.strip().replace(' грн.', '')) * 0.02), 2)
            # print(name, '>>>', final_price)

            data_name.append([brand, code, name, final_price, available, new_or_not])
    
        if soup.find("link", rel="next"):
            next_pages = soup.find("link", rel="next")["href"]
            card_links(next_pages)


# card_links(('https://fordfocus.com.ua/optika-zerkala-775'))


def group_links(url):
    response = retry_request(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    # print("<<<page col>>>", url)

    for el in soup.find("div", class_="under_h1").find_all("a", class_="catalogueGroup"):
        links = 'https://fordfocus.com.ua' + el["href"]
        if '/rozprodaj' in links:
            continue
        card_links(links)
        # print(links)


group_links("https://fordfocus.com.ua/")


column_name = [["Бренд", "Код", "Название", "Цена", "Наличие", "Б/У"]]
with open(os.path.dirname(__file__) + '/fordfocus.csv', 'w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
    writer.writerows(column_name + data_name)