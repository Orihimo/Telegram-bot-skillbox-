
import re
from datetime import datetime

def get_user_input() -> dict:
    """
    Функция запрашивает у клиента название города, кол-во вариантов отелей, показывать ли фото, даты заезда и выезда.
    Все данные возвращаются в виде словаря + количество дней
    """

    while True:
        city = input('Введите название города: ')

        if re.match(r"^[А-ЯЁа-яё]+$", city):
            break
        else:
            print('Название города не должно содержать цифр и должно быть на Русском языке!')



    while True:
        try:
            city_count = int(input('Введите количество показываемых вариантов отелей, максимум 10 штук:  '))
            if 10 >= city_count > 0:
                break
            elif city_count > 10:
                print('Количество отелей должно быть не больше 10')
            else:
                print('Количество отелей должно быть больше 0')
        except ValueError:
            print('Количество отелей должно быть целым числом')



    while True:
        photo_check = input('Показывать фото? Да/Нет: ')
        if photo_check.strip().lower() == 'да':
            try:
                photo_count = int(input("Сколько фотографий отеля показать, максимум 9 шт.:  "))
                if 10 > photo_count > 0:
                    break
                elif photo_count > 9:
                    print('Количество фото не может быть больше 9 шт.')
                else:
                    print('Количество фото отелей должно быть больше 0')
            except ValueError:
                print('Количество отелей должно быть целым числом')
        elif photo_check.strip().lower() == 'нет':
            photo_count = 0
            break
        else:
            print('Неизвестная команда, повторите запрос')



    checkInDate = {'day': None, 'month': None, 'year': None}
    checkOutDate = {'day': None, 'month': None, 'year': None}

    while True:
        checkin_date = input("Введите дату заезда в формате ДД.ММ.ГГГГ: ")
        checkout_date = input("Введите дату отъезда в формате ДД.ММ.ГГГГ: ")

        try:
            checkin_datetime = datetime.strptime(checkin_date, '%d.%m.%Y')
            checkout_datetime = datetime.strptime(checkout_date, '%d.%m.%Y')

            if checkout_datetime < checkin_datetime:
                print('Дата заезда не может быть раньше даты уезда!')
                continue

            checkInDate['day'] = checkin_datetime.day
            checkInDate['month'] = checkin_datetime.month
            checkInDate['year'] = checkin_datetime.year

            checkOutDate['day'] = checkout_datetime.day
            checkOutDate['month'] = checkout_datetime.month
            checkOutDate['year'] = checkout_datetime.year

            days = (checkout_datetime.date() - checkin_datetime.date()).days

            break

        except ValueError:
            print('Ошибка, некорректный формат даты')

    return {'city': city, 'city_count': int(city_count), 'photo_count': int(photo_count), 'checkInDate': checkInDate,
            'checkOutDate': checkOutDate, 'days': days}













