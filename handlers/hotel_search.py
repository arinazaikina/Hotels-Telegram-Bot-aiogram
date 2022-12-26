import asyncio
import datetime
import sqlite3
from contextlib import suppress

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import MediaGroup
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound
from aiogram_calendar_rus import simple_cal_callback, SimpleCalendar
from loguru import logger

from keyboards import kb_inline
from keyboards.kb_inline import get_kb_inline_hotels_list, get_kb_inline_back_hotels_list
from keyboards.kb_reply import get_kb_geolocation
from loader import db, bot
from states.states import SearchHotels, History
from utils.rapidapi.get_cities import get_areas
from utils.rapidapi.get_hotels import get_hotels_list


async def reset_state(message: types.Message) -> None:
    """
    Reply to the user when he writes instead of using the inline keyboard
    """
    await message.answer('😭 Зачем пишешь? Надо кнопку тыкать! Посмотри сообщение выше и, пожалуйста, ткни кнопку 🔘',
                         reply_markup=kb_inline.get_kb_inline_delete_stop())
    await message.delete()


async def delete_message(message: types.Message, sleep_time: int = 0) -> None:
    """
    Remove bot messages
    """
    await asyncio.sleep(sleep_time)
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await message.delete()


async def process_callback_delete(callback_query: types.CallbackQuery) -> None:
    """
    Remove bot messages
    """
    await bot.answer_callback_query(callback_query.id, text='Сообщение удалено')
    msg = callback_query.message
    asyncio.create_task(delete_message(msg, 1))


