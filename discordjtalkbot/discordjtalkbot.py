"""main entry point """

import logging
import os
from os.path import join, dirname, basename

from ctypes.util import find_library

import discord
from discord.ext import commands

from cogs.modules import environ

logging.basicConfig()
LOG = logging.getLogger(basename(__file__) + '$' + __name__)


def main():
    """Main entry point. """

    bot = commands.Bot('$')
    bot.load_extension("cogs.autoreadercog")
    appenv = environ.get_appenv()
    appenv.add_field('prefix', default='$', help='command prefix (%(default)s)')
    appenv.add_field('token', help='bot token')

    # environment variables
    BOT_NAME = 'discordjtalkbot'
    appenv.load_env(prefix=BOT_NAME)
    # setting file
    filename =  BOT_NAME + '-config.json'
    file_path = join(dirname(__file__), 'cogs' + os.sep + 'modules' + os.sep +'files' + os.sep + filename)
    if os.path.exists(file_path):
        appenv.load_json(file_path)

    LOG.setLevel(logging.INFO)

    # dcoker envrionment support
    env_list = []
    if os.getenv('IS_DOCKER'):
        LOG.info('docker mode.')
        if os.getenv('TOKEN'):
            env_list.extend(['--token', os.getenv('TOKEN')])
        if os.getenv('VOICE_HELLO'):
            env_list.extend(['--voice_hello', os.getenv('VOICE_HELLO')])
        if os.getenv('TEXT_START'):
            env_list.extend(['--text_start', os.getenv('TEXT_START')])
        if os.getenv('TEXT_END'):
            env_list.extend(['--text_end', os.getenv('TEXT_END')])
        if os.getenv('OPEN_JTALK_FLAGS'):
            env_list.extend(['--open_jtalk_flags', os.getenv('OPEN_JTALK_FLAGS')])
        if env_list:
            LOG.info(env_list)
            appenv.load_args(env_list)

    discord.opus.load_opus(find_library('opus'))
    if discord.opus.is_loaded():
        LOG.info('Opus library is loaded.')

    bot.command_prefix = appenv.get('prefix', '$')
    intents = discord.Intents.default()
    intents.members = True
    intents.presences = True
    LOG.info(f'{__file__} is running.')
    bot.run(appenv['token'])


if __name__ == "__main__":
    main()