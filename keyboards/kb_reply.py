from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_kb_geolocation() -> ReplyKeyboardMarkup:
    """
    Return button to send location
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    b = KeyboardButton(text='📍 Моё местоположение', request_location=True)
    keyboard.add(b)
    return keyboard
