from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from data import config
from database.sqlite_db import Database

"""The bot object is responsible for sending requests to Telegram. A token is imported from the config.py file to
launch the bot. The storage object is responsible for storing states. The dp object is the deliverer and handler of
all updates. The db object is a database (SQLite). Stores data about the user, his requests, data about the hotels
found, unique codes for city areas """
storage = MemoryStorage()
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)
db = Database()
