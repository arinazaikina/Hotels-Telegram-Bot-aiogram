import sqlite3
from datetime import datetime

from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import CommandStart
from loguru import logger

from loader import db


async def bot_start(message: types.Message):
    """
    Sends a welcome message to the user on the /start command.
    Writes user data to the Users table in the database if the user is connecting to the bot for the first time.
    """
    try:
        db.add_user(id_user=message.from_user.id, name=message.from_user.first_name, connection_date=datetime.now())
    except sqlite3.IntegrityError as err:
        logger.info(err)
    await message.answer(f'Привет, {message.from_user.first_name}!  \U0001F60A\n'
                         f'Я - бот, который поможет тебе выбрать отель.')
    await message.delete()


def register_bot_start(dp: Dispatcher):
    """
    Registers the bot_start handler
    """
    dp.register_message_handler(bot_start, CommandStart())
