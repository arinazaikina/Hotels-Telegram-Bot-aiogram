from aiogram.dispatcher.filters.state import StatesGroup, State


class SearchHotels(StatesGroup):
    command = State()
    geolocation = State()
    city = State()
    area = State()
    amount_hotels = State()
    has_photo = State()
    amount_photos = State()
    date_check_in = State()
    date_check_out = State()
    price_min = State()
    price_max = State()
    center_min = State()
    center_max = State()
    search = State()
    page = State()


class History(StatesGroup):
    step = State()
