from aiogram import types


async def set_bot_commands(dp) -> None:
    """
    Forms a list of commands in the bot menu
    """
    commands = {
        'start': 'Запуск бота',
        'lowprice': 'Топ самых дешёвых отелей',
        'bestdeal': 'По цене и расстоянию до центра',
        'mycity': 'В моём городе',
        'history': 'История поиска',
        'help': 'Справка',
        'hello_world': 'Поздороваться с ботом'
    }
    list_commands = []
    for command, name in commands.items():
        list_commands.append(types.BotCommand(command, name))
    await dp.bot.set_my_commands(list_commands)
