import math
import uuid
from datetime import datetime
from typing import List

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from loader import db
from utils.rapidapi.get_cities import City


def get_kb_inline_area(areas_list: List[City]) -> InlineKeyboardMarkup:
    """
    Returns inline keyboard with area list
    """
    keyboard = InlineKeyboardMarkup()
    for area in areas_list:
        area_id = area.city_id
        name_area = area.name
        uid = str(uuid.uuid1())
        db.add_callback(callback_code=uid, area_name=name_area)
        button = InlineKeyboardButton(text=f'{name_area}', callback_data=f'area_{area_id}_{uid}')
        keyboard.add(button)
    return keyboard


def get_kb_inline_numbers(row_num: int, col_num: int) -> InlineKeyboardMarkup:
    """
    Returns inline keyboard where the number of rows is row_num and the number of columns is col_num.
    """
    keyboard = InlineKeyboardMarkup()
    for i in range(row_num):
        row = []
        for j in range(col_num):
            row.append(InlineKeyboardButton(text=f'{(j + 1) + i * col_num}⃣',
                                            callback_data=f'number_{(j + 1) + i * col_num}'))
        keyboard.row(*row)
    return keyboard


def get_answer_YorN() -> InlineKeyboardMarkup:
    """
    Returns inline keyboard with numbers answers Yes or No
    """
    keyboard = InlineKeyboardMarkup()
    b1 = InlineKeyboardButton(text='Да', callback_data='has_Yes')
    b2 = InlineKeyboardButton(text='Нет', callback_data='has_No')
    keyboard.row(b1, b2)
    return keyboard


def get_kb_inline_delete() -> InlineKeyboardMarkup:
    """
    Returns inline keyboard for remove answer bot
    """
    keyboard = InlineKeyboardMarkup()
    b1 = InlineKeyboardButton('❎ Удалить это сообщение', callback_data='delete')
    keyboard.row(b1)
    return keyboard


def get_kb_inline_delete_stop() -> InlineKeyboardMarkup:
    """
    Returns the inline keyboard to delete the bot response or stop the search
    """
    keyboard = InlineKeyboardMarkup()
    b1 = InlineKeyboardButton('❎ Удалить это сообщение', callback_data='delete')
    b2 = InlineKeyboardButton('❌ Закончить поиск', callback_data='stop')
    keyboard.add(b1).add(b2)
    return keyboard


def get_kb_inline_start() -> InlineKeyboardMarkup:
    """
    Returns the inline keyboard to start the search
    """
    keyboard = InlineKeyboardMarkup()
    b1 = InlineKeyboardButton('🚀 СТАРТ', callback_data='search')
    keyboard.add(b1)
    return keyboard


async def calculated_index(state: FSMContext, page_shift: int, amount_items_per_page: int, length_list: int) -> \
        tuple[int, int, int, int]:
    """
    Returns number of the current page, indexes for obtaining a slice from the list and the number of elements
    on one page for pagination of the list.
    """
    async with state.proxy() as data:
        current_page = data.get('page')
        new_page = current_page + page_shift
        if new_page < 0:
            data['page'] = 0
            index = 0
        elif new_page * amount_items_per_page == length_list:
            data['page'] = int(length_list / amount_items_per_page) - 1
            index = (new_page - 1) * amount_items_per_page
        elif new_page * amount_items_per_page > length_list:
            data['page'] = int(length_list / amount_items_per_page)
            index = (new_page - 1) * amount_items_per_page
        else:
            data['page'] = new_page
            index = new_page * amount_items_per_page
        current_page = data.get('page')
    return current_page, index, index + amount_items_per_page, amount_items_per_page


async def get_kb_inline_hotels_list(state: FSMContext, page_shift: int) -> InlineKeyboardMarkup:
    """
    Formation of an inline keyboard when paginating a hotel list
    """
    async with state.proxy() as data:
        hotels_list = data.get('hotels_list')
    keyboard = InlineKeyboardMarkup()
    current_page, start_index, finish_index, amount_hotels_per_page = await calculated_index(
        length_list=len(hotels_list),
        state=state,
        page_shift=page_shift,
        amount_items_per_page=3)

    for hotel in hotels_list[start_index:finish_index]:
        button = InlineKeyboardButton(text=f'{hotel[1]}, {round(hotel[2])} $ за ночь',
                                      callback_data=f'hotel_{hotel[0]}')
        keyboard.add(button)
    nex = InlineKeyboardButton(text='Вперёд', callback_data='next')
    pages = InlineKeyboardButton(text=f'{current_page + 1}/{math.ceil(len(hotels_list) / amount_hotels_per_page)}',
                                 callback_data=' ')
    back = InlineKeyboardButton(text='Назад', callback_data='back')
    stop = InlineKeyboardButton(text='Закончить просмотр запросов', callback_data='stop')
    keyboard.row(back, pages, nex).add(stop)
    return keyboard


async def get_kb_inline_requests_list(message: types.Message, state: FSMContext, page_shift: int, user_id: int) -> None:
    """
    Formation of an inline keyboard when paginating a user request list
    """
    requests = db.get_requests(user_id=user_id)
    keyboard = InlineKeyboardMarkup()
    current_page, start_index, finish_index, amount_requests_per_page = await calculated_index(
        length_list=len(requests),
        state=state,
        page_shift=page_shift,
        amount_items_per_page=5)
    for request in requests[start_index:finish_index]:
        command = None
        if request[3] == 'самые дешёвые':
            command = 'Поиск дешёвых отелей'
        elif request[3] == 'по цене и расположению от центра':
            command = 'По цене и расположению от центра'
        elif request[3] == 'в моём городе с учётом цены и расположения от центра':
            command = 'В моём городе'
        date = datetime.fromisoformat(request[2])
        button = InlineKeyboardButton(text=f'{command} {date.strftime("%d.%m.%y %H:%M")}',
                                      callback_data=f'request_{request[0]}')
        keyboard.add(button)
    nex = InlineKeyboardButton(text='Вперёд', callback_data='next_step')
    pages = InlineKeyboardButton(text=f'{current_page + 1}/{math.ceil(len(requests) / amount_requests_per_page)}',
                                 callback_data=' ')
    back = InlineKeyboardButton(text='Назад', callback_data='back_step')
    stop = InlineKeyboardButton(text='Закончить просмотр запросов', callback_data='finish')
    keyboard.row(back, pages, nex).add(stop)
    await message.answer('История запросов:', reply_markup=keyboard)


def get_kb_inline_back_hotels_list() -> InlineKeyboardMarkup:
    """
    Returns the inline keyboard to navigate back to the list of found hotels
    """
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton('К списку отелей', callback_data='to_hotels')
    keyboard.add(button)
    return keyboard


def history_action(request_id: str) -> InlineKeyboardMarkup:
    """
    Returns the inline keyboard to remove the request or navigate back to the list of requests
    """
    keyboard = InlineKeyboardMarkup()
    b1 = InlineKeyboardButton(text='Удалить этот запрос', callback_data=f'delreq_{request_id}')
    b2 = InlineKeyboardButton(text='Вернуться к списку запросов', callback_data='to_requests')
    keyboard.row(b1, b2)
    return keyboard
