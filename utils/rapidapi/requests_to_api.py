import json
from typing import Dict, Any

import requests
from loguru import logger


def get_request_to_api(url: str, headers: Dict[str, str], querystring: Dict[str, str]) -> Dict:
    """
    Makes a GET request to the API. Returns data
    """
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        logger.info(response)
        if response.status_code != 200:
            raise LookupError(f'Status code {response.status_code}')
        if not response:
            return {}
        data = json.loads(response.text)
        if not data:
            raise LookupError('Response is empty')
        return data
    except (requests.exceptions.RequestException, LookupError) as err:
        logger.error(err)


def post_request_to_api(url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict:
    """
    Makes a POST request to the API. Returns data
    """
    try:
        response = requests.request("POST", url, json=payload, headers=headers)
        logger.info(response)
        if response.status_code != 200:
            raise LookupError(f'Status code {response.status_code}')
        if not response:
            return {}
        data = json.loads(response.text)
        if not data:
            raise LookupError('Response is empty')
        return data

    except (requests.exceptions.RequestException, LookupError) as err:
        logger.error(err)
