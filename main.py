import asyncio
from loguru import logger

from aiogram import Dispatcher

import handlers
from data import config
from loader import bot, dp, db
from utils.notify_admins import on_starting_notify
from utils.set_bot_commands import set_bot_commands

logger.add(
    config.LOG_FILE,
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="1 week",
    compression="zip",
)


def register_all_handlers(dispatcher: Dispatcher):
    """
    Registers handlers
    """
    handlers.start.register_bot_start(dispatcher)
    handlers.hello.register_hello_bot(dispatcher)
    handlers.help.register_get_help(dispatcher)
    handlers.hotel_search.register_handlers(dispatcher)
    handlers.history.register_get_history(dispatcher)
    handlers.echo.register_bot_echo(dispatcher)


@logger.catch
async def main():
    """
    Bot start:
    - calling the handler registration function;
    - creating Users, UserRequests, Hotel, Callback tables in the database if they are not already created;
    - sending a message to the administrator that the bot is running;
    - prohibition of sending replies to those user messages that were sent at the time the bot was offline;
    - polling the Telegram server for updates;
    - command menu setup.

    Bot finish:
    - sends a message to the administrator about the bot stop;
    - closing session.
    """

    register_all_handlers(dp)
    db.create_table_users()
    db.create_table_user_requests()
    db.create_table_hotel()
    db.create_table_callback()

    try:
        logger.info('Бот запущен')
        await on_starting_notify(dp, 'Бот запущен')
        await dp.skip_updates()
        await dp.start_polling()
        await set_bot_commands(dp)
    finally:
        await on_starting_notify(dp, 'Бот остановлен')
        await dp.storage.close()
        await dp.storage.wait_closed()
        await (await bot.get_session()).close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error('Бот остановлен')
