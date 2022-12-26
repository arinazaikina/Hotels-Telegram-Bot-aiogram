from loguru import logger

from aiogram import Dispatcher
from data.config import ADMINS


async def on_starting_notify(dp: Dispatcher, text: str) -> None:
    """
    Sends a message to bot admins
    """
    for admin in ADMINS:
        try:
            await dp.bot.send_message(admin, text)
        except (KeyboardInterrupt, SystemExit) as err:
            logger.error(err)
