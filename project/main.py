import json

import telebot
from telebot import types
from telebot.types import InputMediaPhoto
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.types import Message
from telebot.storage import StateMemoryStorage

from datetime import datetime
from location import get_location_id
from list_lowprice import get_list_hotels_lowprice
from list_highprice import get_list_hotels_highprice
from list_bestdeal import get_list_hotels_bestdeal
from hotel import get_hotel_info

from peewee import *
import loguru
import time

# Now, you can pass storage to bot.
state_storage = StateMemoryStorage()

bot = telebot.TeleBot('6254243703:AAEeo_03r_UI76iSDqsOZPnGweefMmZ1Lq8', state_storage=state_storage)

db = SqliteDatabase('history.db')


# States group.
class MyStates(StatesGroup):
    city = State()  # creating instances of State class is enough from now
    city_count = State()
    photo = State()
    date_in = State()
    date_out = State()
    min_price = State()
    max_price = State()
    min_dist = State()
    max_dist = State()


class History(Model):
    user_id = IntegerField()
    username = CharField()
    command = CharField()
    city = CharField()
    city_count = IntegerField()
    photo = IntegerField()
    date_in = CharField()
    date_out = CharField()
    min_price = IntegerField(default=0)
    max_price = IntegerField(default=0)
    min_dist = IntegerField(default=0)
    max_dist = IntegerField(default=0)
    hotels = TextField()
    timestamp = DateTimeField(default=datetime.now)

    class Meta:
        database = db


db.create_tables([History])
loguru.logger.add("errors.log", level="CRITICAL")


