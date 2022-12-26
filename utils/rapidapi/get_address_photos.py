from typing import List, Dict

from loguru import logger

from data import config
from utils.rapidapi.requests_to_api import post_request_to_api


def get_detail_info(hotel_id: str) -> Dict:
    """
    Returns additional information for hotel
    """
    url = "https://hotels4.p.rapidapi.com/properties/v2/detail"

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "propertyId": hotel_id
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": config.RAPID_API_KEY,
        "X-RapidAPI-Host": config.RAPID_API_HOST
    }
    logger.info(f'Search for additional information for hotel {hotel_id}')
    detail_info = post_request_to_api(url=url, payload=payload, headers=headers)
    return detail_info


def get_address(hotel_id: str) -> str:
    """
    Returns hotel address
    """
    detail_info = get_detail_info(hotel_id)
    try:
        address = detail_info.get('data', {}).get('propertyInfo', {}).get('summary', {}).get('location', {}). \
            get('address', {}).get('addressLine', None)
        logger.info(f'Found the address for hotel {hotel_id}')
        return address
    except AttributeError as err:
        logger.error(err)
        logger.error('Could not find the address')
        return 'Адрес не найден'


def get_photos(data: Dict[str, str], hotel_id: str) -> List[str]:
    """Returns photo link list"""
    detail_info = get_detail_info(hotel_id)
    amount_photo = data['amount_photos']
    try:
        photos_list = detail_info.get('data', {}).get('propertyInfo', {}).get('propertyGallery', {}).get(
            'images', None)[:amount_photo]
        photos = []
        for photo_dict in photos_list:
            photo_url = parse_url_photo(photo_dict)
            photos.append(photo_url)
        logger.info(f'Found photos for hotel {hotel_id}')
        return photos
    except AttributeError as err:
        logger.error(err)
        logger.error('Could not find photos')
        return []


def parse_url_photo(photo_dict: dict) -> str:
    """
    Returns photo link
    """
    photo_url = photo_dict.get('image', {}).get('url', None)
    return photo_url
