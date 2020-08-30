"""main entry point """

import argparse
import asyncio
import io
import json
import logging
import os
import sys
from ctypes.util import find_library

import discord

from . import VERSION
from . import openjtalk


logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


class Bot(discord.Client):
    """Bot class """

    def __init__(self, *args, **kwds):
        """Constructor. """

        super().__init__(*args, **kwds)

    async def on_ready(self):
        """Called when the client is done preparing the data received
        from Discord. """

        LOG.info(f'Logged in as {self.user}.')


    async def on_message(self, msg: discord.Message):
        """Called when a `Message` is created and sent. """

        if msg.author == self.user:
            return

        tch = msg.channel
        vcl = None
        for vcl in self.voice_clients:
            if vcl.channel.guild == tch.guild and vcl.channel.name == tch.name:
                vcl = vcl
                break
        if vcl:
            LOG.info(f'Reading {msg.author}\'s post on t:{tch.guild}/{tch}.')
            await talk(vcl, msg.content)


    async def on_voice_state_update(self,
                                    member: discord.Member,
                                    before: discord.VoiceState,
                                    after: discord.VoiceState):
        """Called when a `Member` changes their `VoiceState`. """

        if not before.channel and after.channel:
            # someone connected the voice channel.
            vch = after.channel
            if member == vch.guild.owner:
                LOG.info(
                    f'Guild owner {member} connected v:{vch.guild}/{vch}.')
                vcl = await vch.connect()
            elif member == self.user:
                LOG.info(f'{member} connected v:{vch.guild}/{vch}.')
                vcl = discord.utils.find(lambda x: x.channel == vch,
                                         self.voice_clients)
                await talk(vcl, CONFIG['voice_hello'])
                for tch in vch.guild.text_channels:
                    if vch.name == tch.name:
                        await tch.send(CONFIG['text_start'])
                        break
            else:
                LOG.info(f'{member} connected v:{vch.guild}/{vch}.')


        elif before.channel and not after.channel:
            # someone disconnected the voice channel.
            vch = before.channel
            if member == vch.guild.owner:
                LOG.info(
                    f'Guild owner {member} disconnected v:{vch.guild}/{vch}.')
                vcl = discord.utils.find(lambda x: x.channel == vch,
                                         self.voice_clients)
                if vcl and vcl.is_connected():
                    await vcl.disconnect()
                for tch in vch.guild.text_channels:
                    if vch.name == tch.name:
                        await tch.send(CONFIG['text_end'])
                        break
            else:
                LOG.info(f'{member} disconnected v:{vch.guild}/{vch}.')




def load_config() -> dict:
    """Search config file and return its config dict object.

    The configuration file will be found in such order bellow:

    1. ./jtalkbot-config.json
    2. ~/jtalkbot-config.json
    2. ~/.local/jtalkbot-config.json
    3. {module directory}/jtalkbot-config.json
    4. The file specified in JTALKBOT_CONFIG environment value.
    """
    global __config__
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
            LOG.info(f'config file: {__config__}')
            with open(filename) as f:
                return json.load(f)
    LOG.error(f'{config_name} not found.')
    sys.exit(1)

CONFIG = load_config()


async def talk(vcl: discord.VoiceClient,
               text: str,
               dic: str = None,
               voice: str = None,
               sampling: int = None,
               frameperiod: int = None,
               allpass: float = None,
               postfilter: float = None,
               speedrate: float = None,
               halftone: float = None,
               threshold: float = None,
               spectrum: float = None,
               logf0: float = None,
               volume: float = None,
               buffersize: float = None):

    if dic is None:
        dic = CONFIG.get('open_jtalk_x')
    if voice is None:
        voice = CONFIG.get('open_jtalk_m')
    if sampling is None:
        sampling = CONFIG.get('open_jtalk_s')
    if frameperiod is None:
        frameperiod = CONFIG.get('open_jtalk_p')
    if allpass is None:
        allpass = CONFIG.get('open_jtalk_a')
    if postfilter is None:
        postfilter = CONFIG.get('open_jtalk_b')
    if speedrate is None:
        speedrate = CONFIG.get('open_jtalk_r')
    if halftone is None:
        halftone = CONFIG.get('open_jtalk_fm')
    if threshold is None:
        threshold = CONFIG.get('open_jtalk_u')
    if spectrum is None:
        spectrum = CONFIG.get('open_jtalk_jm')
    if logf0 is None:
        logf0 = CONFIG.get('open_jtalk_jf')
    if volume is None:
        volume = CONFIG.get('open_jtalk_g')
    if buffersize is None:
        buffersize = CONFIG.get('open_jtalk_z')

    data = await openjtalk.async_talk(
        text, dic=dic, voice=voice,
        sampling=sampling, frameperiod=frameperiod, allpass=allpass,
        postfilter=postfilter, speedrate=speedrate, halftone=halftone,
        threshold=threshold, spectrum=spectrum, logf0=logf0, volume=volume,
        buffersize=buffersize)
    stream = io.BytesIO(data)
    audio = discord.PCMAudio(stream)
    sleeptime = 0.1
    timeout = 6.0
    for _ in range(int(timeout / sleeptime)):
        if vcl.is_connected():
            break
        await asyncio.sleep(0.1)
    else:
        return
    while vcl.is_playing():
        await asyncio.sleep(0.1)
    vcl.play(audio, after=lambda e: stream.close())


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
    parser.add_argument('--open_jtalk_s', type=int,
                        help='open_jtalk sampling frequency')
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

    # Overwrite CONFIG with args parameters which are specified
    CONFIG.update((k, v) for (k, v) in vars(args).items() if v is not None)

    discord.opus.load_opus(find_library('opus'))
    if discord.opus.is_loaded():
        LOG.info('Opus library is loaded.')

    bot = Bot()
    bot.run(CONFIG['token'])


if __name__ == "__main__":
    main()
