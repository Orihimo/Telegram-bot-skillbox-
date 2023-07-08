import requests


def get_location_id(city: str) -> int:
    """
    Передаем название города, получаем id города
    """
    url = 'https://hotels4.p.rapidapi.com/locations/v3/search'

    querystring = {"q": city}

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "82922b474cmsh3c01ac41dbfe8f5p17d1f4jsn2b45188ed0ec",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        if data['sr']:
            return data['sr'][0]['gaiaId']
        else:
            return False
    else:
        print("Ошибка при запросе:", response.status_code)


#print(get_location_id('стамбул'))