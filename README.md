# discord-jtalkbot

## A Discord bot talking Japanese

Discordのテキストチャンネルに投稿されたメッセージをボイスチャンネルで読み上げるBotです。  
＊このプログラムは[Masaaki Shibata](https://bitbucket.org/emptypage/)さまの[jtalkbot](https://bitbucket.org/emptypage/jtalkbot/src/master/)を改造したものです(discordが前についていますが、修正前プログラムもDiscordで動作します)  
ref. <https://bitbucket.org/emptypage/jtalkbot/src/master/>
> Copyright © 2020 Masaaki Shibata

＊上記は、修正前のプログラムのLICENSEから抜粋したもの

このBotは、読み上げBotを見知らぬ人のサーバーで実行することに不安を覚える人が自分のマシンで読み上げさせることが可能です。低機能ですが、そのあたりが嬉しいかもしれません。

## Table of Contesnts

1. [A Discord bot talking Japanese](#A-Discord-bot-talking-Japanese)

2. [動作環境](#動作環境)

3. [導入](#導入)

4. [使いかた](#使いかた)

5. [Botの実行](#Botの実行)

6. [Botの動作](#Botの動作)

7. [open-jtalk辞書の更新](#open-jtalk辞書の更新)

8. [FAQ](#FAQ)

## 動作環境

以下のプログラム／ライブラリが正常に動作しているシステムが必要ですが、Repl.itでは自動で設定されるようにシェルを作りましたので、準備は不要のはずです。

- [Python 3.8](https://www.python.org "Welcome to Python.org")
- [Open JTalk](http://open-jtalk.sourceforge.net "Open JTalk")（`open_jtalk` コマンド）
- [Opus ライブラリ](https://opus-codec.org "Opus Codec")（[discord.py](https://pypi.org/project/discord.py/ "discord.py · PyPI") の音声機能に必要）

## 導入

下記URLで**FORK**を押します。
https://Repl.it/@tetsuyaki/discord-jtalkbot

ログインし、Repl.itでこのプロジェクトを開ける状態にします。

## 使いかた

### .envファイルの準備

Repl.itの場合は、`.env`ファイルに**Botアカウントのトークンを記述**してください(.env以外は公開されてしまうため！)  
README.mdと同階層に`.env.sample`がありますので、これをコピーし、`.env`に名前を変更した上で、Botアカウントのトークンを記述してください。
(discordjtalkbot-config.jsonにトークンを記述しては**いけません**)

### 設定ファイルの準備

続いて `discordjtalkbot-config.json` ファイルを編集します。  
ライブラリ内にサンプルファイルが `discordjtalkbot-config.sample.json` として入っていますので、これをコピー、リネームして使ってください。

#### `discordjtalkbot-config.json` ファイルの例

  ```JSON
  {
    "token": "__DON'T_USE_THIS!__",
    "open_jtalk_flags": "-x /usr/local/opt/open-jtalk/dic -m /usr/local/opt/open-jtalk/voice/mei/mei_normal.htsvoice",
    "voice_hello": "みなさんこんにちは。",
    "text_start": "読み上げを始めます。",
    "text_end": "読み上げを終わります。",
    "voices": "/usr/local/opt/open-jtalk/voice/m100/nitech_jp_atr503_m001.htsvoice,/usr/local/opt/open-jtalk/voice/mei/mei_angry.htsvoice,/usr/local/opt/open-jtalk/voice/mei/mei_bashful.htsvoice,/usr/local/opt/open-jtalk/voice/mei/mei_happy.htsvoice,/usr/local/opt/open-jtalk/voice/mei/mei_normal.htsvoice,/usr/local/opt/open-jtalk/voice/mei/mei_sad.htsvoice",
    "except_prefix": "!,$,/",
    "read_name": "True",
    "read_system_message": "True",
    "read_all_guild": "False"
  }
  ```

#### `token`

Repl.itで使用する場合は、絶対にBotアカウントのトークンを記述しないでください！（ココに記載すると、全世界に公開されます！）

#### `open_jtalk_flags`

文字列型。`open_jtalk` コマンドに渡すコマンドラインオブションを記述します。読み上げに使用されます(dicを変更したり、読み上げるボイスを指定できます)。

#### `voice_hello`

文字列型。BotがDiscordの音声チャンネルへ接続したときに、「最初に発声するあいさつ」を記述します。

#### `text_start`

文字列型。Botがテキストチャンネルの投稿の読み上げを開始するときに、そのテキストチャンネルに投稿するメッセージを記述します。

#### `text_end`

文字列型。Botがテキストチャンネルの投稿の読み上げを停止するときに、そのテキストチャンネルに投稿するメッセージを記述します(2021/01/10現在、なんか動きません)。

#### `voices`

文字列型。人に適当にvoiceを割り当てます（カンマ区切りで指定）。voiceが足りなくなった場合、重複します。

##### `except_prefix`

文字列型。指定したプレフィックスが先頭にあるメッセージは読み上げしないようになります(カンマ区切りで指定)。ギルドで使用しているBotのプレフィックスを指定すると良いと思います。

##### `read_name`

文字列型。名前を読み上げるかどうか。設定がない場合は読み上げない("True"の時のみ読み上げる)

##### `read_system_message`

文字列型。メンバーのボイスチャンネルへの入退室を読み上げるかどうか。設定がない場合は読み上げない("True"の時のみ読み上げる)

#### `read_all_guild`

文字列型。すべてのギルドのメッセージを読み上げるかどうか。設定がない場合はボイスチャンネルに接続したギルドのみ読み上げる
### Botの実行

Repl.itの場合は、上にある「RUN」ボタンをクリックしてください。

起動するとログを表示しながら待機し続けます。

```sh
open_jtalkはインストール済
ダウンロード済
Installing dependencies from lock file

No dependencies to install or update

INFO:discordjtalkbot.py$__main__:Opus library is loaded.
INFO:discordjtalkbot.py$__main__:discordjtalkbot/discordjtalkbot.py is running.
 * Serving Flask app "" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
INFO:werkzeug: * Running on http://0.0.0.0:xxxxx/ (Press CTRL+C to quit)
INFO:cogs.autoreadercog:_init_
INFO:werkzeug:XXXXXX - - [13/Feb/2021 11:41:30] "GET / HTTP/1.1" 200 -
INFO:cogs.autoreadercog:We have logged in as MyBot#nnnn.
```

Botを停止するときは `Ctrl+C` を押します。

### Botの動作

- オーナー追従機能
  - Botアカウントが招待されているDiscordサーバー（ギルドともいいます）において、そのサーバーのオーナーであるユーザー（ギルドマスター）がボイスチャンネルに接続したとき、同じボイスチャンネルへ同時に接続します。
  - サーバーのオーナーがボイスチャンネルから切断すると読み上げ動作を停止し、同時にボイスチャンネルからも切断します。
- コマンドによる接続/切断/再生停止機能
  - `$connect`やP`$c`(エイリアス)で、Botがコマンドしたメンバーの接続しているボイスチャンネルに接続します。
  - `$disconnect`や`$d`(エイリアス)で、Botがボイスチャンネルから切断します。
  - `$stop`や`$s`(エイリアス)で、Botの読み上げを停止させることができます。
- Help機能
  - `$help`で、このBotで使用できるコマンドが表示されます
  - `$help connect`や`$help stop`で、それぞれの「機能の説明」や「使用できるエイリアス」が表示されます
- さびしんぼ機能
  - メンバーの切断により、ボイスチャンネルに接続しているメンバーがBotのみになった場合、Botもボイスチャンネルから切断します。
- 声色設定機能:
  - discordjtalkbot-config.jsonに、`voices`を追加し、以下のような設定(htsのフルパスを`,`でセパレート)すると、メンバーごとに適当な声色を振り分けます
  - `"voices": "/usr/local/opt/open-jtalk/voice/m100/nitech_jp_atr503_m001.htsvoice,/usr/local/opt/open-jtalk/voice/mei/mei_angry.htsvoice"`,
  - 声色を使い切った場合、また最初から振り分けます（声色が重複して設定されます）
- 接続時の動作
  - 接続中は、**すべてのチャンネルに投稿されたメッセージ**をボイスチャンネルにて読み上げます
  - URLは「URL省略」と発言します。「||」で囲われた部分は「ネタバレ」で読み替えます

### open-jtalk辞書の更新

- 下記手順に従って、`naist-jdic.csv`に単語を登録したのち、`make install`し、`sys.dic`を作成してください
  - https://Repl.it/@tetsuyaki/openjtalkdev#README.md
  - もちろん、自分のパソコンを使って生成することも可能です
  - 英単語は全角英数字でないと登録できないかもしれません（Open-jtalkに詳しくないのでわからないですが、そんな動作にみえます）
- sys.dicをアップロードし、`.dicディレクトリ`の`sys.dic`を上書きしてください
- Botを再起動すれば使用されます

### FAQ

#### 音声を読み上げない場合

- Repl.itのConsuleにあるログを見て対応してください
  - Stopボタンを押したあと、Runボタンを押すとたいてい直ります
  - バグがある場合は、Issueに書き込んでください(Repl.itでしか再現しないものは対応できないかもしれません)