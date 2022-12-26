from typing import Dict, NamedTuple, List, Optional, Any

from loguru import logger

from data import config
from utils.rapidapi.get_address_photos import get_address, get_photos
from utils.rapidapi.requests_to_api import post_request_to_api


class Hotel(NamedTuple):
    hotel_id: str
    name: str
    price: float
    address: str
    photos: Optional[Any]
    center: float


def get_hotels_info(data: Dict[str, Any]) -> Dict:
    """
    Returns information about hotels
    """
    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    check_in_date = str(data['check_in']).split('-')
    check_out_date = str(data['check_out']).split('-')
    check_in_year, check_in_month, check_in_day = map(int, check_in_date)
    check_out_year, check_out_month, check_out_day = map(int, check_out_date)
    sort_order = ''
    destination = {}
    filters = {}
    page_size = None
    if data['command'] == 'самые дешёвые':
        region_id = data['area_id']
        sort_order = 'PRICE_LOW_TO_HIGH'
        page_size = data['amount_hotels']
        destination = {"regionId": region_id}

    elif data['command'] == 'по цене и расположению от центра':
        region_id = data['area_id']
        sort_order = 'DISTANCE'
        filters = {'price': {'max': data['price_max'], 'min': data['price_min']}}
        page_size = 200
        destination = {"regionId": region_id}

    elif data['command'] == 'в моём городе с учётом цены и расположения от центра':
        latitude = data['lat']
        longitude = data['lon']
        sort_order = 'DISTANCE'
        filters = {'price': {'max': data['price_max'], 'min': data['price_min']}}
        page_size = 200
        destination = {"coordinates": {"latitude": latitude, "longitude": longitude}}

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "destination": destination,
        "checkInDate": {
            "day": check_in_day,
            "month": check_in_month,
            "year": check_in_year
        },
        "checkOutDate": {
            "day": check_out_day,
            "month": check_out_month,
            "year": check_out_year
        },
        "rooms": [
            {
                "adults": 1,
                "children": []
            }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": page_size,
        "sort": sort_order,
        "filters": filters
    }

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": config.RAPID_API_KEY,
        "X-RapidAPI-Host": config.RAPID_API_HOST
    }
    logger.info('Search hotels')
    hotels_data = post_request_to_api(url=url, payload=payload, headers=headers)
    return hotels_data


def get_hotels_list(data: Dict[str, Any]) -> List[Hotel]:
    """
    Returns prepared list of hotels
    """
    hotels_result_api = get_hotels_info(data)
    logger.info('Processing the resulting list of hotels')
    if hotels_result_api is None or hotels_result_api.get('data') is None:
        return []
    else:
        start_hotels_list = hotels_result_api.get('data', {}).get('propertySearch', {}).get('properties', None)
        if data['command'] == 'самые дешёвые':
            result_hotels = []
            for hotel in start_hotels_list:
                result_hotels.append(
                    Hotel(
                        hotel_id=parse_hotel_id(hotel),
                        name=parse_hotel_name(hotel),
                        address=get_address(hotel_id=parse_hotel_id(hotel)),
                        center=parse_hotel_center(hotel),
                        price=parse_hotel_price(hotel),
                        photos=get_hotel_photos(data, hotel)
                    )
                )
            return result_hotels
        elif data['command'] == 'по цене и расположению от центра' or \
                data['command'] == 'в моём городе с учётом цены и расположения от центра':
            center_min = round(data['center_min'] * 0.62)
            center_max = round(data['center_max'] * 0.62)
            amount_hotels = data['amount_hotels']

            result_hotels = []
            for hotel in start_hotels_list:
                center = parse_hotel_center(hotel)
                if center_min <= center <= center_max:
                    result_hotels.append(
                        Hotel(
                            hotel_id=parse_hotel_id(hotel),
                            name=parse_hotel_name(hotel),
                            address=get_address(hotel_id=parse_hotel_id(hotel)),
                            center=parse_hotel_center(hotel),
                            price=parse_hotel_price(hotel),
                            photos=get_hotel_photos(data, hotel)
                        )
                    )
                if len(result_hotels) == amount_hotels:
                    break
            return result_hotels


def parse_hotel_id(hotel_dict: dict) -> str:
    """
    Returns hotel id
    """
    return hotel_dict.get('id', None)


def parse_hotel_name(hotel_dict: dict) -> str:
    """
    Returns hotel name
    """
    return hotel_dict.get('name', None)


def parse_hotel_center(hotel_dict: dict) -> float:
    """
    Return distance to city center (miles)
    """
    return hotel_dict.get('destinationInfo', {}).get('distanceFromDestination', {}).get('value', 0)


def parse_hotel_price(hotel_dict: dict) -> float:
    """
    Returns hotel price per night ($)
    """
    return hotel_dict.get('price', {}).get('lead', {}).get('amount', 0)


def get_hotel_photos(data: Dict[str, str], hotel_dict: dict) -> Optional[Any]:
    """
    If the user wanted to get a photo of the hotel returns links to the photo, otherwise returns None.
    """
    hotel_id = parse_hotel_id(hotel_dict)
    if data['has_photo'] == 'Yes':
        photo_list = get_photos(data, hotel_id)
        if photo_list:
            return ', '.join(photo_list)
        else:
            return None
    else:
        return None
