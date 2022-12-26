from typing import Dict, NamedTuple, List

from loguru import logger

from data import config
from utils.rapidapi.requests_to_api import get_request_to_api


class City(NamedTuple):
    city_id: str
    name: str
    latitude: str
    longitude: str


def get_city_info(city: str) -> Dict:
    """
    Returns information about cities
    """
    url = "https://hotels4.p.rapidapi.com/locations/v3/search"
    querystring = {"q": city, "locale": "ru_RU", "langid": "1033", "siteid": "300000001"}
    headers = {
        "X-RapidAPI-Key": config.RAPID_API_KEY,
        "X-RapidAPI-Host": config.RAPID_API_HOST
    }
    logger.info(f'Search {city}')
    city_data = get_request_to_api(url=url, headers=headers, querystring=querystring)
    return city_data


def get_areas(city: str) -> List[City]:
    """
    Returns prepared list of areas
    """
    city_data = get_city_info(city)
    areas_list = get_area_list(city_data)
    logger.info('Processing the resulting list of areas')
    areas = []
    for area in areas_list:
        areas.append(
            City(
                city_id=parse_area_id(area),
                name=parse_name_area(area),
                latitude=parse_latitude_area(area),
                longitude=parse_longitude_area(area)
            )
        )
    return areas


def get_area_list(city_data: dict) -> List[Dict]:
    """
    Returns list of areas whose type is neither hotel nor airport
    """
    areas = []
    try:
        logger.info('Search for areas in the city')
        places = city_data['sr']
        for place in places:
            if place['type'] != 'HOTEL' and place['type'] != 'AIRPORT':
                areas.append(place)
        return areas
    except TypeError as err:
        logger.error(err)
        return areas


def parse_area_id(area: Dict) -> str:
    """
    Returns area id
    """
    return area.get('gaiaId', None)


def parse_name_area(area: Dict) -> str:
    """
    Returns area name
    """
    return area.get('regionNames', {}).get('shortName', None)


def parse_latitude_area(area: Dict) -> str:
    """
    Returns area latitude
    """
    return area.get('coordinates', {}).get('lat', 0)


def parse_longitude_area(area: Dict) -> str:
    """
    Returns area longitude
    """
    return area.get('coordinates', {}).get('long', 0)
