# discord-jtalkbot

## A Discord bot talking Japanese

Discordのテキストチャンネルに投稿されたメッセージをボイスチャンネルで読み上げるBotです。  
＊このプログラムは[Masaaki Shibata](https://bitbucket.org/emptypage/)さまの[jtalkbot](https://bitbucket.org/emptypage/jtalkbot/src/master/)を改造したものです(discordが前についていますが、修正前プログラムもDiscordで動作します)  
ref. https://bitbucket.org/emptypage/jtalkbot/src/master/
> Copyright © 2020 Masaaki Shibata

＊上記は、修正前のプログラムのLICENSEから抜粋したもの

このBotは、読み上げBotを見知らぬ人のサーバーで実行することに不安を覚える人が自分のマシンで読み上げさせることが可能です。低機能ですが、そのあたりが嬉しいかもしれません。

## Table of Contesnts

1. [A Discord bot talking Japanese](#A-Discord-bot-talking-Japanese)

2. [動作環境](#動作環境)

3. [導入](#導入)

4. [準備作業(Homebrew)](#準備作業Homebrew)

5. [本作業](#本作業)

6. [使いかた](#使いかた)

7. [Botの実行](#Botの実行)

8. [Botの動作](#Botの動作)

9. [Dockerでの動かし方](#dockerでの動かし方)

## 動作環境

以下のプログラム／ライブラリが正常に動作しているシステムが必要です。

- [Python 3.8](https://www.python.org "Welcome to Python.org")
- [Open JTalk](http://open-jtalk.sourceforge.net "Open JTalk")（`open_jtalk` コマンド）
- [Opus ライブラリ](https://opus-codec.org "Opus Codec")（[discord.py](https://pypi.org/project/discord.py/ "discord.py · PyPI") の音声機能に必要）

それぞれの導入方法はお使いのシステムによって違いますので各自でお調べください([Homebrewでの導入方法は後述](#準備作業Homebrew)します)。
修正元ソースの作者さまはmacOSで[MacPorts](https://www.macports.org "The MacPorts Project -- Home") を使っています。
このソース(discord-jtalkbot)の作者は[Homebrew](https://brew.sh/index_ja)を使っています。

## 導入

### 前置き

[Dockerでの動かし方](#Dockerでの動かし方)を参照ください。Discord Botのトークンを指定するだけで、すぐに動かせます。  
以降では、Macに、Homebrewを使って環境構築し、Botを動かす手順を説明します。  
また、**このBotはWindowsではエラーが発生し、動作しません。** Dockerでなら動かせるかと思いますので、[Dockerでの動かし方](#Dockerでの動かし方)を参照ください。

### 準備作業(Homebrew)

何も対策せずに実行すると、PyAudioをインストール中に`portaudio.hが見つからない`旨のエラーが発生したため、[Qiitaの記事](https://qiita.com/mayfair/items/abb59ebf503cc294a581#%E5%95%8F%E9%A1%8C)を参考に、portaudioをインストールし、「インストールされたライブラリおよびインクルードファイルの位置を指定」した上でpip installします。

```sh
brew install open-jtalk
brew install opus
brew install portaudio
sudo env LDFLAGS="-L/usr/local/lib" CFLAGS="-I/usr/local/include" pip3 install pyaudio
```

### 本作業

`git clone` します。その後、requirements.txtのモジュールをインストールし、Botを実行します。

### 例

  ```sh
  ~/ $ git clone https://github.com/tetsuya-ki/discord-jtalkbot.git
  ~/ $ cd discord-jtalkbot
  ~/discord-jtalkbot $ python3 -m venv .venv
  ~/discord-jtalkbot $ source .venv/bin/activate
  (.venv) ~/discord-jtalkbot $ pip3 install -r requirements.txt
  ...
  (.venv) ~/discord-jtalkbot $ python3 discordjtalkbot/discordJtalkbot.py
  ```

## 使いかた

### 設定ファイルの準備

はじめに `discordjtalkbot-config.json` ファイルを編集します。  
ライブラリ内にサンプルファイルが `discordjtalkbot-config.sample.json` として入っていますので、これをコピー、リネームして使ってください。

#### `discordjtalkbot-config.json` ファイルの例

  ```JSON
  {
    "token": "__ENTER_YOUR_TOKEN_HERE__",
    "open_jtalk_flags": "-x /usr/local/opt/open-jtalk/dic -m /usr/local/opt/open-jtalk/voice/mei/mei_normal.htsvoice",
    "voice_hello": "みなさんこんにちは。",
    "text_start": "読み上げを始めます。",
    "text_end": "読み上げを終わります。"
  }
  ```

#### `token`

文字列型。Discordによって発行されたBotアカウントのトークンを記述します(**トークンは厳重に管理し公開されないようにしてください**)

#### `open_jtalk_flags`

文字列型。`open_jtalk` コマンドに渡すコマンドラインオブションを記述します。読み上げに使用されます(dicを変更したり、読み上げるボイスを指定できます)。

#### `voice_hello`

文字列型。BotがDiscordの音声チャンネルへ接続したときに、「最初に発声するあいさつ」を記述します。

#### `text_start`

文字列型。Botがテキストチャンネルの投稿の読み上げを開始するときに、そのテキストチャンネルに投稿するメッセージを記述します。

#### `text_end`

文字列型。Botがテキストチャンネルの投稿の読み上げを停止するときに、そのテキストチャンネルに投稿するメッセージを記述します(2021/01/10現在、なんか動きません)。

### Botの実行

 `python3 discordjtalkbot/discordJtalkbot.py` コマンドを実行します。  
 下記設定ファイルを参照し、処理を開始します。  
 `{Clone先ディレクトリ}/discordjtalkbot/cogs/modules/files/discordjtalkbot-config.json`

起動するとログを表示しながら待機し続けます。

```sh
~/discord-jtalkbot $ python3 discordjtalkbot/discordJtalkbot.py
INFO:discordJtalkbot.py$__main__:Opus library is loaded.
INFO:discordJtalkbot.py$__main__:discordjtalkbot/discordJtalkbot.py is running.
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
- 接続時の動作
  - 接続中は、**すべてのチャンネルに投稿されたメッセージ**をボイスチャンネルにて読み上げます
  - URLは「URL省略」と発言します。「||」で囲われた部分は「ネタバレ」で読み替えます

### Dockerでの動かし方

Docker Hubのページは以下です。  
<https://hub.docker.com/r/tk2812/discord-jtalkbot>

#### Pull from Docker Hub

`docker pull tk2812/discord-jtalkbot:latest`

#### Run docker container  

TOKENを環境変数で指定し、docker runする。

`docker run -e TOKEN=XXXXXXXX tk2812/discord-jtalkbot:latest`

#### Build Dockerfile(memo)

`docker build -t discord-jtalkbot:dev .`
