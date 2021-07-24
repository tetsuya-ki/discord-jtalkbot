"""auto reader plugin """

import asyncio
import io
import logging
import re
import os
import random
import mojimoji
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

        self.member_name = ''
        LOG.debug("voices:" + appenv.get('voices', ''))
        voices = str(appenv.get('voices', '')).split(',')
        self.voices = voices
        self.voices_init = voices
        self.voice_init = self.agent.voice
        self.member2voice = {}
        self.read_channel = None
        LOG.info("_init_")

    # Botの準備完了時に呼び出されるイベント
    @commands.Cog.listener()
    async def on_ready(self):
        """called when the bot is ready """

        bot = self.bot
        LOG.info('We have logged in as {0}'.format(bot.user))

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """Called when a `Message` is created and sent. """

        bot = self.bot
        if msg.author == bot.user:
            return

        tch = self.vch
        if self.vch:
            vcl = discord.utils.get(
                bot.voice_clients, channel__guild=tch.guild, channel__name=tch.name)
            if vcl:
                # 何もなかったら無視
                if len(msg.clean_content) == 0:
                    return
                # コマンドは無視
                if msg.clean_content.startswith(await self.bot.get_prefix(msg)):
                    return

                appenv = environ.get_appenv()
                command = str(appenv.get('except_prefix', '')).split(',')
                for ignore_command in command:
                    if msg.clean_content.startswith(ignore_command):
                        return

                # 設定ファイルで設定されていれば、他のギルドも読み上げる
                if not appenv.get('read_all_guild') == 'True':
                    # 接続しているギルド以外は無視
                    if msg.guild != tch.guild:
                        return

                # 読み上げチャンネルが指定されている場合、そのチャンネルのみを読み上げる
                if self.read_channel is not None and self.read_channel != msg.channel.name:
                    return
                LOG.info(f'!!Reading {msg.author}\'s post on t:{tch.guild}/{tch}!!.')
                if msg.author.bot:
                    self.member_name = 'ボット'
                else:
                    self.member_name = msg.author.display_name

                # URL省略
                message = re.sub('http(s)?://[\w.,~:#%-]+\w+(/[\w .,/?%&=~:#-]*)?','URL省略', msg.clean_content)
                # ネタバレ削除
                message = re.sub(r'[|]+.+?[|]+', 'ネタバレ', message)
                # 絵文字無視
                message = re.sub(r'<:\w+:\d+>', '絵文字', message)
                # 改行対策
                message = re.sub('\n', '。。', message)
                # ソース削除
                message = re.sub(r'[`]+.+?[`]+', '', message)
                # いろいろ変換
                message = self._suuji2hiragana(message)

                # 設定ファイルで設定されていれば、名前を読み上げる
                if appenv.get('read_name') == 'True':
                    message = f'{self.member_name}さん、' + message

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

            if member == vch.guild.owner and self.vch is None and appenv.get('owner_connect') == 'True':
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
                vcl = discord.utils.get(bot.voice_clients, channel=vch)

                # 設定ファイルで設定されていれば、入退室を読み上げる
                if appenv.get('read_system_message') == 'True':
                    if vcl:
                        await self.talk(vcl, f'{member.display_name}さんが接続しました')

        elif before.channel and not after.channel:
            # someone disconnected the voice channel.
            vch = before.channel
            guild = vch.guild
            vcl = discord.utils.get(bot.voice_clients, channel=vch)
            if member.id == vch.guild.owner_id and len(vch.members) != 1:
                LOG.info(f'Guild owner {member} disconnected v:{guild}/{vch}.')
                LOG.info(f'{str(len(vch.members))} 人になりました')
                vcl = discord.utils.get(bot.voice_clients, channel=vch)
                if vcl and vcl.is_connected() and appenv.get('owner_disconnect') == 'True':
                    await vcl.disconnect()
                    self.vch = None
                tch = discord.utils.get(guild.text_channels, name=vch.name)
                if tch:
                    await tch.send(appenv['text_end'])
            else:
                LOG.info(f'{member} disconnected v:{guild}/{vch}.')
                LOG.info(f'{str(len(vch.members))} 人になりました')
                
                vcl = discord.utils.get(bot.voice_clients, channel=vch)

                # 設定ファイルで設定されていれば、入退室を読み上げる
                if appenv.get('read_system_message') == 'True':
                    if vcl:
                        await self.talk(vcl, f'{member.display_name}さんが切断しました')

                # 誰もいなくなったら切断する
                if len(vch.members) == 1 and vcl and vcl.is_connected():
                    await vcl.disconnect()
                    self.vch = None
                    tch = discord.utils.get(guild.text_channels, name=vch.name)
                    if tch:
                        await tch.send(appenv['text_end'])

    async def talk(self, vcl: discord.VoiceClient, text: str):
        # 半角英カナを全角へ変換
        text = mojimoji.han_to_zen(text, digit=True)
        texts = text.split('。。')

        for phrase in texts:
            if len(phrase) == 0:
                continue
            if len(self.voices) == 0 or not self.member_name:
                LOG.debug('default voice.')
                self.agent.voice = self.voice_init
                data = await self.agent.async_talk(phrase)
            else:
                # メンバーにボイスを対応させる
                self._set_member2voice()
                self.agent.voice = self.member2voice[self.member_name]
                LOG.debug('member:' + self.member_name + ', voice:' + self.agent.voice)
                data = await self.agent.async_talk(phrase)

            voice_name = re.sub('.+/', '', self.agent.voice)
            LOG.info(f'talk({voice_name}):{phrase}')
            stream = io.BytesIO(data)
            audio = discord.PCMAudio(stream)
            sleeptime = 0.1
            timeout = 3.0
            for _ in range(int(timeout / sleeptime)):
                if vcl.is_connected():
                    break
                await asyncio.sleep(sleeptime)
            else:
                return# return
            vcl.play(audio, after=lambda e: stream.close())
            while vcl.is_playing():
                await asyncio.sleep(sleeptime)
        else:
            self.member_name = ''

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

    @commands.command(aliases=['c','con','conn','setsuzoku'],description='コマンド実行者の接続しているボイスチャンネルに、Botを接続するコマンドです')
    async def connect(self, ctx: commands.Context):
        """ コマンド実行者の接続しているボイスチャンネルに、Botを接続するコマンドです """
        guild = ctx.guild
        member = ctx.author
        voice_state = ctx.author.voice

        if voice_state is not None and self.vch is None:
            if voice_state.channel is not None:
                vch = voice_state.channel

                LOG.info(f'Executed command {member} connected v:{guild}/{vch}.')
                vcl = await vch.connect()
                self.vch = vch

    @commands.command(aliases=['d','dc','disco','setsudan'],description='ボイスチャンネルからBotを切断するコマンドです')
    async def disconnect(self, ctx: commands.Context):
        """ ボイスチャンネルからBotを切断するコマンドです """
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

    @commands.command(aliases=['s','tomeru'],description='Botの発言を止めさせるコマンドです')
    async def stop(self, ctx: commands.Context):
        """ Botの発言を止めさせるコマンドです """
        vcl = self.vch.guild.voice_client

        # 再生を停止
        if vcl and vcl.is_playing():
            vcl.stop()
            await self.talk(vcl, '停止')
            LOG.info("stop talking")

    @commands.command(aliases=['set','setChannel'],description='Botで読み上げるチャンネルを指定するコマンドです')
    async def setReadTextChannel(self, ctx: commands.Context, channel:str):
        """ Botで読み上げるチャンネルを指定するコマンドです """
        vcl = self.vch.guild.voice_client
        if not channel:
            return
        
        # チャンネルの設定
        temp_channel = discord.utils.get(ctx.guild.text_channels, name=channel)
        if temp_channel is None:
            temp_channel_id = re.sub(r'[<#>]', '', channel)
            if temp_channel_id.isdecimal() and '#' in channel:
                channel_id = int(temp_channel_id)
                self.read_channel = ctx.guild.get_channel(channel_id).name
            else:
                if vcl:
                    await self.talk(vcl, '無効なチャンネルです。')
        else:
            self.read_channel = channel

        LOG.info(f"set 「{self.read_channel}」 for read channel")
        if vcl:
            await self.talk(vcl, self.read_channel + 'のみ読み上げるように変更しました')

    @commands.command(aliases=['reset','resetChannel'],description='Botで読み上げるチャンネルを解除するコマンドです')
    async def resetReadTextChannel(self, ctx: commands.Context):
        """ Botで読み上げるチャンネルを解除するコマンドです """
        self.read_channel = None
        vcl = self.vch.guild.voice_client
        LOG.info(f"reset read channel")
        if vcl:
            await self.talk(vcl, '読み上げチャンネル指定を解除')

    def _set_member2voice(self):
        # すでに登録されているか確認
        if self.member_name in self.member2voice:
            return

        # voicesがあるならシャッフルしておき、ないなら初期のものを持ってくる
        if self.voices:
            random.shuffle(self.voices)
        else:
            self.voices = random.shuffle(self.voices_init)

        voice = self.voices.pop()
        name = self.member_name
        self.member2voice[name]=voice
        LOG.info(f'set voice({voice}) to member({name}).')

    def _suuji2hiragana(self, text):
        converted_text = ''
        # 日付
        r_date = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        rep_r_date = r'\1ねん、\2がつ、\3にち。'
        r_date2 = r'(\d{1,2})[-/](\d{1,2})'
        rep_r_date2 = r'\1がつ、\2にち。'
        converted_text = re.sub(r_date, rep_r_date, text)
        converted_text = re.sub(r_date2, rep_r_date2, converted_text)

        # 時間
        r_time = r'(\d{1,2}):(\d{1,2}):(\d{1,2})(\.\d{3})?'
        rep_r_time = r'\1じ、\2ふん、\3びょう。'
        r_time2 = r'(\d{1,2}):(\d{1,2})'
        rep_r_time2 = r'\1じ、\2ふん。'
        converted_text = re.sub(r_time, rep_r_time, converted_text)
        converted_text = re.sub(r_time2, rep_r_time2, converted_text)

        # 数字
        str1 = r'(\d)(\d{12,20})'
        rep_str1 = '大きい数字'
        converted_text = re.sub(str1, rep_str1, converted_text) # １兆以上は読まない
        converted_text = re.sub(r'(\d{1,4})(\d{8})', r'\1おく\2', converted_text) # 1億
        LOG.info(converted_text)
        converted_text = re.sub(r'(\d{1,4})(\d{4})', r'\1まん\2', converted_text) # 1万
        LOG.info(converted_text)
        converted_text = re.sub(r'(\d)(\d{3})', r'\1せん\2', converted_text)
        LOG.info(converted_text)
        converted_text = re.sub(r'(\d)(\d{2})', r'\1ひゃく\2', converted_text)
        LOG.info(converted_text)
        converted_text = re.sub(r'(\d)(\d{1})', r'\1じゅう\2', converted_text)
        LOG.info(converted_text)
        converted_text = re.sub(r'1(せん)', r'イッ\1', converted_text)
        converted_text = re.sub(r'1(ひゃく|じゅう)', r'\1', converted_text)
        LOG.info(converted_text)
        converted_text = re.sub(r'1', 'イチ', converted_text)
        converted_text = re.sub(r'2', 'ニイ', converted_text)
        converted_text = re.sub(r'3', 'サン', converted_text)
        converted_text = re.sub(r'4', 'ヨン', converted_text)
        converted_text = re.sub(r'5', 'ゴ', converted_text)
        converted_text = re.sub(r'6', 'ロク', converted_text)
        converted_text = re.sub(r'7', 'ナナ', converted_text)
        converted_text = re.sub(r'8', 'ハチ', converted_text)
        converted_text = re.sub(r'9', 'キュウ', converted_text)
        converted_text = re.sub(r'0(おく|まん|せん|ひゃく|じゅう)', '', converted_text) # ゼロは読まない
        
        LOG.info(converted_text)
        return converted_text

def setup(bot: commands.Bot):
    BOT_NAME = 'discordjtalkbot'
    LOG.setLevel(logging.INFO)
    appenv = environ.get_appenv()
    appenv.load_env(prefix=BOT_NAME)
    bot.add_cog(AutoReaderCog(bot))