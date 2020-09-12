"""main entry point """

import argparse
import json
import logging
import os
import sys
from ctypes.util import find_library

import discord
from discord.ext import commands

from . import VERSION


logging.basicConfig()
LOG = logging.getLogger(__name__)

__config__ = None
CONFIG = {}


def load_config():
    """Search config file and store its data into `CONFIG`.

    The configuration file will be found in such order bellow:

    1. ./jtalkbot-config.json
    2. ~/jtalkbot-config.json
    2. ~/.local/jtalkbot-config.json
    3. {module directory}/jtalkbot-config.json
    4. The file specified in JTALKBOT_CONFIG environment value.
    """
    global __config__, CONFIG
    config_name = 'jtalkbot-config.json'
    paths = [
        config_name,
        os.path.expanduser(f'~/{config_name}'),
        os.path.expanduser(f'~/.local/{config_name}'),
        os.path.join(os.path.dirname(__file__), config_name),
        os.environ.get('JTALKBOT_CONFIG')
    ]
    for filename in paths:
        if filename and os.path.exists(filename):
            __config__ = os.path.abspath(filename)
            with open(filename) as f:
                CONFIG = json.load(f)
                return
    LOG.error(f'{config_name} not found.')
    sys.exit(1)


def main():
    """Main entry point. """

    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', action='store_true',
        help='print the version number and exit')
    parser.add_argument('-t', '--token',
        help='override the Discord bot token')
    parser.add_argument('-J', '--open_jtalk_flags',
        help='open_jtalk command line options')
    args = parser.parse_args()

    if args.version:
        print(__package__, VERSION)
        sys.exit()

    LOG.setLevel(logging.INFO)
    LOG.info(f'jtalkbot {VERSION}')

    load_config()
    LOG.info(f'config file: {__config__}')

    # Overwrite CONFIG with args parameters which are specified
    CONFIG.update((k, v) for (k, v) in vars(args).items() if v is not None)

    discord.opus.load_opus(find_library('opus'))
    if discord.opus.is_loaded():
        LOG.info('Opus library is loaded.')

    bot = commands.Bot(command_prefix='$')
    bot.config = CONFIG
    bot.load_extension('jtalkbot.autoreader')
    bot.run(CONFIG['token'])


if __name__ == "__main__":
    main()