@bot.message_handler(state="*", commands=['cancel'])
def any_state(message: Message):
    """
    Cancel state
    """
    bot.send_message(message.chat.id, "Your state was cancelled.")
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(commands=['start'])
def start_command(message):
    keyboard = types.InlineKeyboardMarkup()
    help_button = types.InlineKeyboardButton("❓ Помощь", callback_data='help')
    lowprice_button = types.InlineKeyboardButton("💰 Самые дешевые отели", callback_data='lowprice')
    highprice_button = types.InlineKeyboardButton("💸 Самые дорогие отели", callback_data='highprice')
    bestdeal_button = types.InlineKeyboardButton("🌟 Лучшие отели по заданным характеристикам", callback_data='bestdeal')
    history_button = types.InlineKeyboardButton("📚 История запросов", callback_data='history')
    keyboard.add(help_button, lowprice_button, highprice_button, bestdeal_button, history_button)

    bot.send_message(message.chat.id, "Привет, чем могу помочь?", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def button_callback(call):
    if call.data == 'help':
        help_command(call.message)
    elif call.data == 'lowprice':
        lowprice(call.message)
    elif call.data == "highprice":
        highprice(call.message)
    elif call.data == "bestdeal":
        bestdeal(call.message)
    elif call.data == 'history':
        history(call.message)


@bot.message_handler(commands=['history'])
def history(message: Message):
    """
    При запуске команды history, мы показываем историю поисковых запросов с результатами и временем
    """
    try:
        bot.send_message(message.chat.id, "Показываю историю запросов")

        found_history = False

        for hist in History.select().order_by(History.id.desc()):
            if hist.user_id == message.chat.id:
                found_history = True

                formatted_timestamp = hist.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                mess = (
                    f'Имя пользователя: {hist.username}\n'
                    f'Название города: {hist.city}\n'
                    f'Кол-во отелей для показа: {hist.city_count}\n'
                    f'Кол-во фото для показа {hist.photo}\n'
                    f'Дата заезда: {hist.date_in}\n'
                    f'Дата отъезда: {hist.date_out}\n'
                    f'Время создания запроса: {formatted_timestamp}\n'
                )

                hotels_data = json.loads(hist.hotels)

                bot.send_message(message.chat.id, mess)

                for hotel in hotels_data:
                    hotel_mess = (
                        f'Название отеля: {hotel["name"]}\n'
                        f'Адрес отеля: {hotel["address"]}\n'
                        f'Растояние до центра: {hotel["distance"]}\n'
                        f'Цена за ночь: {hotel["price_per_day"]}\n'
                        f'Цена за весь срок пребывания: {hotel["total_price"]}\n'
                    )

                    if 'photos' in hotel and hotel['photos']:
                        media_group = []
                        for num, photo_url in enumerate(hotel['photos']):
                            media_group.append(InputMediaPhoto(media=photo_url, caption=hotel_mess if num == 0 else None))
                        bot.send_media_group(chat_id=message.chat.id, media=media_group)
                    else:
                        bot.send_message(message.chat.id, hotel_mess)
                    time.sleep(1)

        if not found_history:
            bot.send_message(message.chat.id, "У вас еще не было истории запросов")

        bot.send_message(message.chat.id, "Команда history завершена")
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции history: {str(e)}')

@bot.message_handler(commands=['help'])
def help_command(message: Message):
    """
    При запуске команды help. Показываем доступные команды для пользователя
    """
    try:
        help_message = "Вот список доступных команд:\n\n" \
                       "/help - Показать список команд\n" \
                       "/lowprice - Показать список самых дешевых отелей\n" \
                       "/highprice - Показать список самых дорогих отелей\n" \
                       "/bestdeal - Показать список отелей по заданым критериям\n" \
                       "/history - История запросов"

        bot.send_message(message.chat.id, help_message)
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции help: {str(e)}')

@bot.message_handler(commands=['lowprice'])
def lowprice(message: Message):
    """
    При запуске команды lowprice, мы присваеваем состоянию статус city, а так же запрашиваем название города
    с которым работаем в следующей функции
    """
    try:
        bot.set_state(message.chat.id, MyStates.city, message.chat.id)
        bot.send_message(message.chat.id, 'Введите название города')
        with bot.retrieve_data(message.chat.id, message.chat.id) as data:
            data['command'] = 'lowprice'
            data['username'] = message.chat.first_name
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции lowprice: {str(e)}')


@bot.message_handler(commands=['highprice'])
def highprice(message: Message):
    """
    При запуске команды highprice, мы присваеваем состоянию статус city, а так же запрашиваем название города
    с которым работаем в следующей функции
    """
    try:
        bot.set_state(message.chat.id, MyStates.city, message.chat.id)
        bot.send_message(message.chat.id, 'Введите название города')
        with bot.retrieve_data(message.chat.id, message.chat.id) as data:
            data['command'] = 'highprice'
            data['username'] = message.chat.first_name
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции highprice: {str(e)}')

@bot.message_handler(commands=['bestdeal'])
def bestdeal(message: Message):
    """
    При запуске команды bestdeal, мы присваеваем состоянию статус city, а так же запрашиваем название города
    с которым работаем в следующей функции
    """
    try:
        bot.set_state(message.chat.id, MyStates.city, message.chat.id)
        bot.send_message(message.chat.id, 'Введите название города')
        with bot.retrieve_data(message.chat.id, message.chat.id) as data:
            data['command'] = 'bestdeal'
            data['username'] = message.chat.first_name
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции bestdeal: {str(e)}')


@bot.message_handler(state=MyStates.city)
def get_city(message: Message):
    """
    Функцию перехватчик, перехватывает сообщение название города
    и добавляет его в словарь data
    """
    try:
        city_name = message.text
        bot.send_message(message.chat.id, f'Вы ввели город: {city_name}')

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['city'] = city_name

        bot.set_state(message.from_user.id, MyStates.city_count, message.chat.id)
        bot.send_message(message.chat.id, 'Введите количество показываемых отелей')
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_city: {str(e)}')


@bot.message_handler(state=MyStates.city_count, is_digit=True)
def get_city_count(message: Message):
    """
    В функции перехватываем количество отелей для показа
    и добавляет его в словарь data
    """
    try:
        city_count = message.text
        bot.send_message(message.chat.id, f'Вы ввели количество: {city_count}')

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['city_count'] = city_count

        bot.set_state(message.from_user.id, MyStates.photo, message.chat.id)
        bot.send_message(message.chat.id, 'Нужны ли вам фотографии?\n Введите число от 0 до 6 (0 - ненужны)')
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_city_count: {str(e)}')


@bot.message_handler(state=MyStates.photo, is_digit=True)
def get_photo_count(message: Message):
    """
    Функция перехватывает кол-во фото
    и добавляет их в словарь data
    """
    try:
        photo = message.text
        bot.send_message(message.chat.id, f'Вы ввели количество фото: {photo}')

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['photo'] = photo

        bot.set_state(message.from_user.id, MyStates.date_in, message.chat.id)
        bot.send_message(message.chat.id, 'Укажите дату въезда в формате ДД.ММ.ГГГГ:')
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_photo_count: {str(e)}')


@bot.message_handler(state=MyStates.date_in)
def get_date_in(message: Message):
    """
    Функция перехватывает дату въезда, обрабатывает ее
    и делает две записи в словарь. Для расчета разницы дней и для поиска отелей по дате
    """
    try:
        date_in = message.text
        bot.send_message(message.chat.id, f'Вы ввели дату въезда: {date_in}')

        checkInDate = {'day': None, 'month': None, 'year': None}
        checkin_datetime = datetime.strptime(date_in, '%d.%m.%Y')
        checkInDate['day'] = checkin_datetime.day
        checkInDate['month'] = checkin_datetime.month
        checkInDate['year'] = checkin_datetime.year

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['date_in'] = checkInDate
            data['start'] = checkin_datetime

        bot.set_state(message.from_user.id, MyStates.date_out, message.chat.id)
        bot.send_message(message.chat.id, 'Укажите дату выезда в формате ДД.ММ.ГГГГ:')
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_date_in: {str(e)}')


@bot.message_handler(state=MyStates.date_out)
def get_date_out(message: Message):
    """
    Функция перехватывает дату выезда
    и делает три записи в словарь. Для расчета разницы дней и для поиска отелей по дате, и кол-во дней пребывания
    """
    try:
        date_out = message.text
        bot.send_message(message.chat.id, f'Вы ввели дату въезда: {date_out}')

        checkOutDate = {'day': None, 'month': None, 'year': None}
        checkout_datetime = datetime.strptime(date_out, '%d.%m.%Y')
        checkOutDate['day'] = checkout_datetime.day
        checkOutDate['month'] = checkout_datetime.month
        checkOutDate['year'] = checkout_datetime.year

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['date_out'] = checkOutDate
            data['finish'] = checkout_datetime
            data['days'] = (data['finish'].date() - data['start'].date()).days

            command = data['command']

        msg = f'Город - {data.get("city")}\n' \
              f'Количество отелей - {data.get("city_count")}\n' \
              f'Количество фото - {data.get("photo")}\n' \
              f'Дата заезда - {data.get("date_in").get("day")}.{data.get("date_in").get("month")}.{data.get("date_in").get("year")}\n' \
              f'Дата выезда - {data.get("date_out").get("day")}.{data.get("date_out").get("month")}.{data.get("date_out").get("year")}'

        if command == 'lowprice':
            bot.send_message(message.chat.id, f'Идёт поиск:\n{msg}')
            get_result_lowprice(message)

        elif command == 'highprice':
            bot.send_message(message.chat.id, f'Идёт поиск:\n{msg}')
            get_result_highprice(message)

        elif command == 'bestdeal':
            bot.set_state(message.from_user.id, MyStates.min_price, message.chat.id)
            bot.send_message(message.chat.id, 'Введите минимальную цену в $:')
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_date_out: {str(e)}')


@bot.message_handler(state=MyStates.min_price, is_digit=True)
def get_min_price(message: Message):
    try:
        min_price = message.text
        bot.send_message(message.chat.id, f'Вы ввели минимальную цену: {min_price}')

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['min_price'] = min_price

        bot.set_state(message.from_user.id, MyStates.max_price, message.chat.id)
        bot.send_message(message.chat.id, 'Введите максимальную цену в $:')
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_min_price: {str(e)}')


@bot.message_handler(state=MyStates.max_price, is_digit=True)
def get_max_price(message: Message):
    try:
        max_price = message.text
        bot.send_message(message.chat.id, f'Вы ввели максимальную цену: {max_price}')

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['max_price'] = max_price

        bot.set_state(message.from_user.id, MyStates.min_dist, message.chat.id)
        bot.send_message(message.chat.id, 'Введите минимальное расстояние до центра в км.:')
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_max_price: {str(e)}')


@bot.message_handler(state=MyStates.min_dist, is_digit=True)
def get_min_dist(message: Message):
    try:
        min_dist = message.text
        bot.send_message(message.chat.id, f'Вы ввели минимальное расстояние до центра в км.: {min_dist}')

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['min_dist'] = min_dist

        bot.set_state(message.from_user.id, MyStates.max_dist, message.chat.id)
        bot.send_message(message.chat.id, 'Введите максимальное расстояние до центра в км.:')
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_min_dist: {str(e)}')

@bot.message_handler(state=MyStates.max_dist, is_digit=True)
def get_max_dist(message: Message):
    try:
        max_dist = message.text
        bot.send_message(message.chat.id, f'Вы ввели максимальное расстояние до центра в км.: {max_dist}')

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['max_dist'] = max_dist

            msg = f'Город - {data.get("city")}\n' \
                  f'Количество отелей - {data.get("city_count")}\n' \
                  f'Количество фото - {data.get("photo")}\n' \
                  f'Дата заезда - {data.get("date_in").get("day")}.{data.get("date_in").get("month")}.{data.get("date_in").get("year")}\n' \
                  f'Дата выезда - {data.get("date_out").get("day")}.{data.get("date_out").get("month")}.{data.get("date_out").get("year")}'

        bot.send_message(message.chat.id, f'Идёт поиск:\n{msg}')
        get_result_bestdeal(message)
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_max_dist: {str(e)}')


def get_result_bestdeal(message: Message):
    """
    Вызывается функция поиска отелей с лучшей ценой и расстоянием до центра
    Используем модули location - для поиска id отеля
    list_bestdeal - для поиска списка отелей (имя, расстояния, цена)
    hotel - для поиска фото, адреса
    """
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            location_id = get_location_id(city=data['city'])
            list_hotels = get_list_hotels_bestdeal(id_city=str(location_id), city_count=int(data['city_count']),
                                                   min_price=int(data['min_price']), max_price=int(data['max_price']),
                                                   min_dist=int(data['min_dist']), max_dist=int(data['max_dist']),
                                                   check_in_date=data['date_in'], check_out_date=data['date_out'])

        bot.send_message(message.chat.id, 'Отели найдены')

        hotels_data = []
        for hotel in list_hotels:
            hotels_info = get_hotel_info(str(hotel['id']), int(data['photo']))

            text_message = f'Название отеля: {hotel["name"]}\n' \
                           f'Адрес отеля: {hotels_info[0]["address"]}\n' \
                           f'Расстояние до центра: {hotel["distance"]}\n' \
                           f'Цена за ночь: {round(hotel["price_per_day"], 2)} $\n' \
                           f'Цена за: {data["days"]} дня(ей): {round(hotel["price_per_day"] * data["days"])} $'

            photos = []
            if 'photos' in hotels_info[0]:
                for photo_url in hotels_info[0]["photos"]:
                    photos.append(photo_url)

            hotel_data = {
                'name': hotel['name'],
                'address': hotels_info[0]['address'],
                'distance': hotel['distance'],
                'price_per_day': round(hotel['price_per_day'], 2),
                'total_price': round(hotel['price_per_day'] * data['days']),
                'photos': photos
            }
            hotels_data.append(hotel_data)

            if 'photos' in hotels_info[0]:
                media_group = []
                for num, photo_url in enumerate(hotels_info[0]["photos"]):
                    media_group.append(InputMediaPhoto(media=photo_url, caption=text_message if num == 0 else None))
                bot.send_media_group(chat_id=message.chat.id, media=media_group)
            else:
                bot.send_message(chat_id=message.chat.id, text=text_message)

        bot.send_message(chat_id=message.chat.id, text='Поиск завершён')
        bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)

        hotels_json = json.dumps(hotels_data)
        history = History.create(
            user_id=message.from_user.id,
            username=data['username'],
            command='get_result_bestdeal',
            city=data['city'],
            city_count=int(data['city_count']),
            photo=int(data['photo']),
            date_in=data['date_in'],
            date_out=data['date_out'],
            min_price=int(data['min_price']),
            max_price=int(data['max_price']),
            min_dist=int(data['min_dist']),
            max_dist=int(data['max_dist']),
            hotels=hotels_json
        )
        history.save()
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_result_bestdeal: {str(e)}')


