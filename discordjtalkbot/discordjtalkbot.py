"""main entry point """

import logging
import os
import textwrap
from os.path import join, dirname, basename

from ctypes.util import find_library

import discord
from discord.ext import commands

from cogs.modules import environ

logging.basicConfig()
LOG = logging.getLogger(basename(__file__) + '$' + __name__)
INITIAL_EXTENSIONS = ['cogs.autoreadercog']

# カラー
HELP_COLOR_NORMAL = 0x0000bb
HELP_COLOR_WARN = 0xbb0000
class DiscordJTalkBot(commands.Bot):
    def __init__(self, command_prefix, help_command, intents):
        # スーパークラスのコンストラクタに値を渡して実行。
        super().__init__(command_prefix, case_insensitive = True, help_command=help_command, intents=intents)
        # INITIAL_EXTENSIONに格納されている名前からCogを読み込む。
        # エラーが発生した場合、エラー内容を表示する。
        for cog in INITIAL_EXTENSIONS:
            try:
                self.load_extension(cog)
            except Exception:
                LOG.warning("traceback:", stack_info=True)


# クラス定義。HelpCommandクラスを継承。
class Help(commands.HelpCommand):

    # AssistantBotのコンストラクタ。
    def __init__(self):
        # スーパークラスのコンストラクタに値を渡して実行。
        super().__init__()
        self.no_category = '__カテゴリ未設定__'
        self.command_attrs['description'] = 'コマンドリストを表示します。'
        # ここでメソッドのオーバーライドを行います。

    async def create_category_tree(self,category,enclosure):
            """
            コマンドの集まり（Group、Cog）から木の枝状のコマンドリスト文字列を生成する。
            生成した文字列は enlosure 引数に渡された文字列で囲われる。
            """
            content = ''
            command_list = category.walk_commands()
            for cmd in await self.filter_commands(command_list,sort=False):
                if cmd.root_parent:
                    # cmd.root_parent は「根」なので、根からの距離に応じてインデントを増やす
                    index = cmd.parents.index(cmd.root_parent)
                    indent = '\t' * (index + 1)
                    if indent:
                        content += f'`{indent}- {cmd.name}` → {cmd.description}\n'
                    else:
                        # インデントが入らない、つまり木の中で最も浅く表示されるのでprefixを付加
                        content += f'`{self.context.prefix}{cmd.name}` → {cmd.description}\n'
                else:
                    # 親を持たないコマンドなので、木の中で最も浅く表示する。prefixを付加
                    content += f'`{self.context.prefix}{cmd.name}` → {cmd.description}\n'

            if content == '':
                content = '＊中身なし＊'
            return enclosure + textwrap.dedent(content) + enclosure

    async def send_bot_help(self,mapping):
        embed = discord.Embed(title='**＊＊コマンドリスト＊＊**',color=HELP_COLOR_NORMAL)
        if self.context.bot.description:
            # もしBOTに description 属性が定義されているなら、それも埋め込みに追加する
            embed.description = self.context.bot.description
        for cog in mapping:
            if cog:
                cog_name = '__' + cog.qualified_name + '__'
            else:
                # mappingのキーはNoneになる可能性もある
                # もしキーがNoneなら、自身のno_category属性を参照する
                cog_name = self.no_category

            command_list = await self.filter_commands(mapping[cog],sort=True)
            content = ''
            for cmd in command_list:
                content += f'`{self.context.prefix}{cmd.name}`\n {cmd.description}\n'
            if content == '':
                content = '＊中身なし＊'
            embed.add_field(name=cog_name,value=content,inline=False)

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self,cog):
        embed = discord.Embed(title=cog.qualified_name,description=cog.description,color=HELP_COLOR_NORMAL)
        embed.add_field(name='コマンドリスト：',value=await self.create_category_tree(cog,''))
        await self.get_destination().send(embed=embed)

    async def send_group_help(self,group):
        embed = discord.Embed(title=f'{self.context.prefix}{group.qualified_name}',
            description=group.description,color=HELP_COLOR_NORMAL)
        if group.aliases:
            embed.add_field(name='有効なエイリアス：',value='`' + '`, `'.join(group.aliases) + '`',inline=False)
        if group.help:
            embed.add_field(name='ヘルプテキスト：',value=group.help,inline=False)
        embed.add_field(name='サブコマンドリスト：',value=await self.create_category_tree(group,''),inline=False)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self,command):
        params = ' '.join(command.clean_params.keys())
        if params != '':
            params = f'***{params}***'
        embed = discord.Embed(title=f'{self.context.prefix}{command.qualified_name} {params}',
            description=command.description,color=HELP_COLOR_NORMAL)
        if command.aliases:
            embed.add_field(name='有効なエイリアス：',value='`' + '`, `'.join(command.aliases) + '`',inline=False)
        if command.help:
            embed.add_field(name='ヘルプテキスト：',value=command.help,inline=False)
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        embed = discord.Embed(title='ヘルプ表示のエラー',description=error,color=HELP_COLOR_WARN)
        await self.get_destination().send(embed=embed)

    def command_not_found(self,string):
        return f'{string} というコマンドは存在しません。'

    def subcommand_not_found(self,command,string):
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            # もし、そのコマンドにサブコマンドが存在しているなら
            return f'{command.qualified_name} に {string} というサブコマンドは登録されていません。'
        return f'{command.qualified_name} にサブコマンドは登録されていません。'

