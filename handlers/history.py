from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from loguru import logger

from keyboards.kb_inline import history_action, get_kb_inline_delete, get_kb_inline_requests_list
from loader import db
from states.states import History


async def enter_history(message: types.Message, state: FSMContext) -> None:
    """
    The answer to the user when a command is 'history'.
    Setting a state 'step'.
    """
    logger.info(f'Start viewing the history of requests, user {message.from_user.id}')
    await History.step.set()
    requests = db.get_requests(user_id=message.from_user.id)
    if len(requests) == 0:
        text = '<b>История запросов пуста!</b>\nМожно что-нибудь поискать:\n\n/lowprice\n\n/bestdeal'
        await message.answer(text, parse_mode='HTML', reply_markup=get_kb_inline_delete())
        await state.finish()
    else:
        async with state.proxy() as data:
            data['page'] = 0
        await get_kb_inline_requests_list(message, state, page_shift=0, user_id=message.from_user.id)


async def pagination(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Inline keyboard update when paginating a user request list
    """
    if callback.data == 'next_step':
        await callback.message.delete()
        await get_kb_inline_requests_list(callback.message, state, page_shift=1, user_id=callback.message.chat.id)
    elif callback.data == 'back_step':
        await callback.message.delete()
        await get_kb_inline_requests_list(callback.message, state, page_shift=-1, user_id=callback.message.chat.id)
    elif callback.data == 'to_requests':
        await callback.message.delete()
        await get_kb_inline_requests_list(callback.message, state, page_shift=0, user_id=callback.message.chat.id)
    elif callback.data == 'finish':
        logger.info(f'Finish viewing the history of requests, user {callback.message.from_user.id}')
        await callback.message.delete()
        await callback.message.answer('Вы вышли из истории запросов', reply_markup=get_kb_inline_delete())
        await state.finish()


async def get_request_info(callback: types.CallbackQuery) -> None:
    """
    The answer to the user (hotels information) when a callback is "request_{id_request}" and state is "step".
    """
    request_id = callback.data.split('_')[1]
    hotels_list = db.get_report_hotel(request_id=request_id)
    if hotels_list:
        text = ''
        for hotel in hotels_list:
            name = hotel[5]
            address = hotel[6]
            center = round(float(hotel[7]) * 1.6)
            price = round(float(hotel[8]))
            link = f'https://www.hotels.com/h{hotel[4]}.Hotel-Information'
            hotel_info = f'🏨 <b>{name}</b>\n' \
                         f'📍 <b>Адрес:</b>  {address}\n' \
                         f'📏 <b>Расстояние до центра:</b>  {center} км\n' \
                         f'💲 <b>Цена за ночь:</b>  {price} $\n' \
                         f'🔗 <b>Ссылка:</b>  {link}\n\n\n'
            text += hotel_info
        await callback.message.delete()
        await callback.message.answer(text, parse_mode='HTML', reply_markup=history_action(request_id=request_id))
    else:
        await callback.message.delete()
        await callback.message.answer(text='Это пустой запрос. Здесь нет отелей',
                                      reply_markup=history_action(request_id=request_id))


async def delete_hotels(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Removing hotels from the Hotel table and removing requests from the UserRequests when a callback is 'delreq_'
    and state is 'step'.
    """
    request_id = callback.data.split('_')[1]
    db.delete_hotels(request_id=request_id)
    db.delete_request(id=request_id)
    await callback.answer('Отели и запрос удалены из истории')
    await callback.message.delete()
    await get_kb_inline_requests_list(callback.message, state, page_shift=0, user_id=callback.message.chat.id)


def register_get_history(dp: Dispatcher) -> None:
    """
    Enter_history, get_request_info, delete_hotels, pagination handlers registration
    """
    dp.register_message_handler(enter_history, text='/history')
    dp.register_callback_query_handler(get_request_info, Text(startswith='request_'), state=History.step)
    dp.register_callback_query_handler(delete_hotels, Text(startswith='delreq_'), state=History.step)
    dp.register_callback_query_handler(pagination, state=History.step)
