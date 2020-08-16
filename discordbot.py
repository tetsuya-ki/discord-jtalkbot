#!/usr/bin/env python

import json

import discord


client = discord.Client()


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


with open('discordbot-config.json') as f:
    config = json.load(f)
TOKEN = config['token']
client.run(TOKEN)
