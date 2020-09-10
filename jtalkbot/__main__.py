"""main entry point """

import argparse
import asyncio
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


class MyBot(commands.Bot):
    """Bot class """

    def __init__(self, *args, **kwds):
        """Constructor. """

        super().__init__(*args, **kwds)

    async def on_ready(self):
        """Called when the client is done preparing the data received
        from Discord. """

        LOG.info(f'Logged in as {self.user}.')


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
    parser.add_argument('--open_jtalk_x',
        help='open_jtalk dictionary directory')
    parser.add_argument('--open_jtalk_m',
        help='open_jtalk HTS voice file')
    parser.add_argument('--open_jtalk_p', type=int,
        help='open_jtalk frame period (point)')
    parser.add_argument('--open_jtalk_a', type=float,
        help='open_jtalk all-pass constant')
    parser.add_argument('--open_jtalk_b', type=float,
        help='open_jtalk postfiltering coefficient')
    parser.add_argument('--open_jtalk_r', type=float,
        help='open_jtalk speech speed rate')
    parser.add_argument('--open_jtalk_fm', type=float,
        help='open_jtalk additional half-tone')
    parser.add_argument('--open_jtalk_u', type=float,
        help='open_jtalk voiced/unvoiced threshold')
    parser.add_argument('--open_jtalk_jm', type=float,
        help='open_jtalk weight of GV for spectrum')
    parser.add_argument('--open_jtalk_jf', type=float,
        help='open_jtalk weight of GV for log F0')
    parser.add_argument('--open_jtalk_g', type=float,
        help='open_jtalk volume (dB)')
    parser.add_argument('--open_jtalk_z', type=int,
        help='open_jtalk audio buffer size (if i==0, turn off)')
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

    bot = MyBot(command_prefix='$')
    bot.config = CONFIG
    bot.load_extension('jtalkbot.autoreader')
    bot.run(CONFIG['token'])


if __name__ == "__main__":
    main()
