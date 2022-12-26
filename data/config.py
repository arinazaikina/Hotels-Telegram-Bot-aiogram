from environs import Env

"""
Creation of a object of environment.
Unloading variables from the environment: token line, bot administrators list, key line to API Rapid.
"""

env = Env()
env.read_env()

BOT_TOKEN = env.str('BOT_TOKEN')
ADMINS = env.list('ADMINS')
RAPID_API_KEY = env.str('RAPID_API_KEY')
RAPID_API_HOST = env.str('RAPID_API_HOST')
LOG_FILE = env.str('LOG_FILE')
