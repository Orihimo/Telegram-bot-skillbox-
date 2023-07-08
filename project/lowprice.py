from lowprice_question import HotelSearch
from location import get_location_id
from list_lowprice import get_list_hotels
from hotel import get_hotel_info

def lowprice():
        user_input = HotelSearch().get_user_input() #Получаем словарь с данными клиента(город, кол-во показов, кол-во фото, дата заезда/ дата выезда, кол-во дней)

        location_id = get_location_id(user_input['city']) #Получаем id города

        if location_id is not False:

            #Получаем id отеля, название отеля, расстояние до центра, стоимость за ночь

            list_hotels = get_list_hotels(id_city=str(location_id), city_count=user_input['city_count'], check_in_date=user_input['checkInDate'], check_out_date=user_input['checkOutDate'])


            print()
            print('Смотрим информацию по отелям в городе:', user_input['city'].title())
            print()

            #В цикле перебираем все отели из ранее полученного списка list_hotels. В каждой итерации вызываем функцию из модуля hotel
            #На выходе получаем все нужные нам данные

            for hotel in list_hotels:
                hotels_info = get_hotel_info(hotel['id'], user_input['photo_count'])

                print(f'Название отеля: {hotel["name"]}')
                print(f'Адрес отеля: {hotels_info[0]["address"]}')
                print(f'Растояние до центра: {hotel["distance"]} км.')
                print(f'Стоимость за ночь: {round(hotel["price_per_day"], 2)} $')
                print(f'Стоимость за {user_input["days"]} дня(ей): {round(hotel["price_per_day"] * user_input["days"])} $')

                if 'photos' in hotels_info[0]:
                    print(f'Фото отеля: {hotels_info[0]["photos"]}')

                print('_' * 80)
        else:
            print('Такого города нет')

print(lowprice())
