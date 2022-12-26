from aiogram import types, Dispatcher
from loguru import logger


async def get_help(message: types.Message) -> None:
    """
    The answer to the user if a command is 'help'
    """
    logger.info('Start help command')
    await message.delete()
    text = """
    Я помогу выбрать тебе отель.

В моём меню доступны следующие команды:

/start выводит приветственное сообщение и подключает вас к боту

/lowprice ищет топ самых дешёвых отелей

/bestdeals ищет отели, наиболее подходящие по цене и расположению от центра города

/mycity ищет отели в вашем городе по цене и расположению от центра

/history показывает историю ваших запросов

/hello_world здоровается с пользователем

/help показывает раздел помощи
"""

    await message.answer(text=text)


def register_get_help(dp: Dispatcher) -> None:
    """
    get_help handler registration
    """
    dp.register_message_handler(get_help, commands=['help'])
