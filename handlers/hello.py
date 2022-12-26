import sqlite3
from datetime import datetime

from aiogram import types, Dispatcher
from loguru import logger

from loader import db


async def hello_bot(message: types.Message) -> None:
    """
    The answer to the user if a command is 'hello_world' or message is "Привет".
    Adding user data to the Users table in the database, if the user connected to the bot for the first time.
    """
    logger.info('Start hello_world command')
    try:
        db.add_user(id_user=message.from_user.id, name=message.from_user.first_name, connection_date=datetime.now())
    except sqlite3.IntegrityError as err:
        logger.info(err)
    await message.answer(f'Привет, {message.from_user.first_name}!  \U0001F60A\n'
                         f'Меня зовут @HotelRapidBot. Я помогу тебе выбрать отель. Доступные команды есть в справке '
                         f'/help и в основном меню.')
    await message.delete()


def register_hello_bot(dp: Dispatcher) -> None:
    """
    hello_bot handler registration
    """
    dp.register_message_handler(hello_bot, text='Привет')
    dp.register_message_handler(hello_bot, commands=['hello_world'])
