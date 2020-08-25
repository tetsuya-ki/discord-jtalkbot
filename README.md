# jtalkbot

## A Discord bot talking Japanese

Discord のテキストチャンネルに投稿されたメッセージを同名のボイスチャンネルで読み上げるボットプログラムです。


## 動作環境

以下のプログラム／ライブラリが正常に動作しているシステムが必要です。

- [Python 3.8](https://www.python.org "Welcome to Python.org")
- [Open JTalk](http://open-jtalk.sourceforge.net "Open JTalk")（`open_jtalk` コマンド）
- [Opus ライブラリ](https://opus-codec.org "Opus Codec")（[discord.py](https://pypi.org/project/discord.py/ "discord.py · PyPI") の音声機能に必要）

それぞれの導入方法はお使いのシステムによって違いますので各自でお調べください。私は macOS で [MacPorts](https://www.macports.org "The MacPorts Project -- Home") を使っています。

## 導入

`pip install jtalkbot-mshibata` します。

依存関係が設定されているのでプログラムの実行に必要なモジュールはあわせて自動的にインストールされます。

インストールが終わると、`jtalkbot` コマンドが使えるようになっています。

### 例

    ~/app % mkdir jtalkbot
    ~/app % cd jtalkbot
    ~/app/jtalkbot % python3 -m venv .venv
    ~/app/jtalkbot % source .venv/bin/activate
    (.venv) ~/app/jtalkbot % pip install jtalkbot-mshibata
    ...
    (.venv) ~/app/jtalkbot % jtalkbot --version
    jtalkbot 0.1.0

## 使いかた

### 設定ファイルの準備

はじめに `jtalkbot-config.json` ファイルを編集します。ライブラリ内にサンプルファイルが `jtalkbot-config-sample.json` として入っていますので、これをコピー、リネームして使ってください。

#### `jtalk-config.json` ファイルの例

```JSON
{
    "token": "__ENTER_YOUR_TOKEN_HERE__",
    "libopus": "/opt/local/lib/libopus.dylib",
    "open_jtalk": "/opt/local/bin/open_jtalk",
    "open_jtalk/dic": "/opt/local/lib/open_jtalk/dic",
    "open_jtalk/voice": "/opt/local/lib/open_jtalk/voice/mei/mei_normal.htsvoice",
    "voice/hello": "みなさんこんにちは。",
    "text/start": "読み上げを始めます。",
    "text/end": "読み上げを終わります。"
}
```

#### `token`

文字列型。Discord によって発行されたボットアカウントのトークンを記述します。

#### `libopus`

文字列型。Opus ライブラリの場所をフルパスで記述します。ファイル名は macOS では `libopus.dylib`、Linux では `libopus.so`、Windows では `libopus.dll` などになっていることが多いでしょう。

#### `open_jtalk`

文字列型。`open_jtalk` コマンドの場所をフルパスで記述します。あらかじめコマンドを実行してみて適切に動作することを確認しておいてください。

#### `open_jtalk/dic`

文字列型。`open_jtalk` コマンドの `-x` オプションに渡す辞書ディレクトリの場所をフルパスで記述します。

#### `open_jtalk/voice`

文字列型。`open_jtalk` コマンドの `-m` オプションに渡す HTS 音声ファイルの場所をフルパスで記述します。

#### `voice/hello`

文字列型。ボットが Discord の音声チャンネルに接続したとき最初に発声するあいさつを記述します。

#### `text/start`

文字列型。ボットがテキストチャンネルの投稿の読み上げを開始するときにそのテキストチャンネルに投稿するメッセージを記述します。

#### `text/end`

文字列型。ボットがテキストチャンネルの投稿の読み上げを停止するときにそのテキストチャンネルに投稿するメッセージを記述します。

### ボットの実行

パッケージと一緒にインストールされる `jtalkbot` コマンドを実行します。ボットを停止するときは Ctrl+C を押します。

```
~/app % jtalkbot
2020-08-25 19:25:57 INFO Opus library is loaded.
2020-08-25 19:26:00 INFO Logged in as MyBot#0123.
```

### ボットの動作

ボットアカウントが招待されている Discord サーバー（ギルドともいいます）において、そのサーバーのオーナーであるユーザー（ギルドマスター）がボイスチャンネルに接続したとき、同じボイスチャンネルに同時に接続します。接続中は、そのボイスチャンネルと __同名のテキストチャンネル__ に投稿されたメッセージをボイスチャンネルにて読み上げます。サーバーのオーナーがボイスチャンネルから切断すると読み上げ動作を停止し、同時にボイスチャンネルからも切断します。

現時点ではこれだけです。
