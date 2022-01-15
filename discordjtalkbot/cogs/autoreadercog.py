"""auto reader plugin """

import asyncio
import io
import logging
import re
import os
import random
from discord import player
import mojimoji
from os.path import join, dirname
from collections import deque

import discord
from discord import member
from discord.ext import commands

from .modules import environ
from .modules import openjtalk
from .modules.secret import secret_bou

logging.basicConfig()
LOG = logging.getLogger(__name__)


class AutoReaderCog(commands.Cog):
    BOT_NAME = 'ボット'

    def __init__(self, bot: commands.Bot):
        """constructor """

        self.bot = bot
        appenv = environ.get_appenv()
        flags = appenv.get('open_jtalk_flags', '')
        self.agent = openjtalk.Agent.from_flags(flags)
        self.agent.sampling = openjtalk.FREQ_48000HZ
        self.vch = None

        LOG.debug("voices:" + appenv.get('voices', ''))
        voices = str(appenv.get('voices', '')).split(',')
        self.voices = voices
        self.voices_init = voices
        self.voice_init = self.agent.voice
        self.member2voice = {}
        self.read_channel = None
        self.queue = deque()
        self.last_talked_member = ''
        self.talk_queue = deque()
        self.create_talk_task_id = 0
        self.play_talk_task_id = 0

        LOG.info("_init_")

    # Botの準備完了時に呼び出されるイベント
    @commands.Cog.listener()
    async def on_ready(self):
        """called when the bot is ready """

        bot = self.bot
        LOG.info('We have logged in as {0}'.format(bot.user))
        await self.main_task()

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
                    member_name = self.BOT_NAME
                else:
                    member_name = msg.author.display_name

                # いろいろ変換
                message = self._convert2hiragana(msg.clean_content)
                self.add_queue(vcl, member_name, message)

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
                    self.add_to_head_queue(vcl, '', appenv['voice_hello'])
                tch = discord.utils.get(guild.text_channels, name=vch.name)
                if tch:
                    await tch.send(appenv['text_start'])
            else:
                LOG.info(f'{member} connected v:{guild}/{vch}.')
                vcl = discord.utils.get(bot.voice_clients, channel=vch)

                # 設定ファイルで設定されていれば、入退室を読み上げる
                if appenv.get('read_system_message') == 'True':
                    if vcl:
                        self.add_to_head_queue(vcl, '', f'{member.display_name}さんが接続しました')

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
                        self.add_to_head_queue(vcl, '', f'{member.display_name}さんが切断しました')

                # 誰もいなくなったら切断する
                if len(vch.members) == 1 and vcl and vcl.is_connected():
                    await vcl.disconnect()
                    self.vch = None
                    tch = discord.utils.get(guild.text_channels, name=vch.name)
                    if tch:
                        await tch.send(appenv['text_end'])

    # async def new_talk(self, vcl: discord.VoiceClient, member_name:str, text: str):
    #     talk_data_list = await self.create_talk_data(member_name, text)
    #     await self.play_talk_data(vcl, talk_data_list)

    async def talk(self, vcl: discord.VoiceClient, member_name:str, text: str):
        # 設定ファイルで設定されていれば、名前を読み上げる
        appenv = environ.get_appenv()
        if appenv.get('read_name') == 'True' and self.last_talked_member != member_name and member_name != '':
            text = f'{member_name}さん、' + text
        self.last_talked_member = member_name

        # 半角英カナを全角へ変換
        text = mojimoji.han_to_zen(text, digit=True)
        texts = text.split('。。')
        data_list = []

        for phrase in texts:
            if len(phrase) == 0:
                continue
            if len(self.voices) == 0 or not member_name or member_name == self.BOT_NAME:
                LOG.debug('default voice.')
                self.agent.voice = self.voice_init
                data = await self.agent.async_talk(phrase)
            else:
                # メンバーにボイスを対応させる
                self._set_member2voice(member_name)
                self.agent.voice = self.member2voice[member_name]
                LOG.debug('member:' + member_name + ', voice:' + self.agent.voice)
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
            self.add_to_head_queue(vcl, '', '停止します')
            LOG.info("stop talking")

    @commands.command(aliases=['set','setChannel'],description='Botで読み上げるチャンネルを指定するコマンドです')
    async def setReadTextChannel(self, ctx: commands.Context, channel:str=None):
        """ Botで読み上げるチャンネルを指定するコマンドです """
        if self.vch is None or not channel:
            return
        vcl = self.vch.guild.voice_client
        # チャンネルの設定
        temp_channel = discord.utils.get(ctx.guild.text_channels, name=channel)
        if temp_channel is None:
            temp_channel_id = re.sub(r'[<#>]', '', channel)
            if temp_channel_id.isdecimal() and '#' in channel:
                channel_id = int(temp_channel_id)
                self.read_channel = ctx.guild.get_channel(channel_id).name
            else:
                if vcl:
                    self.add_to_head_queue(vcl, '', '無効なチャンネルです。')
        else:
            self.read_channel = channel

        LOG.info(f"set 「{self.read_channel}」 for read channel")
        if vcl:
            self.add_to_head_queue(vcl, '', self.read_channel + 'のみ読み上げるように変更しました')

    @commands.command(aliases=['reset','resetChannel'],description='Botで読み上げるチャンネルを解除するコマンドです')
    async def resetReadTextChannel(self, ctx: commands.Context):
        """ Botで読み上げるチャンネルを解除するコマンドです """
        self.read_channel = None
        vcl = self.vch.guild.voice_client
        LOG.info(f"reset read channel")
        if vcl:
            self.add_to_head_queue(vcl, '', '読み上げチャンネル指定を解除')

    def _set_member2voice(self, member_name):
        # すでに登録されているか確認
        if member_name in self.member2voice:
            return

        # voicesがあるならシャッフルしておき、ないなら初期のものを持ってくる
        if self.voices:
            random.shuffle(self.voices)
        else:
            self.voices = random.shuffle(self.voices_init)

        voice = self.voices.pop()
        self.member2voice[member_name]=voice
        LOG.info(f'set voice({voice}) to member({member_name}).')

    def _convert2hiragana(self, text):
        sys_dict = {
                r'http(s)?://[\w.,~:#%-]+\w+(/[\w .,/?%&=~:#-$]*)?' : 'URL省略' # URL省略
                , r'[|]+.+?[|]+' : 'ネタバレ' # ネタバレ削除
                , r'<:\w+:\d+>' : '絵文字' # 絵文字無視
                , '\n' : '。。' # 改行対策
                , r'[`]+.+?[`]+' : '' # ソース削除
                , r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})' : r'\1ねん、\2がつ、\3にち。' # 日付
                , r'(\d{1,2})[-/](\d{1,2})' : r'\1がつ、\2にち。' # 日付2
                , r'(\d{1,2}):(\d{1,2}):(\d{1,2})(\.\d{3})?' : r'\1じ、\2ふん。' # 時間(秒は省略)
                , r'(\d{1,2}):(\d{1,2})' : r'\1じ、\2ふん。' # 時間2
                , r',' : '' # カンマ無視
                , r'(\d)(\d{12,20})' : '大きい数字' # 数字(大きい)
                , r'(\d{1,4})(\d{8})' : r'\1おく\2' # 1億
                , r'(\d{1,4})(\d{4})' : r'\1まん\2' # 1万
                , '(\d)(\d{3})' : r'\1せん\2' # 千
                , r'(\d)(\d{2})' : r'\1ひゃく\2' # 百
                , r'(\d)(\d{1})' : r'\1じゅう\2' # 十
                , r'じゅう0' : r'じゅう'
                , r'0(おく|まん|せん|ひゃく|じゅう)' : '' # ゼロは読まない
                , r'1(せん)' : r'イッ\1'
                , r'8(せん)' : r'ハッ\1'
                , r'1(ひゃく|じゅう)' : r'\1'
                , r'8(ひゃく)' : r'はっぴゃく\1'
                , r'6(ひゃく)' : r'ろっぴゃく\1'
                , r'3(ひゃく)' : r'さんびゃく'
                , r'0' : 'ゼロ'
                , r'1' : 'イチ'
                , r'2' : 'ニイ'
                , r'3' : 'サン'
                , r'4' : 'ヨン'
                , r'5' : 'ゴ'
                , r'6' : 'ロク'
                , r'7' : 'ナナ'
                , r'8' : 'ハチ'
                , r'9' : 'キュウ'
        }
        user_dict = {
                '(Mon)' : 'マン'
                , '(Tue)' : 'タァズ'
                , '(Wed)' : 'ウェンズ'
                , '(Thu)' : 'サーズ'
                , '(Fri)' : 'フライ'
                , '(Sat)' : 'サタ'
                , '(Sun)' : 'サン'
                , 'Date:' : 'デイト '
                , 'Tuber' : 'チューバー'
        }

        read_list = [] # 読み仮名リスト
        for i, one_dic in enumerate(user_dict.items()): # one_dicは単語と読みのタプル。添字はそれぞれ0と1。
            text = re.sub(one_dic[0], '{'+str(i)+'}', text)
            read_list.append(one_dic[1]) # 変換が発生した順に読み仮名リストに追加
        read_text = text.format(*read_list) #読み仮名リストを引数にとる

        # その他の読みかえ(正規表現あり)
        for word, read in sys_dict.items():
            read_text = re.sub(word, read, read_text)

        return read_text

    async def main_task(self):
        while True:
            await asyncio.sleep(0.01)
            await self.talk_task()

    async def talk_task(self):
        talking_task = asyncio.create_task(self.talking_task())
        playing_talk_task = asyncio.create_task(self.play_talk_data()) 
        await talking_task, playing_talk_task

    def add_queue(self, vcl, name, message):
        self.queue.append([vcl, name, message, False])

    def add_to_head_queue(self, vcl, name, message):
        self.queue.appendleft([vcl, name, message, True])

    def pop_queue(self):
        return self.queue.popleft()

    async def talking_task(self):
        if len(self.queue) == 0:
            return
        while len(self.queue) > 0:
            vcl, name, message, primary = self.pop_queue()
            # await self.talk(vcl, name, message)
            await self.create_talk_data(name, message, vcl, primary)
            self.create_talk_task_id += 1
        return

    async def create_talk_data(self, member_name:str, text: str, vcl: discord.VoiceClient, is_parimary:bool):
        # 設定ファイルで設定されていれば、名前を読み上げる
        appenv = environ.get_appenv()
        if appenv.get('read_name') == 'True' and self.last_talked_member != member_name and member_name != '':
            text = f'{member_name}さん、' + text
        self.last_talked_member = member_name

        # 半角英カナを全角へ変換
        text = mojimoji.han_to_zen(text, digit=True)
        texts = text.split('。。')
        audio_data_list = []

        if len(self.voices) == 0 or not member_name or member_name == self.BOT_NAME:
            LOG.debug('default voice.')
            voice = self.voice_init
        else:
            # メンバーにボイスを対応させる
            self._set_member2voice(member_name)
            voice = self.member2voice[member_name]
            LOG.debug('member:' + member_name + ', voice:' + voice)
        voice_name = re.sub('.+/', '', voice)

        task_id = self.play_talk_task_id if is_parimary else self.create_talk_task_id
        for i in range(0, len(texts)):
            if len(texts[i]) == 0:
                continue

            create_talk_task = asyncio.create_task(self.async_create_talk_data(i, texts[i], voice))
            index,stream,audio = await create_talk_task
            LOG.info(f'talk({voice_name}):{texts[i]}')

            # 優先するものなら、タスクを繰り上げる
            audio_data_list.append([index, audio, stream, vcl, texts[i], task_id])
        # 並び替え
        datas = sorted(audio_data_list)
        # 先頭のインデックスを削る
        data_list = [row[1:] for row in datas]
        self.talk_queue.append(data_list)
        LOG.info(f'{task_id})create talk:{text}')

    async def play_talk_data(self):
        if len(self.talk_queue) == 0:
            return
        while len(self.talk_queue) > 0:
            talk_data_list = self.talk_queue.popleft()
            if len(self.talk_queue) > 0:
                talk_data_list_next = self.talk_queue.popleft()
                talk_data_list_next_id = talk_data_list_next[0][4]
            else:
                talk_data_list_next_id = 0
            if len(self.talk_queue) > 0:
                talk_data_list_third = self.talk_queue.popleft()
                talk_data_list_third_id = talk_data_list_next[0][4]
            else:
                talk_data_list_third_id = 0

            # 再生中や次のデータまで来てしまった場合は、無視
            ##or talk_data_list[0][4] >= self.create_talk_task_id
            LOG.info(f'len:{len(talk_data_list)} / atai_{talk_data_list[0]}')
            if talk_data_list[0][2].is_playing():
                if talk_data_list_third_id != 0:
                    self.talk_queue.appendleft(talk_data_list_third)
                if talk_data_list_next_id != 0:
                    self.talk_queue.appendleft(talk_data_list_next)
                self.talk_queue.appendleft(talk_data_list)
                return
            if (talk_data_list[0][4] > talk_data_list_next_id and talk_data_list_next_id != 0) \
                or (talk_data_list[0][4] > talk_data_list_third_id and talk_data_list_third_id != 0):
                if talk_data_list_third_id != 0:
                    if talk_data_list_third_id < talk_data_list_next_id < talk_data_list[0][4]:
                        self.talk_queue.appendleft(talk_data_list)
                        self.talk_queue.appendleft(talk_data_list_next)
                        self.talk_queue.appendleft(talk_data_list_third)
                    elif talk_data_list_next_id < talk_data_list_third_id < talk_data_list[0][4]:
                        self.talk_queue.appendleft(talk_data_list)
                        self.talk_queue.appendleft(talk_data_list_third)
                        self.talk_queue.appendleft(talk_data_list_next)
                    elif talk_data_list_third_id < talk_data_list[0][4] < talk_data_list_next_id:
                        self.talk_queue.appendleft(talk_data_list_next)
                        self.talk_queue.appendleft(talk_data_list)
                        self.talk_queue.appendleft(talk_data_list_third)
                    elif talk_data_list[0][4] < talk_data_list_third_id < talk_data_list_next_id:
                        self.talk_queue.appendleft(talk_data_list_next)
                        self.talk_queue.appendleft(talk_data_list_third)
                        self.talk_queue.appendleft(talk_data_list)
                    elif talk_data_list_next_id < talk_data_list[0][4] < talk_data_list_third_id:
                        self.talk_queue.appendleft(talk_data_list_third)
                        self.talk_queue.appendleft(talk_data_list)
                        self.talk_queue.appendleft(talk_data_list_next)
                    else:
                        self.talk_queue.appendleft(talk_data_list_third)
                        self.talk_queue.appendleft(talk_data_list_next)
                        self.talk_queue.appendleft(talk_data_list)
                elif talk_data_list_next_id != 0:
                    if talk_data_list_next_id < talk_data_list[0][4]:
                        self.talk_queue.appendleft(talk_data_list)
                        self.talk_queue.appendleft(talk_data_list_next)
                    else:
                        self.talk_queue.appendleft(talk_data_list_next)
                        self.talk_queue.appendleft(talk_data_list)
                self.talk_queue.appendleft(talk_data_list)
                LOG.info(f'talk_data_{talk_data_list[0][4]}/next_{talk_data_list_next_id}/th_{talk_data_list_third_id}/self_talk_data_{self.create_talk_task_id})play talk:{talk_data_list[0][3]}')
                LOG.info(f'talk_data_list[0][2].is_playing(){talk_data_list[0][2].is_playing()}/talk_data_list[0][4] > talk_data_list_next_id{talk_data_list[0][4] > talk_data_list_next_id}talk_data_list[0][4] > talk_data_list_third_id/{talk_data_list[0][4] > talk_data_list_third_id}')
                return
            else:
                self.play_talk_task_id += 1

            for talk_data in talk_data_list:
                LOG.info(f'{self.play_talk_task_id}/talk_data_{talk_data[4]}/self_talk_data_{self.create_talk_task_id})play talk:{talk_data[3]}')
                LOG.info(talk_data)
                sleeptime = 0.5
                timeout = 3.0
                for _ in range(int(timeout / sleeptime)):
                    if talk_data[2].is_connected():
                        break
                    await asyncio.sleep(sleeptime)
                else:
                    return
                try:
                    LOG.info('reading' + talk_data[3])
                    talk_data[2].play(talk_data[0], after=lambda e: talk_data[1].close())
                except Exception as e:
                    LOG.info(str(e))

                while talk_data[2].is_playing():
                    await asyncio.sleep(sleeptime)

    async def async_create_talk_data(self, number:int, text:str, voice:str):
        self.agent.voice = voice
        if 'phont/' in voice:
            data = secret_bou.talk(text, file_phont=self.agent.voice)
            stream = io.BytesIO(data)
            audio = discord.PCMAudio(stream)
        else:
            data = await self.agent.async_talk(text)
            stream = io.BytesIO(data)
            audio = discord.PCMAudio(stream)
        return number,stream,audio

def setup(bot: commands.Bot):
    BOT_NAME = 'discordjtalkbot'
    LOG.setLevel(logging.INFO)
    appenv = environ.get_appenv()
    appenv.load_env(prefix=BOT_NAME)
    bot.add_cog(AutoReaderCog(bot))