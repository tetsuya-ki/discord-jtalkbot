#!/usr/bin/env python

import asyncio
import io
import json

import discord

import openjtalk


with open('discordbot-config.json') as f:
    CONFIG = json.load(f)


discord.opus.load_opus(CONFIG['libopus'])
if discord.opus.is_loaded():
    print('Opus library is loaded.')
client = discord.Client()


def find_voice_client(voice_channel: discord.VoiceChannel) -> discord.VoiceClient:

    for voice_client in client.voice_clients:
        if voice_client.channel == voice_channel:
            return voice_client


async def talk(voice_client: discord.VoiceClient, text: str):

    data = await openjtalk.exec(text)
    stream = io.BytesIO(data)
    audio = discord.PCMAudio(stream)
    while not voice_client.is_connected() or voice_client.is_playing():
        await asyncio.sleep(0.1)
    voice_client.play(audio, after=lambda e: stream.close())



@client.event
async def on_ready():
    print(f'Logged in as {client.user}.')


@client.event
async def on_message(msg: discord.Message):

    tch = msg.channel

    voice_client = None
    for vcl in client.voice_clients:
        if vcl.channel.guild == tch.guild and vcl.channel.name == tch.name:
            voice_client = vcl
            break

    if voice_client:
        print(f'Reading {msg.author}\'s post on t:{tch.guild}/{tch}.')
        await talk(msg.content)


@client.event
async def on_voice_state_update(member: discord.Member,
                                before: discord.VoiceState,
                                after: discord.VoiceState):

    if not before.channel and after.channel:
        vch = after.channel
        if member == vch.guild.owner:
            print(f'The guild owner {member} connected v:{vch.guild}/{vch}.')
            voice_client = await vch.connect()
            await talk(voice_client, CONFIG['voice.hello'])

    elif before.channel and not after.channel:
        vch = before.channel
        if member == vch.guild.owner:
            print(f'The guild owner {member} disconnected v:{vch.guild}/{vch}.')
            voice_client = find_voice_client(vch)
            await voice_client.disconnect()


if __name__ == "__main__":
    client.run(CONFIG['token'])
