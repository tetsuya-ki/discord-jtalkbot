"""main entry point """

import json
import logging
import os
import sys
from argparse import ArgumentParser
from ctypes.util import find_library

import discord
from discord.ext import commands

from . import VERSION
from . import settings


logging.basicConfig()
LOG = logging.getLogger(__name__)


def main():
    """Main entry point. """

    LOG.setLevel(logging.INFO)
    LOG.info(f'jtalkbot {VERSION}')

    setting_schema = settings.get_setting_schema()
    setting_schema.register('prefix', default='$', help='command prefix')
    setting_schema.register('token', help='bot token')

    settings.load_settings(args, 'jtalkbot-config.json', os.environ)
    config = settings.get_settings()
    print(config)

    discord.opus.load_opus(find_library('opus'))
    if discord.opus.is_loaded():
        LOG.info('Opus library is loaded.')

    bot = commands.Bot(command_prefix=config.prefix)
    bot.load_extension('jtalkbot.autoreader')
    bot.run(config.token)


if __name__ == "__main__":
    main()
