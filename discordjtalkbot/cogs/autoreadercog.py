"""auto reader plugin """

import asyncio
import io
import logging
import re
import os
from os.path import join, dirname

import discord
from discord import member
from discord.ext import commands

from .modules import environ
from .modules import openjtalk

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
        self.vch = None
        LOG.info("_init_")

    # async def on_ready(self):
    #     LOG.info('We have logged in as {0}'.format(self.user))
    #     setup()

    # Botの準備完了時に呼び出されるイベント
    @commands.Cog.listener()
    async def on_ready(self):
        """called when the bot is ready """

        bot = self.bot
        appenv = environ.get_appenv()
        LOG.info('We have logged in as {0}'.format(bot.user))

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """Called when a `Message` is created and sent. """

        bot = self.bot
        LOG.info(f'nya-n43')
        if msg.author == bot.user:
            return

        # tch = msg.channel
        tch = self.vch
        if self.vch:
            vcl = discord.utils.get(
                bot.voice_clients, channel__guild=tch.guild, channel__name=tch.name)
            if vcl:
                # コマンドは無視
                if msg.clean_content.startswith(await self.bot.get_prefix(msg)):
                    return

                LOG.info(f'!!Reading {msg.author}\'s post on t:{tch.guild}/{tch}!!.')
                LOG.info(f'nya-n')
                message = re.sub('http(s)?://(\w+\.)+\w+(/[\w ./?%&=~-]*)?','URL省略', msg.clean_content)
                await self.talk(vcl, message)

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
            if member == vch.guild.owner and self.vch is None:
                LOG.info(f'Guild owner {member} connected v:{guild}/{vch}.')
                vcl = await vch.connect()
                self.vch = vch
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
            if member.id == vch.guild.owner_id:
                LOG.info(f'Guild owner {member} disconnected v:{guild}/{vch}.')
                vcl = discord.utils.get(bot.voice_clients, channel=vch)
                if vcl and vcl.is_connected():
                    await vcl.disconnect()
                    self.vch = None
                tch = discord.utils.get(guild.text_channels, name=vch.name)
                if tch:
                    await tch.send(appenv['text_end'])
            else:
                LOG.info(f'{member} disconnected v:{guild}/{vch}.')

                # 誰もいなくなったら切断する
                vcl = discord.utils.get(bot.voice_clients, channel=vch)
                if len(vch.members) == 1 and vcl and vcl.is_connected():
                    await vcl.disconnect()
                    self.vch = None

    async def talk(self, vcl: discord.VoiceClient, text: str):

        LOG.info(f'talk:{text}')

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

    async def cmd_connect(self, ctx: commands.Context):
        """connect to the voice channel the name of which is the same as
        the text channel (if not connected yet) """

        tch = ctx.channel
        vch = discord.utils.get(tch.guild.voice_channels, name=tch.name)
        if vch:
            await vch.connect()

    async def cmd_disconnect(self, ctx: commands.Context):
        """disconnect from the voice channel that the name of which is
        the same as the text channel (if already connected to) """

        tch = ctx.channel
        vcl = tch.guild.voice_client
        if vcl and vcl.channel.name == tch.name and vcl.is_connected():
            await vcl.disconnect()

    @commands.command(aliases=['c','con','conn','setsuzoku'])
    async def connect(self, ctx: commands.Context):
        guild = ctx.guild
        member = ctx.author
        voice_state = ctx.author.voice

        if voice_state is not None and self.vch is None:
            if voice_state.channel is not None:
                vch = voice_state.channel

                LOG.info(f'Executed command {member} connected v:{guild}/{vch}.')
                vcl = await vch.connect()
                self.vch = vch

    @commands.command(aliases=['d','dc','disco','setsudan'])
    async def disconnect(self, ctx: commands.Context):
        guild = ctx.guild
        member = ctx.author

        # voice_state = ctx.author.voice

        if self.vch is not None:
            LOG.info(f'Executed command {member} **disconnected** v:{guild}/{self.vch}.')
            vcl = self.vch.guild.voice_client
            if vcl and vcl.channel.name == self.vch.name and vcl.is_connected():
                await vcl.disconnect()
            self.vch = None
            LOG.info("set self.vch to None")

def setup(bot: commands.Bot):
    BOT_NAME = 'discordjtalkbot'
    LOG.setLevel(logging.INFO)

    appenv = environ.get_appenv()
    appenv.add_field('voice_hello')
    appenv.add_field('text_start',
                    help='text on start speaking  (%(default)s)')
    appenv.add_field('text_end',
                    help='text on stop speaking  (%(default)s)')
    appenv.add_field('cmd_connect', default='connect',
                    help='command to connect to the voice channel (%(default)s)')
    appenv.add_field('cmd_disconnect', default='disconnect',
                    help='command to disconnect from the voice channel (%(default)s)')
    # environment variables
    appenv.load_env(prefix=BOT_NAME)
    # setting file
    filename = BOT_NAME + '-config.json'
    file_path = join(dirname(__file__), 'modules' + os.sep +'files' + os.sep + filename)
    if os.path.exists(file_path):
        appenv.load_json(file_path)
    # command line args
    bot.add_cog(AutoReaderCog(bot))