async def stop(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Cancel hotel search, close state machine when a callback is 'stop'.
    """
    await callback.message.answer('Вы отменили поиск отелей 🙅\nМожет всё же что-нибудь поищем?'
                                  '\n\n/lowprice\n\n/bestdeal\n\n/mycity',
                                  reply_markup=kb_inline.get_kb_inline_delete())
    logger.info('Cancel hotel search')
    await state.finish()


async def geolocation_start(message: types.Message, state: FSMContext) -> None:
    """
    The answer to the user when a command is 'mycity'.
    Setting a state 'geolocation'.
    """
    await SearchHotels.command.set()
    async with state.proxy() as data:
        logger.info('Start mycity command')
        data['command'] = 'в моём городе с учётом цены и расположения от центра'
    try:
        db.add_user(id_user=message.from_user.id, name=message.from_user.first_name,
                    connection_date=datetime.datetime.now())
    except sqlite3.IntegrityError as err:
        logger.info(err)
    await message.answer('Отправьте свою геолокацию', reply_markup=get_kb_geolocation())
    await SearchHotels.geolocation.set()


async def enter_geolocation(message: types.Message, state: FSMContext) -> None:
    """
    The answer to the user when a state is 'geolocation'.
    Setting a state 'amount_hotels'.
    """
    lat = message.location.latitude
    lon = message.location.longitude
    async with state.proxy() as data:
        data['lat'] = lat
        data['lon'] = lon
    logger.info(f'Location coordinates: latitude {lat}, longitude {lon}')
    await message.answer('Какое количество отелей найти?',
                         reply_markup=kb_inline.get_kb_inline_numbers(row_num=3, col_num=3))
    await SearchHotels.amount_hotels.set()


async def finish_geolocation(message: types.Message, state: FSMContext) -> None:
    """
    Cancel hotel search, close state machine when location coordinates not received.
    """
    await state.finish()
    await message.answer('К сожалению, не смог получить ваши координаты 😔.\nМожно попробовать другой вид поиска:'
                         '\n\n/lowprice\n\n/bestdeal')


async def city_start(message: types.Message, state: FSMContext) -> None:
    """
    The answer to the user when a command is 'lowprice' or 'bestdeal'.
    Setting a state 'city'.
    """
    await SearchHotels.command.set()
    async with state.proxy() as data:
        if message.text == '/lowprice':
            logger.info('Start lowprice command')
            data['command'] = 'самые дешёвые'
        elif message.text == '/bestdeal':
            logger.info('Start bestdeal command')
            data['command'] = 'по цене и расположению от центра'
    try:
        db.add_user(id_user=message.from_user.id, name=message.from_user.first_name,
                    connection_date=datetime.datetime.now())
    except sqlite3.IntegrityError as err:
        logger.info(err)
    await message.answer('Введите название города', reply_markup=kb_inline.get_kb_inline_delete_stop())
    await SearchHotels.city.set()


async def enter_city_name(message: types.Message, state: FSMContext) -> None:
    """
    The answer to the user when a message sent from state 'city'
    Setting a state 'area'
    """
    await message.answer('Сверяюсь с картой. Пожалуйста, подождите...', reply_markup=kb_inline.get_kb_inline_delete())
    async with state.proxy() as data:
        data['city'] = message.text.strip()
    city = data.get('city')
    areas_list = get_areas(city)
    if areas_list:
        await message.answer('Пожалуйста, уточните место: ', reply_markup=kb_inline.get_kb_inline_area(areas_list))
        await message.delete()
        await SearchHotels.area.set()
    else:
        logger.info('Failed to find the city')
        await message.answer('Не могу получить информацию по этому городу. Давайте попробуем ещё раз /lowprice')
        await message.delete()
        logger.info('Cancel hotel search')
        await state.finish()


async def enter_area_name(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    The answer to the user when a state is 'city' and callback is 'area_'
    Setting a state 'amount_hotels'.
    """
    area_id = callback.data.split('_')[1]
    callback_code = callback.data.split('_')[2]
    area_name = db.get_callback(callback_code=callback_code)[0]
    async with state.proxy() as data:
        data['area_id'] = area_id
        data['area_name'] = area_name
    await callback.message.delete()
    await callback.message.answer('Какое количество отелей найти?',
                                  reply_markup=kb_inline.get_kb_inline_numbers(row_num=3, col_num=3))
    await SearchHotels.amount_hotels.set()


async def enter_amount_hotels(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    The answer to the user when a state is 'amount_hotels' and callback is 'number_'
    Setting a state 'has_photo'.
    """
    amount = int(callback.data.split('_')[1])
    async with state.proxy() as data:
        data['amount_hotels'] = int(amount)
    await callback.message.delete()
    await callback.message.answer('Желаете загрузить фото отелей?', reply_markup=kb_inline.get_answer_YorN())
    await SearchHotels.has_photo.set()


async def enter_has_photos(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    The answer to the user when a state is 'has_photo' and callback is 'has_'
    Setting a state 'amount_photos'.
    """
    answer = callback.data.split('_')[1]
    async with state.proxy() as data:
        data['has_photo'] = answer
    if data['has_photo'] == 'Yes':
        await callback.message.delete()
        await callback.message.answer('Какое количество фотографий загрузить?',
                                      reply_markup=kb_inline.get_kb_inline_numbers(row_num=3, col_num=3))
        await SearchHotels.amount_photos.set()
    elif data['has_photo'] == 'No':
        async with state.proxy() as data:
            data['amount_photos'] = 0
        await callback.message.delete()
        await callback.message.answer('Выберите дату заезда', reply_markup=await SimpleCalendar().start_calendar())
        await SearchHotels.date_check_in.set()


async def enter_amount_photos(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    The answer to the user when a state is 'amount_photos' and callback is 'number_'
    Setting a state 'check_in'.
    """
    amount_photos = int(callback.data.split('_')[1])
    async with state.proxy() as data:
        data['amount_photos'] = amount_photos
    await callback.message.delete()
    await callback.message.answer('Выберите дату заезда', reply_markup=await SimpleCalendar().start_calendar())
    await SearchHotels.date_check_in.set()


async def enter_date_check_in(callback: types.CallbackQuery, callback_data, state: FSMContext) -> None:
    """
    The answer to the user when a state is 'check_in'
    Setting a state 'check_out'.
    """
    selected, date = await SimpleCalendar().process_selection(callback, callback_data)
    if selected:
        if date.date() < datetime.date.today():
            await callback.message.answer('⛔ Нельзя выбрать дату из прошлого! Введите корректную дату',
                                          reply_markup=await SimpleCalendar().start_calendar())
            await callback.message.delete()
        else:
            async with state.proxy() as data:
                data['check_in'] = date.date()
            await callback.message.delete()
            await callback.message.answer('Выберите дату отъезда', reply_markup=await SimpleCalendar().start_calendar())
            await SearchHotels.date_check_out.set()


async def enter_date_check_out(callback: types.CallbackQuery, callback_data, state: FSMContext) -> None:
    """
    The answer to the user when a state is 'check_out'
    Setting a state 'price_min' or state 'search'.
    """
    selected, date = await SimpleCalendar().process_selection(callback, callback_data)
    if selected:
        async with state.proxy() as data:
            date_check_in = data.get('check_in')
            command = data.get('command')
        if date.date() <= date_check_in:
            await callback.message.answer('⛔ Дата отъезда не может быть раньше даты приезда! Введите корректную дату',
                                          reply_markup=await SimpleCalendar().start_calendar())
            await callback.message.delete()
        if command == 'по цене и расположению от центра' or \
                command == 'в моём городе с учётом цены и расположения от центра':
            async with state.proxy() as data:
                data['check_out'] = date.date()
            await callback.message.answer('Введите минимальную цену в $', reply_markup=kb_inline.get_kb_inline_delete())
            await SearchHotels.price_min.set()
        else:
            async with state.proxy() as data:
                data['check_out'] = date.date()
                data['time_request'] = datetime.datetime.now()
            await callback.message.delete()
            await callback.message.answer('Нажмите СТАРТ, чтобы начать поиск',
                                          reply_markup=kb_inline.get_kb_inline_start())
            await SearchHotels.search.set()


async def enter_price_min(message: types.Message, state: FSMContext) -> None:
    """
    The answer to the user when a message sent from state 'price_min'
    Setting a state 'price_max'.
    """
    price_min = message.text.strip()
    if price_min.isdigit():
        if int(price_min) == 0:
            price_min = '1'
        async with state.proxy() as data:
            data['price_min'] = int(price_min)
        await message.delete()
        await message.answer('Введите максимальную цену в $', reply_markup=kb_inline.get_kb_inline_delete())
        await SearchHotels.price_max.set()
    else:
        await message.answer('⛔ Цена - это целое положительное число. Введите корректную минимальную цену!',
                             reply_markup=kb_inline.get_kb_inline_delete())
        await SearchHotels.price_min.set()


async def enter_price_max(message: types.Message, state: FSMContext) -> None:
    """
    The answer to the user when a message sent from state 'price_max'
    Setting a state 'center_min'.
    """
    price_max = message.text.strip()
    async with state.proxy() as data:
        price_min = data.get('price_min')
    if not price_max.isdigit() or price_min > int(price_max):
        await message.answer('⛔ Максимальная цена - это целое положительное число. '
                             'Максимальная цена должна быть больше минимальной. '
                             'Введите корректную максимальную цену!',
                             reply_markup=kb_inline.get_kb_inline_delete())
        await SearchHotels.price_max.set()
    else:
        async with state.proxy() as data:
            data['price_max'] = int(price_max)
        await message.delete()
        await message.answer('Введите минимальное расстояние от центра в км',
                             reply_markup=kb_inline.get_kb_inline_delete())
        await SearchHotels.center_min.set()


async def enter_center_min(message: types.Message, state: FSMContext) -> None:
    """
    The answer to the user when a message sent from state 'center_min'
    Setting a state 'center_max'.
    """
    center_min = message.text.strip()
    if center_min.isdigit():
        async with state.proxy() as data:
            data['center_min'] = int(center_min)
        await message.delete()
        await message.answer('Введите максимальное расстояние до центра в км',
                             reply_markup=kb_inline.get_kb_inline_delete())
        await SearchHotels.center_max.set()
    else:
        await message.answer('⛔ Расстояние - это целое положительное число. Введите корректное минимальное расстояние!',
                             reply_markup=kb_inline.get_kb_inline_delete())
        await SearchHotels.center_min.set()


async def enter_center_max(message: types.Message, state: FSMContext) -> None:
    """
    The answer to the user when a message sent from state 'center_max'
    Setting a state 'search'.
    """
    center_max = message.text.strip()
    async with state.proxy() as data:
        center_min = data.get('center_min')
    if not center_max.isdigit() or center_min > int(center_max):
        await message.answer('⛔ Максимальное расстояние - это целое положительное число. '
                             'Максимальное расстояние должно быть больше минимального. '
                             'Введите корректное максимальное расстояние!',
                             reply_markup=kb_inline.get_kb_inline_delete())
        await SearchHotels.center_max.set()
    else:
        async with state.proxy() as data:
            data['center_max'] = int(center_max)
            data['time_request'] = datetime.datetime.now()
        await message.delete()
        await message.answer('Нажмите СТАРТ, чтобы начать поиск',
                             reply_markup=kb_inline.get_kb_inline_start())
        await SearchHotels.search.set()


async def start_searching(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    The answer to the user when a state is 'search' and callback is 'search'
    Setting a state 'page'.
    When hotels are not found close state machine
    """
    async with state.proxy() as data:
        user_id = callback.from_user.id
        date_request = data.get('time_request')
        type_search = data.get('command')
        city = data.get('city')
        area_id = data.get('area_id')
        area_name = data.get('area_name', 'в моём городе')
        latitude = data.get('lat')
        longitude = data.get('lon')
        amount_hotels = data.get('amount_hotels')
        has_photo = data.get('has_photo')
        amount_photos = data.get('amount_photos')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        price_min = data.get('price_min', 'нет')
        price_max = data.get('price_max', 'нет')
        center_min = data.get('center_min', 'нет')
        center_max = data.get('center_max', 'нет')

    db.add_user_request(user_id=user_id, date_request=date_request, type_search=type_search, city=city, area_id=area_id,
                        area_name=area_name, latitude=latitude, longitude=longitude, amount_hotels=amount_hotels,
                        has_photo=has_photo, amount_photos=amount_photos, check_in=check_in, check_out=check_out,
                        price_min=price_min, price_max=price_max, center_min=center_min, center_max=center_max)

    request = f'✅ Ок!\n' \
              f'<b>Тип поиска</b>: {type_search}\n' \
              f'<b>Место</b>: {area_name}\n' \
              f'<b>Количество отелей:</b> {amount_hotels}\n' \
              f'<b>Количество фотографий:</b> {amount_photos}\n' \
              f'<b>Количество ночей:</b> {(check_out - check_in).days} ' \
              f'(c {check_in} по {check_out})\n' \
              f'<b>Минимальная цена, $:</b> {price_min}\n' \
              f'<b>Максимальная цена, $:</b> {price_max}\n' \
              f'<b>Минимальное расстояние до центра, км:</b> {center_min}\n' \
              f'<b>Максимальное расстояние до центра, км:</b> {center_max}\n'

    await callback.message.delete()
    await callback.message.answer(request, parse_mode='HTML')
    await callback.message.answer(text='Пожалуйста, подождите! Ищу варианты ...', parse_mode='HTML',
                                  reply_markup=kb_inline.get_kb_inline_delete())
    hotels_list = get_hotels_list(data)
    logger.info('Ready list of hotels')
    if len(hotels_list) != 0:
        async with state.proxy() as data:
            data['hotels_list'] = hotels_list
            data['page'] = 0
        for hotel in hotels_list:
            request_id = db.get_request_id(date_request=data['time_request'])[0]
            db.add_hotel_report(user_id=callback.from_user.id, request_id=request_id,
                                date_report=datetime.datetime.now(), hotel_id=hotel.hotel_id, name=hotel.name,
                                address=hotel.address, center=hotel.center, price=hotel.price,
                                photos=hotel.photos)
        await callback.message.answer(text='Варианты отелей:',
                                      reply_markup=await get_kb_inline_hotels_list(state=state, page_shift=0))
    else:
        await callback.message.answer(text='К сожалению ничего не могу найти для вас 😞\n'
                                           'Можно попробовать ещё раз, изменив критерии поиска!'
                                           '\n\n/lowprice\n\n/bestdeal\n\n/mycity',
                                      reply_markup=kb_inline.get_kb_inline_delete())
        logger.info('Hotels are not found')
        await state.finish()


async def pagination(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Inline keyboard update when paginating a hotel list
    """

    if callback.data == 'next':
        await callback.message.delete()
        await callback.message.answer(text='Варианты отелей',
                                      reply_markup=await get_kb_inline_hotels_list(state=state, page_shift=1))
    elif callback.data == 'back':
        await callback.message.delete()
        await callback.message.answer(text='Варианты отелей',
                                      reply_markup=await get_kb_inline_hotels_list(state=state, page_shift=-1))
    elif callback.data == 'to_hotels':
        await callback.message.delete()
        await callback.message.answer(text='Варианты отелей',
                                      reply_markup=await get_kb_inline_hotels_list(state=state, page_shift=0))

    elif callback.data.split('_')[0] == 'hotel':
        async with state.proxy() as data:
            hotels_list = data.get('hotels_list')
        hotel_id = callback.data.split('_')[1]
        hotel_info = ''
        short_info = ''
        album = MediaGroup()
        for i_hotel in hotels_list:
            if i_hotel.hotel_id == hotel_id:
                amount_nights = (data["check_out"] - data["check_in"]).days
                hotel_info = f'🏨 <b>{i_hotel.name}</b>\n📍 <b>Адрес:</b>  {i_hotel.address}\n' \
                             f'📏 <b>Расстояние до центра:</b>  {round(i_hotel.center * 1.6)} км\n' \
                             f'💲 <b>Цена за ночь:</b>  {round(i_hotel.price)} $' \
                             f'\n💰 <b>Cтоимость за {amount_nights} ноч.:' \
                             f'</b>  {round(amount_nights * i_hotel.price)} $\n' \
                             f'🔗 <b>Ссылка:</b>  https://www.hotels.com/h{hotel_id}.Hotel-Information'

                if i_hotel.photos is not None:
                    short_info = f'<b>{i_hotel.name}</b>, {round(i_hotel.price)} $ за ночь'
                    photos_list = i_hotel.photos.split(', ')
                    for photo in photos_list:
                        album.attach_photo(photo=photo)
                break

        if short_info != '':
            await callback.message.answer(text=short_info, parse_mode='HTML')
            await callback.message.answer_media_group(media=album)

        await callback.message.delete()
        await callback.message.answer(text=hotel_info, parse_mode='HTML',
                                      reply_markup=get_kb_inline_back_hotels_list())

    elif callback.data == 'stop':
        await callback.message.delete()
        await callback.message.answer('Вы закрыли список предложенных вариантов.\nМожно поискать еще!\n\n/lowprice'
                                      '\n\n/bestdeal\n\n/mycity\n\nИстория запросов:\n\n/history',
                                      reply_markup=kb_inline.get_kb_inline_delete())
        logger.info('Hotel browsing stopped')
        await state.finish()


def register_handlers(dp: Dispatcher) -> None:
    """
    Handlers registration
    """
    dp.register_message_handler(city_start, commands=['lowprice', 'bestdeal'])
    dp.register_message_handler(geolocation_start, commands=['mycity'])
    dp.register_message_handler(enter_geolocation, content_types=['location'], state=SearchHotels.geolocation)
    dp.register_message_handler(finish_geolocation, state=SearchHotels.geolocation)
    dp.register_message_handler(enter_city_name, state=SearchHotels.city)
    dp.register_callback_query_handler(enter_area_name, Text(startswith='area_'), state=SearchHotels.area)
    dp.register_callback_query_handler(enter_amount_hotels, Text(startswith='number_'),
                                       state=SearchHotels.amount_hotels)
    dp.register_callback_query_handler(enter_has_photos, Text(startswith='has_'), state=SearchHotels.has_photo)
    dp.register_callback_query_handler(enter_amount_photos, Text(startswith='number_'),
                                       state=SearchHotels.amount_photos)
    dp.register_callback_query_handler(enter_date_check_in, simple_cal_callback.filter(),
                                       state=SearchHotels.date_check_in)
    dp.register_callback_query_handler(enter_date_check_out, simple_cal_callback.filter(),
                                       state=SearchHotels.date_check_out)
    dp.register_message_handler(enter_price_min, state=SearchHotels.price_min)
    dp.register_message_handler(enter_price_max, state=SearchHotels.price_max)
    dp.register_message_handler(enter_center_min, state=SearchHotels.center_min)
    dp.register_message_handler(enter_center_max, state=SearchHotels.center_max)
    dp.register_callback_query_handler(start_searching, text='search', state=SearchHotels.search)
    dp.register_message_handler(reset_state, state=[SearchHotels.area, SearchHotels.amount_hotels,
                                                    SearchHotels.amount_photos, SearchHotels.date_check_in,
                                                    SearchHotels.date_check_out, SearchHotels.search,
                                                    SearchHotels.page, History.step])
    dp.register_callback_query_handler(pagination, state=SearchHotels.search)
    dp.register_callback_query_handler(process_callback_delete, text='delete', state='*')
    dp.register_callback_query_handler(stop, text='stop', state='*')
