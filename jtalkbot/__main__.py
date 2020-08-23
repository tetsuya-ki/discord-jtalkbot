"""main entry point """

import argparse
import asyncio
import io
import json
import os.path
import sys

import discord

from . import VERSION
from . import openjtalk


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
            print(f'config file: {__config__}', file=sys.stderr)
            with open(filename) as f:
                return json.load(f)
    print(f'{config_name} not found.', file=sys.stderr)
    sys.exit(1)

CONFIG = load_config()


discord.opus.load_opus(CONFIG['libopus'])
if discord.opus.is_loaded():
    print('Opus library is loaded.')
client = discord.Client()


def find_voice_client(vch: discord.VoiceChannel) -> discord.VoiceClient:

    for vcl in client.voice_clients:
        if vcl.channel == vch:
            return vcl
    return None


async def talk(vcl: discord.VoiceClient, text: str):

    data = await openjtalk.async_talk(text, speedrate=0.8)
    stream = io.BytesIO(data)
    audio = discord.PCMAudio(stream)
    while not vcl.is_connected() or vcl.is_playing():
        await asyncio.sleep(0.1)
    vcl.play(audio, after=lambda e: stream.close())


@client.event
async def on_ready():
    print(f'Logged in as {client.user}.')


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
        print(f'Reading {msg.author}\'s post on t:{tch.guild}/{tch}.')
        await talk(vcl, msg.content)


@client.event
async def on_voice_state_update(member: discord.Member,
                                before: discord.VoiceState,
                                after: discord.VoiceState):

    if not before.channel and after.channel:
        # someone connected the voice channel.
        vch = after.channel
        if member == vch.guild.owner:
            print(f'The guild owner {member} connected v:{vch.guild}/{vch}.')
            vcl = await vch.connect()
        elif member == client.user:
            print(f'{member} connected v:{vch.guild}/{vch}.')
            vcl = find_voice_client(vch)
            await talk(vcl, CONFIG['voice/hello'])
            for tch in vch.guild.text_channels:
                if vch.name == tch.name:
                    await tch.send(CONFIG['text/start'])
                    break
        else:
            print(f'{member} connected v:{vch.guild}/{vch}.')


    elif before.channel and not after.channel:
        # someone disconnected the voice channel.
        vch = before.channel
        if member == vch.guild.owner:
            print(f'The guild owner {member} disconnected v:{vch.guild}/{vch}.')
            vcl = find_voice_client(vch)
            if vcl and vcl.is_connected():
                await vcl.disconnect()
            for tch in vch.guild.text_channels:
                if vch.name == tch.name:
                    await tch.send(CONFIG['text/end'])
                    break
        else:
            print(f'{member} disconnected v:{vch.guild}/{vch}.')


def main():
    """Main entry point. """

    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', action='store_true',
                        help='print the version number and exit')
    args = parser.parse_args()

    if args.version:
        print(VERSION)
        sys.exit()

    client.run(CONFIG['token'])


if __name__ == "__main__":
    main()
