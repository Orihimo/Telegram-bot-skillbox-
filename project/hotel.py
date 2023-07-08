import requests


def get_hotel_info(id_hotel: str, photo_count: int) -> list:
    """
    Функция, которая собирает данные о конкретном отеле, на вход получает id отеля, и количество фото для показа
    если в данные передается 0(кол-во фото), функция не ломается и возвращает все данные в виде списка
    """



    url = "https://hotels4.p.rapidapi.com/properties/v2/detail"

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "propertyId": id_hotel,
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "82922b474cmsh3c01ac41dbfe8f5p17d1f4jsn2b45188ed0ec",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()

        hotel_info = []

        hotel_info_dict = {}
        hotel_info_dict['id'] = data['data']['propertyInfo']['summary']['id']  # id отеля для проверки
        hotel_info_dict['address'] = data['data']['propertyInfo']['summary']['location']['address'][
            'addressLine']  # адрес отеля
        photos_list = []

        if photo_count > 0:
            photos = data['data']['propertyInfo']['propertyGallery']['images'][:photo_count]  # перебираем все url ссылки с фото отеля
            for photo in photos:
                photos_list.append(photo['image']['url'])
                hotel_info_dict['photos'] = photos_list
        hotel_info.append(hotel_info_dict)

        return hotel_info

        # print(json.dumps(data['data']['propertyInfo']['summary']['name'], ensure_ascii=False, indent=4)) #название отеля

    else:
        print("Ошибка при запросе:", response.status_code)


#print(get_hotel_info('1699', 4))