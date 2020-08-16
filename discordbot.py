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
    print('opus is loaded')
client = discord.Client()


def find_voice_client(voice_channel):
    for voice_client in client.voice_clients:
        if voice_client.channel == voice_channel:
            return voice_client


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

    voice_channels = []
    for channel in client.get_all_channels():
        if isinstance(channel, discord.VoiceChannel):
            voice_channels.append(channel)
    print(len(voice_channels), 'voice channels found')


@client.event
async def on_message(msg):
    tch = msg.channel
    print(f'{msg.author} wrote on {tch.guild}/{tch}')
    voice_client = None
    for vcl in client.voice_clients:
        if vcl.channel.guild == tch.guild \
          and vcl.channel.name == tch.name:
            voice_client = vcl
            break
    if voice_client:
        data = await openjtalk.exec(msg.content)
        stream = io.BytesIO(data)
        audio_source = discord.PCMAudio(stream)
        while voice_client.is_playing():
            print('voice_client.is_playing')
            await asyncio.sleep(0.5)
        voice_client.play(audio_source)


@client.event
async def on_voice_state_update(member, before, after):

    if not before.channel and after.channel:
        vch = after.channel
        if member == vch.guild.owner:
            print(f'guild owner {member} connected {vch.guild}/{vch}')
            voice_client = await vch.connect()
            await asyncio.sleep(CONFIG['connect_after'])
            data = await openjtalk.exec(CONFIG['voice.hello'])
            stream = io.BytesIO(data)
            audio_source = discord.PCMAudio(stream)
            voice_client.play(audio_source)
            return
        return

    if before.channel and not after.channel:
        vch = before.channel
        if member == vch.guild.owner:
            print(f'guild owner {member} disconnected {vch.guild}/{vch}')
            voice_client = find_voice_client(vch)
            await voice_client.disconnect()
            return
        return


if __name__ == "__main__":
    client.run(CONFIG['token'])
