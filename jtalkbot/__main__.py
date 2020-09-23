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
from . import environ


logging.basicConfig()
LOG = logging.getLogger(__name__)


def main():
    """Main entry point. """

    bot = commands.Bot()
    bot.load_extension('jtalkbot.autoreader')

    appenv = environ.get_appenv()
    appenv.add_field('prefix', default='$', help='command prefix')
    appenv.add_field('token', help='bot token')

    # environment variables
    appenv.load_env(prefix='jtalkbot')
    # setting file
    filename = 'jtalkbot-config.json'
    if os.path.exists(filename):
        appenv.load_json(filename)
    # command line args
    parser = ArgumentParser()
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s '+VERSION)
    appenv.load_args(parser=parser)

    bot.com

    LOG.setLevel(logging.INFO)
    LOG.info(f'jtalkbot {VERSION}')

    discord.opus.load_opus(find_library('opus'))
    if discord.opus.is_loaded():
        LOG.info('Opus library is loaded.')

    bot.run(appenv['token'])


if __name__ == "__main__":
    main()
