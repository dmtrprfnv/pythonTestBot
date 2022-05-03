import datetime
import requests
import csv
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


def collect_data(city_code='1505'):
    cur_time = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M')
    goods = []
    temp = {}
    ua = UserAgent()
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': ua.random
    }

    cookies = {
        'mg_geo_id': f'{city_code}'
    }

    responce = requests.get(url='https://magnit.ru/promo/', headers=headers, cookies=cookies)

    soup = BeautifulSoup(responce.text, 'lxml')
    city = soup.find('a', class_='header__contacts-link_city').text.strip()
    cards = soup.find_all('a', class_='card-sale_catalogue')

    # filename = f'{city}_{cur_time}.csv'
    # with open(filename, 'w') as file:
    #     writer = csv.writer(file)
    #
    #     writer.writerow(
    #         (
    #             'Продукт',
    #             'Старая цена',
    #             'Новая цена',
    #             'Процент скидки',
    #             'Время акции',
    #             'Ссылка'
    #         )
    #     )

    for card in cards:


        try:
            card_title = card.find('div', class_='card-sale__title').text.strip()
        except AttributeError:
            continue
        if card_title == 'Скидка для пенсионеров':
            break

        try:
            card_discount = card.find('div', class_='card-sale__discount').text.strip()
        except AttributeError:
            continue

        card_price_old_integer = card.find('div', class_='label__price_old').find('span', class_='label__price-integer').text.strip()
        card_price_old_decimal = card.find('div', class_='label__price_old').find('span', class_='label__price-decimal').text.strip()
        card_old_price = f'{card_price_old_integer}.{card_price_old_decimal}'

        try:
            card_price_integer = card.find('div', class_='label__price_new').find('span', class_='label__price-integer').text.strip()
            card_price_decimal = card.find('div', class_='label__price_new').find('span', class_='label__price-decimal').text.strip()
            card_price = f'{card_price_integer}.{card_price_decimal}'
        except AttributeError:
            continue

        card_sale_date = card.find('div', class_='card-sale__date').text.strip().replace('\n', ' ')

        # print('https://magnit.ru' + card.get('href'))
        # print(card_title)
        # print(card_discount)
        # print('Выгода:', float(card_old_price) - float(card_price))
        # print(card_price)
        # print(card_sale_date)

        # with open(filename, 'a') as file:
        #     writer = csv.writer(file)
        #
        #     writer.writerow(
        #         (
        #             card_title,
        #             card_old_price,
        #             card_price,
        #             card_discount,
        #             card_sale_date,
        #             'https://magnit.ru' + card.get('href')
        #         )
        #     )
        link = 'https://magnit.ru' + card.get('href')
        temp = {
            'Продукт' : card_title,
            'Старая цена' : card_old_price,
            'Новая цена' : card_price,
            'Скидка': card_discount,
            'Действие акции': card_sale_date,
            'Ссылка': link
        }
        goods.append(temp)
    #print(f'Файл {city}_{cur_time}.csv записан!')
    #path = '/Users/dmtrprfnv/PycharmProjects/pythonTestBot/' + filename
    # print(path)

    #return path, goods
    return goods
