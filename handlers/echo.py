from aiogram import types, Dispatcher
from loguru import logger


async def bot_echo(message: types.Message) -> None:
    """
    The answer to the user if a command is not on the bot menu
    """
    await message.answer('Не знаю такой команды')


def register_bot_echo(dp: Dispatcher) -> None:
    """
    bot_echo handler registration
    """
    logger.info('Start echo')
    dp.register_message_handler(bot_echo)
