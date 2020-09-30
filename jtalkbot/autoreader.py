"""auto reader plugin """

import asyncio
import io
import logging

import discord
from discord.ext import commands

from . import environ
from . import openjtalk


logging.basicConfig()
LOG = logging.getLogger(__name__)


class AutoReaderCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        """constructor """

        self.bot = bot
        appenv = environ.get_appenv()
        flags = appenv.get('open_jtalk_flags', '')
        self.agent = openjtalk.Agent.from_flags(flags)
        self.agent.sampling = openjtalk.FREQ_48000HZ

    @commands.Cog.listener()
    async def on_ready(self):
        """called when the bot is ready """

        bot = self.bot
        appenv = environ.get_appenv()

        # register commands
        bot.add_command(commands.Command(
            self.connect_vch, name=appenv['cmd_connect_vch']))
        bot.add_command(commands.Command(
            self.disconnect_vch, name=appenv['cmd_disconnect_vch']))

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """Called when a `Message` is created and sent. """

        bot = self.bot
        if msg.author == bot.user:
            return

        tch = msg.channel
        vcl = discord.utils.get(
            bot.voice_clients, channel__guild=tch.guild, channel__name=tch.name)
        if vcl:
            LOG.info(f'Reading {msg.author}\'s post on t:{tch.guild}/{tch}.')
            await self.talk(vcl, msg.content)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState):
        """Called when a `Member` changes their `VoiceState`. """

        bot = self.bot
        appenv = environ.get_appenv()

        if not before.channel and after.channel:
            # someone connected the voice channel.
            vch = after.channel
            guild = vch.guild
            if member == vch.guild.owner:
                LOG.info(f'Guild owner {member} connected v:{guild}/{vch}.')
                vcl = await vch.connect()
            elif member == bot.user:
                LOG.info(f'{member} connected v:{guild}/{vch}.')
                vcl = discord.utils.get(bot.voice_clients, channel=vch)
                if vcl:
                    await self.talk(vcl, appenv['voice_hello'])
                tch = discord.utils.get(guild.text_channels, name=vch.name)
                if tch:
                    await tch.send(appenv['text_start'])
            else:
                LOG.info(f'{member} connected v:{guild}/{vch}.')


        elif before.channel and not after.channel:
            # someone disconnected the voice channel.
            vch = before.channel
            guild = vch.guild
            if member == vch.guild.owner:
                LOG.info(f'Guild owner {member} disconnected v:{guild}/{vch}.')
                vcl = discord.utils.get(bot.voice_clients, channel=vch)
                if vcl and vcl.is_connected():
                    await vcl.disconnect()
                tch = discord.utils.get(guild.text_channels, name=vch.name)
                if tch:
                    await tch.send(appenv['text_end'])
            else:
                LOG.info(f'{member} disconnected v:{guild}/{vch}.')

    async def talk(self, vcl: discord.VoiceClient, text: str):

        data = await self.agent.async_talk(text)
        stream = io.BytesIO(data)
        audio = discord.PCMAudio(stream)
        sleeptime = 0.1
        timeout = 6.0
        for _ in range(int(timeout / sleeptime)):
            if vcl.is_connected():
                break
            await asyncio.sleep(sleeptime)
        else:
            return
        while vcl.is_playing():
            await asyncio.sleep(0.1)
        vcl.play(audio, after=lambda e: stream.close())

    async def connect_vch(self, ctx: commands.Context):
        """connect to the voice channel the name of which is the same as
        the text channel (if not connected yet) """

        tch = ctx.channel
        vch = discord.utils.get(tch.guild.voice_channels, name=tch.name)
        if vch:
            await vch.connect()

    async def disconnect_vch(self, ctx: commands.Context):
        """disconnect from the voice channel that the name of which is
        the same as the text channel (if already connected to) """

        tch = ctx.channel
        vcl = tch.guild.voice_client
        if vcl and vcl.channel.name == tch.name and vcl.is_connected():
            await vcl.disconnect()


def setup(bot: commands.Bot):
    LOG.setLevel(logging.INFO)

    appenv = environ.get_appenv()
    appenv.add_field('voice_hello')
    appenv.add_field('text_start')
    appenv.add_field('text_end')
    appenv.add_field('cmd_connect_vch', default='connect')
    appenv.add_field('cmd_disconnect_vch', default='disconnect')

    bot.add_cog(AutoReaderCog(bot))