if __name__ == "__main__":

        appenv = environ.get_appenv()
        appenv.add_field('prefix', default='$', help='command prefix (%(default)s)')
        appenv.add_field('token', help='bot token')
        appenv.add_field('voice_hello')
        appenv.add_field('open_jtalk_flags', default='-x /usr/local/opt/open-jtalk/dic -m /usr/local/opt/open-jtalk/voice/mei/mei_normal.htsvoice',
                        help='open jtalk settings  (%(default)s)')
        appenv.add_field('voices', default='/usr/local/opt/open-jtalk/voice/mei/mei_normal.htsvoice',
                        help='voices  (%(default)s)')
        appenv.add_field('except_prefix', default='$',
                        help='ignore prefix charactor  (%(default)s)')
        appenv.add_field('read_name', default='False',
                        help="read message author's name")
        appenv.add_field('read_system_message', default='False',
                        help="read system messsage")

        # environment variables
        BOT_NAME = 'discordjtalkbot'
        appenv.load_env(prefix=BOT_NAME)
        # setting file
        filename =  BOT_NAME + '-config.json'
        file_path = join(dirname(__file__), 'cogs' + os.sep + 'modules' + os.sep +'files' + os.sep + filename)
        if os.path.exists(file_path):
            appenv.load_json(file_path)

        LOG.setLevel(logging.INFO)

        # dcoker envrionment support
        env_list = []
        if os.getenv('IS_DOCKER'):
            LOG.info('docker mode.')
            if os.getenv('TOKEN'):
                env_list.extend(['--token', os.getenv('TOKEN')])
            if os.getenv('VOICE_HELLO'):
                env_list.extend(['--voice_hello', os.getenv('VOICE_HELLO')])
            if os.getenv('TEXT_START'):
                env_list.extend(['--text_start', os.getenv('TEXT_START')])
            if os.getenv('TEXT_END'):
                env_list.extend(['--text_end', os.getenv('TEXT_END')])
            if os.getenv('OPEN_JTALK_FLAGS'):
                env_list.extend(['--open_jtalk_flags', os.getenv('OPEN_JTALK_FLAGS')])
            if os.getenv('VOICES'):
                env_list.extend(['--voices', os.getenv('VOICES')])
            if os.getenv('EXCEPT_PREFIX'):
                env_list.extend(['--except_prefix', os.getenv('EXCEPT_PREFIX')])
            if os.getenv('READ_NAME'):
                env_list.extend(['--read_name', os.getenv('READ_NAME')])
            if os.getenv('READ_SYSTEM_MESSAGE'):
                env_list.extend(['--read_system_message', os.getenv('READ_SYSTEM_MESSAGE')])
            if env_list:
                LOG.info(env_list)
                appenv.load_args(env_list)

        discord.opus.load_opus(find_library('opus'))
        if discord.opus.is_loaded():
            LOG.info('Opus library is loaded.')

        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        intents.typing = False
        LOG.info(f'{__file__} is running.')
        token = appenv.get('token')

        bot = DiscordJTalkBot(
                command_prefix = appenv.get('prefix', '$')
                ,help_command=Help()
                ,intents=intents
            )# 大文字小文字は気にしない
        bot.run(token)