def get_result_lowprice(message: Message):
    """
    Вызывается функция поиска отелей с минимальной ценой.
    Используем модули location - для поиска id отеля
    list - для поиска списка отелей (имя, расстояния, цена)
    hotel - для поиска фото, адреса
    """
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            location_id = get_location_id(city=data['city'])
            list_hotels = get_list_hotels_lowprice(id_city=str(location_id), city_count=int(data['city_count']),
                                                   check_in_date=data['date_in'], check_out_date=data['date_out'])

        bot.send_message(message.chat.id, 'Отели найдены')
        hotels_data = []
        for hotel in list_hotels:
            hotels_info = get_hotel_info(str(hotel['id']), int(data['photo']))

            text_message = f'Название отеля: {hotel["name"]}\n' \
                           f'Адрес отеля: {hotels_info[0]["address"]}\n' \
                           f'Расстояние до центра: {hotel["distance"]}\n' \
                           f'Цена за ночь: {round(hotel["price_per_day"], 2)} $\n' \
                           f'Цена за: {data["days"]} дня(ей): {round(hotel["price_per_day"] * data["days"])} $'

            photos = []
            if 'photos' in hotels_info[0]:
                for photo_url in hotels_info[0]["photos"]:
                    photos.append(photo_url)

            hotel_data = {
                'name': hotel['name'],
                'address': hotels_info[0]['address'],
                'distance': hotel['distance'],
                'price_per_day': round(hotel['price_per_day'], 2),
                'total_price': round(hotel['price_per_day'] * data['days']),
                'photos': photos
            }
            hotels_data.append(hotel_data)

            if 'photos' in hotels_info[0]:
                media_group = []
                for num, photo_url in enumerate(hotels_info[0]["photos"]):
                    media_group.append(InputMediaPhoto(media=photo_url, caption=text_message if num == 0 else None))
                bot.send_media_group(chat_id=message.chat.id, media=media_group)
            else:
                bot.send_message(chat_id=message.chat.id, text=text_message)

        bot.send_message(chat_id=message.chat.id, text='Поиск завершён')
        bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)

        hotels_json = json.dumps(hotels_data)
        history = History.create(
            user_id=message.from_user.id,
            username=data['username'],
            command='get_result_bestdeal',
            city=data['city'],
            city_count=int(data['city_count']),
            photo=int(data['photo']),
            date_in=data['date_in'],
            date_out=data['date_out'],
            hotels=hotels_json
        )
        history.save()
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_result_lowprice: {str(e)}')


