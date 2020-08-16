#!/usr/bin/env python

import io
import json

import discord

import openjtalk


client = discord.Client()
voice_channels = []


data = openjtalk.run('こんにちは')


class MyAudio(discord.PCMAudio):

    def __init__(self, stream):
        super().__init__(stream)
        self.stream = stream

    def read(self):
        return self.stream.read(3840)


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

    for channel in client.get_all_channels():
        if isinstance(channel, discord.VoiceChannel):
            voice_channels.append(channel)
    print(len(voice_channels), 'voice channels found')

    if voice_channels:
        voice_channel = voice_channels[0]
        voice_client = await voice_channel.connect()
        stream = io.BytesIO(data)
        audio_source = MyAudio(stream)
        voice_client.play(audio_source)


with open('discordbot-config.json') as f:
    config = json.load(f)
TOKEN = config['token']
client.run(TOKEN)
