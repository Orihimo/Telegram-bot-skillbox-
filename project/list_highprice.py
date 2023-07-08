import requests


def get_list_hotels_highprice(id_city: str, check_in_date: dict, check_out_date: dict, ) -> list:
    """
    Функция получает список отелей, а так же данные id, название, расстояние до центра и стоимость за ночь
    на вход функция получает id города, кол-во показов отелей, даты заезда/ выезда
    """

    url = "https://hotels4.p.rapidapi.com/properties/v2/list"

    payload = {'currency': 'USD',
               'eapid': 1,
               'locale': 'ru_RU',
               'siteId': 300000001,
               'destination': {
                   'regionId': id_city  # id Города
               },
               'checkInDate': check_in_date, # Дата заезда
               'checkOutDate': check_out_date, # Дата выезда
               'rooms': [{'adults': 1}],
               'resultsStartingIndex': 0,
               'resultsSize': 200,
               'sort': 'PRICE_LOW_TO_HIGH',
               "filters": {"price": {
                   "max": 10000,
                   "min": 100
               }}
               }

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "82922b474cmsh3c01ac41dbfe8f5p17d1f4jsn2b45188ed0ec",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()

        hotels = []

        for hotel in data['data']['propertySearch']['properties']:
            hotel_dict = {}
            hotel_dict['id'] = hotel['id']
            hotel_dict['name'] = hotel['name']
            hotel_dict['distance'] = hotel['destinationInfo']['distanceFromDestination']['value']
            hotel_dict['price_per_day'] = hotel['price']['lead']['amount']
            hotels.append(hotel_dict)

        return hotels

    else:
        print("Ошибка при запросе:", response.status_code)


#print(get_list_hotels_highprice(id_city = '1639', check_in_date = {'day': 23, 'month': 6, 'year': 2023}, check_out_date = {'day': 28, 'month': 6, 'year': 2023}))