def get_result_highprice(message: Message):
    """
    Вызывается функция поиска отелей с максимальной ценой.
    Используем модули location - для поиска id отеля
    list_highprice - для поиска списка отелей (имя, расстояния, цена)
    hotel - для поиска фото, адреса
    """
    try:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            location_id = get_location_id(city=data['city'])
            list_hotels = get_list_hotels_highprice(id_city=str(location_id), check_in_date=data['date_in'],
                                                    check_out_date=data['date_out'])
            city_count = int(data['city_count'])

        bot.send_message(message.chat.id, 'Отели найдены')

        hotels_data = []
        for hotel in list_hotels[::-1][:city_count]:
            hotels_info = get_hotel_info(str(hotel['id']), int(data['photo']))

            text_message = f'Название отеля: {hotel["name"]}\n' \
                           f'Адрес отеля: {hotels_info[0]["address"]}\n' \
                           f'Расстояние до центра: {hotel["distance"]} км.\n' \
                           f'Цена за ночь: {round(hotel["price_per_day"], 2)} $\n' \
                           f'Цена за: {data["days"]} дня(ей): {round(hotel["price_per_day"] * data["days"])} $'

            photos = []
            if 'photos' in hotels_info[0]:
                for photo_url in hotels_info[0]["photos"]:
                    photos.append(photo_url)

            hotel_data = {
                'name': hotel['name'],
                'address': hotels_info[0]['address'],
                'distance': hotel['distance'],
                'price_per_day': round(hotel['price_per_day'], 2),
                'total_price': round(hotel['price_per_day'] * data['days']),
                'photos': photos
            }
            hotels_data.append(hotel_data)

            if 'photos' in hotels_info[0]:
                media_group = []
                for num, photo_url in enumerate(hotels_info[0]["photos"]):
                    media_group.append(InputMediaPhoto(media=photo_url, caption=text_message if num == 0 else None))
                bot.send_media_group(chat_id=message.chat.id, media=media_group)
            else:
                bot.send_message(chat_id=message.chat.id, text=text_message)

        bot.send_message(chat_id=message.chat.id, text='Поиск завершён')
        bot.delete_state(user_id=message.from_user.id, chat_id=message.chat.id)

        hotels_json = json.dumps(hotels_data)
        history = History.create(
            user_id=message.from_user.id,
            username=data['username'],
            command='get_result_bestdeal',
            city=data['city'],
            city_count=int(data['city_count']),
            photo=int(data['photo']),
            date_in=data['date_in'],
            date_out=data['date_out'],
            hotels=hotels_json
        )
        history.save()
    except Exception as e:
        loguru.logger.critical(f'Критическая ошибка в функции get_result_highprice: {str(e)}')


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())
bot.infinity_polling(skip_pending=True)
