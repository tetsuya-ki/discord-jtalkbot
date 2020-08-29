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


logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


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
            logger.info(f'config file: {__config__}')
            with open(filename) as f:
                return json.load(f)
    logger.error(f'{config_name} not found.')
    sys.exit(1)

CONFIG = load_config()


client = discord.Client()


def find_voice_client(vch: discord.VoiceChannel) -> discord.VoiceClient:

    for vcl in client.voice_clients:
        if vcl.channel == vch:
            return vcl
    return None


async def talk(vcl: discord.VoiceClient,
               text: str,
               command: str = None,
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

    if command is None:
        command = CONFIG.get('open_jtalk')
    if dic is None:
        dic = CONFIG.get('open_jtalk/x')
    if voice is None:
        voice = CONFIG.get('open_jtalk/m')
    if sampling is None:
        sampling = CONFIG.get('open_jtalk/s')
    if frameperiod is None:
        frameperiod = CONFIG.get('open_jtalk/p')
    if allpass is None:
        allpass = CONFIG.get('open_jtalk/a')
    if command is None:
        command = CONFIG.get('open_jtalk/b')
    if speedrate is None:
        speedrate = CONFIG.get('open_jtalk/r')
    if halftone is None:
        halftone = CONFIG.get('open_jtalk/fm')
    if threshold is None:
        threshold = CONFIG.get('open_jtalk/u')
    if spectrum is None:
        spectrum = CONFIG.get('open_jtalk/jm')
    if logf0 is None:
        logf0 = CONFIG.get('open_jtalk/jf')
    if volume is None:
        volume = CONFIG.get('open_jtalk/g')
    if buffersize is None:
        buffersize = CONFIG.get('open_jtalk/z')

    data = await openjtalk.async_talk(
        text, command=command, dic=dic, voice=voice,
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


@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}.')


@client.event
async def on_message(msg: discord.Message):

    if msg.author == client.user:
        return

    tch = msg.channel
    vcl = None
    for vcl in client.voice_clients:
        if vcl.channel.guild == tch.guild and vcl.channel.name == tch.name:
            vcl = vcl
            break
    if vcl:
        logger.info(f'Reading {msg.author}\'s post on t:{tch.guild}/{tch}.')
        await talk(vcl, msg.content)


@client.event
async def on_voice_state_update(member: discord.Member,
                                before: discord.VoiceState,
                                after: discord.VoiceState):

    if not before.channel and after.channel:
        # someone connected the voice channel.
        vch = after.channel
        if member == vch.guild.owner:
            logger.info(
                f'The guild owner {member} connected v:{vch.guild}/{vch}.')
            vcl = await vch.connect()
        elif member == client.user:
            logger.info(f'{member} connected v:{vch.guild}/{vch}.')
            vcl = find_voice_client(vch)
            await talk(vcl, CONFIG['voice/hello'])
            for tch in vch.guild.text_channels:
                if vch.name == tch.name:
                    await tch.send(CONFIG['text/start'])
                    break
        else:
            logger.info(f'{member} connected v:{vch.guild}/{vch}.')


    elif before.channel and not after.channel:
        # someone disconnected the voice channel.
        vch = before.channel
        if member == vch.guild.owner:
            logger.info(
                f'The guild owner {member} disconnected v:{vch.guild}/{vch}.')
            vcl = find_voice_client(vch)
            if vcl and vcl.is_connected():
                await vcl.disconnect()
            for tch in vch.guild.text_channels:
                if vch.name == tch.name:
                    await tch.send(CONFIG['text/end'])
                    break
        else:
            logger.info(f'{member} disconnected v:{vch.guild}/{vch}.')


def main():
    """Main entry point. """

    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', action='store_true',
                        help='print the version number and exit')
    parser.add_argument('-t', '--token',
                        help='override the Discord bot token')
    parser.add_argument('--open_jtalk',
                        help='open_jtalk command')
    parser.add_argument('--open_jtalk-x',
                        help='open_jtalk dictionary directory')
    parser.add_argument('--open_jtalk-m',
                        help='open_jtalk HTS voice file')
    parser.add_argument('--open_jtalk-s', type=int,
                        help='open_jtalk sampling frequency')
    parser.add_argument('--open_jtalk-p', type=int,
                        help='open_jtalk frame period (point)')
    parser.add_argument('--open_jtalk-a', type=float,
                        help='open_jtalk all-pass constant')
    parser.add_argument('--open_jtalk-b', type=float,
                        help='open_jtalk postfiltering coefficient')
    parser.add_argument('--open_jtalk-r', type=float,
                        help='open_jtalk speech speed rate')
    parser.add_argument('--open_jtalk-fm', type=float,
                        help='open_jtalk additional half-tone')
    parser.add_argument('--open_jtalk-u', type=float,
                        help='open_jtalk voiced/unvoiced threshold')
    parser.add_argument('--open_jtalk-jm', type=float,
                        help='open_jtalk weight of GV for spectrum')
    parser.add_argument('--open_jtalk-jf', type=float,
                        help='open_jtalk weight of GV for log F0')
    parser.add_argument('--open_jtalk-g', type=float,
                        help='open_jtalk volume (dB)')
    parser.add_argument('--open_jtalk-z', type=int,
                        help='open_jtalk audio buffer size (if i==0, turn off)')
    args = parser.parse_args()

    if args.version:
        print(__package__, VERSION)
        sys.exit()
    if args.token is not None:
        CONFIG['token'] = args.token
    if args.open_jtalk_x is not None:
        CONFIG['open_jtalk/x'] = args.open_jtalk_x
    if args.open_jtalk_m is not None:
        CONFIG['open_jtalk/m'] = args.open_jtalk_m
    if args.open_jtalk_s is not None:
        CONFIG['open_jtalk/s'] = args.open_jtalk_s
    if args.open_jtalk_p is not None:
        CONFIG['open_jtalk/p'] = args.open_jtalk_p
    if args.open_jtalk_a is not None:
        CONFIG['open_jtalk/a'] = args.open_jtalk_a
    if args.open_jtalk_b is not None:
        CONFIG['open_jtalk/b'] = args.open_jtalk_b
    if args.open_jtalk_r is not None:
        CONFIG['open_jtalk/r'] = args.open_jtalk_r
    if args.open_jtalk_fm is not None:
        CONFIG['open_jtalk/fm'] = args.open_jtalk_fm
    if args.open_jtalk_u is not None:
        CONFIG['open_jtalk/u'] = args.open_jtalk_u
    if args.open_jtalk_jm is not None:
        CONFIG['open_jtalk/jm'] = args.open_jtalk_jm
    if args.open_jtalk_jf is not None:
        CONFIG['open_jtalk/jf'] = args.open_jtalk_jf
    if args.open_jtalk_g is not None:
        CONFIG['open_jtalk/g'] = args.open_jtalk_g
    if args.open_jtalk_z is not None:
        CONFIG['open_jtalk/z'] = args.open_jtalk_z

    logger.setLevel(logging.INFO)
    discord.opus.load_opus(find_library('opus'))
    if discord.opus.is_loaded():
        logger.info('Opus library is loaded.')
    client.run(CONFIG['token'])


if __name__ == "__main__":
    main()
