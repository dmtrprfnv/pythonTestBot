import sqlite3
import requests
import telebot
from telebot import types
from datetime import datetime
from parser import collect_data
from aiogram.utils.markdown import hbold, hlink, hstrikethrough
from telebot.types import InlineKeyboardButton

from telegram_bot_pagination import InlineKeyboardPaginator

from auth import token
from auth import weatherAPIkey
from auth import db


def connect(db_name):
    sqlite_connection = sqlite3.connect(db_name)
    cursor = sqlite_connection.cursor()
    #print("База данных создана и успешно подключена к SQLite")
    print('SQLite Success!')
    cursor.close()
    return sqlite_connection

def disconnect(sql):
    if (sql):
        sql.close()
        print("Соединение с SQLite закрыто")

def telegram_bot(token):
    global cur
    global cursor
    global goodsList

    bot = telebot.TeleBot(token)

    cur = connect(db)
    #sqlite_query = '''SELECT * FROM user_info;'''
    sqlite_query = '''
    CREATE TABLE IF NOT EXISTS user_info(
        chatId      INTEGER PRIMARY KEY,
        firstname   TEXT NOT NULL,
        username    TEXT NOT NULL,
        lat         FLOAT,
        lon         FLOAT);'''

    cursor = cur.cursor()
    print("База данных подключена к SQLite")
    cursor.execute(sqlite_query)
    #record = cursor.fetchall()
    #print(record)
    cur.commit()
    print('success!')
    cursor.close()

    @bot.message_handler(commands=['start'])
    def start_message(message):
        #print(message)
        if message.chat.id == 660201592:
            bot.send_message(message.chat.id, f'Привет, мелочь!')
        else:
            bot.send_message(message.chat.id, f'Hello, {message.from_user.first_name}!')

    @bot.message_handler(content_types=['location'])
    def location(message):
        if message.location is not None:
            lon = message.location.longitude
            lat = message.location.latitude

            id = message.from_user.id
            firstname = message.from_user.first_name
            username = message.from_user.username

            cur = connect(db)
            cursor = cur.cursor()

            sqlite_query1 = f'SELECT chatId FROM user_info WHERE chatId = {id};'
            cursor.execute(sqlite_query1)
            record = cursor.fetchone()
            if record:
                print('Такая запись уже существует!')
            else:
                sqlite_query = f'''INSERT INTO user_info (chatId, firstname, username, lat, lon) VALUES ({id}, '{firstname}', '{username}', {lat}, {lon});'''
                cursor.execute(sqlite_query)
                cur.commit()
                cursor.close()

    @bot.message_handler(content_types=['text'])
    def send_message(message):
        if message.text.lower().strip() == 'погода' or message.text.lower().strip() == 'weather':
            try:
                cur = connect(db)
                cursor = cur.cursor()

                sqlite_query1 = f'SELECT lat, lon FROM user_info WHERE chatId = {message.chat.id};'
                cursor.execute(sqlite_query1)
                record = cursor.fetchone()
                if record:
                    req = requests.get(f'https://api.openweathermap.org/data/2.5/weather?lat={record[0]}&lon={record[1]}&lang=ru&appid={weatherAPIkey}&units=metric')
                    response = req.json()
                    town = response['name']
                    weatherDescription = response['weather'][0]['description']
                    temp = response['main']['temp']
                    feelsLike = response['main']['feels_like']
                    print(f'town: {town}\nweather: {weatherDescription}\ntemp: {temp}\nfeels_like: {feelsLike}')
                    bot.send_message(message.chat.id, f'Погода в городе {town}\nна {datetime.strftime(datetime.now(), "%d %b %Y, %H:%M:%S")}:\n{weatherDescription}\nТемпература: {temp} градусов\nОщущается как: {feelsLike} градусов')
                else:
                    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                    button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
                    keyboard.add(button_geo)
                    bot.send_message(message.chat.id, "Поделись местоположением", reply_markup=keyboard)
                cursor.close()
            except:
                bot.send_message(message.chat.id, 'Error!')

        if message.text.lower().strip() == 'поиск товара':
            bot.send_message(
                chat_id=message.chat.id,
                text='Какой товар ищем в акции?\nФормат ввода: "Товар:Название"'
            )

        if message.text.lower().strip() == 'магнит' or message.text.lower().strip() == 'акции' or message.text.lower().strip() == 'Все акции магнита':

            goodsList = collect_data()
            send_character_page(message, goodsList)

        if message.text.lower().strip() == 'что ты умеешь' or message.text.lower().strip() == 'функции':
            keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            button_weather = types.KeyboardButton(text='Погода')
            button_magnit_all = types.KeyboardButton(text='Все акции Магнита')
            button_magnit_search = types.KeyboardButton(text='Поиск товара')
            keyboard.add(button_weather, button_magnit_all, button_magnit_search)
            bot.send_message(message.chat.id, 'Вот, что я умею:', reply_markup=keyboard)

        if 'товар:' in message.text.lower().strip():
            goodsList = collect_data()
            item = message.text.lower().strip()[6:]
            itemsList = []
            print(item)

            for x in goodsList:
                if item in x['Продукт'].lower():
                    print('Найдено!', x)
                    itemsList.append(x)

            if len(itemsList):
                pack = ''
                for x in itemsList:
                    myCard = f'{hlink(x["Продукт"], x["Ссылка"])}\n' \
                             f'{hbold("Скидка: ")}{x["Скидка"][1:]}\n' \
                             f'{"Старая цена: "}{hstrikethrough(x["Старая цена"])} руб.\n' \
                             f'{hbold("Новая цена: ")}{x["Новая цена"]} руб.'
                    print(x, x['Продукт'])
                    pack += myCard + '\n' + '-' * 35 + '\n'
                pack = pack[:len(pack) - 36]

                bot.send_message(chat_id=message.chat.id, text='Вот что удалось найти:')
                send_character_page(message, itemsList)

    @bot.callback_query_handler(func=lambda call: call.data.split('#')[0] == 'character')
    def characters_page_callback(call):
        page = int(call.data.split('#')[1])
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
        send_character_page(call.message, listList, page)

    @bot.message_handler(func=lambda message: True)
    def get_character(message):
        send_character_page(message)

    def send_character_page(message, list, page=1):
        global listList
        listList= list
        spisokLen = len(listList) // 4
        if len(listList) % 4 != 0:
            spisokLen += 1
        paginator = InlineKeyboardPaginator(
            spisokLen,
            current_page=page,
            data_pattern='character#{page}'
        )
        pack = ''
        for x in listList[(page - 1) * 4:page * 4]:
            myCard = f'{hlink(x["Продукт"], x["Ссылка"])}\n' \
                     f'{hbold("Скидка: ")}{x["Скидка"][1:]}\n' \
                     f'{"Старая цена: "}{hstrikethrough(x["Старая цена"])} руб.\n' \
                     f'{hbold("Новая цена: ")}{x["Новая цена"]} руб.'
            print(x, x['Продукт'])
            pack += myCard + '\n' + '-' * 35 + '\n'
        pack = pack[:len(pack)-36]

        paginator.add_after(InlineKeyboardButton('Найти товар', callback_data='search'))

        bot.send_message(chat_id=message.chat.id, text=pack, reply_markup=paginator.markup, parse_mode='html')

        # paginator.add_before(
        #     InlineKeyboardButton('Like', callback_data='like#{}'.format(page)),
        #     InlineKeyboardButton('Dislike', callback_data='dislike#{}'.format(page))
        # )

    @bot.callback_query_handler(func=lambda call: call.data.split('#')[0] == 'search')
    def product_search(call):
        bot.send_message(chat_id=call.message.chat.id, text='Какой товар ищем в акции?\nФормат ввода: "Товар:Название"')

    bot.polling()


if __name__ == '__main__':
    telegram_bot(token)
    disconnect(cur)


