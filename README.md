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

`pip install jtalkbot` します。

依存関係が設定されているのでプログラムの実行に必要なモジュールはあわせて自動的にインストールされます。

インストールが終わると、`jtalkbot` コマンドが使えるようになっています。

### 例

    ~/app % mkdir jtalkbot
    ~/app % cd jtalkbot
    ~/app/jtalkbot % python3 -m venv .venv
    ~/app/jtalkbot % source .venv/bin/activate
    (.venv) ~/app/jtalkbot % pip install jtalkbot
    ...
    (.venv) ~/app/jtalkbot % jtalkbot --version
    jtalkbot X.Y.Z

## 使いかた

### 設定ファイルの準備

はじめに `jtalkbot-config.json` ファイルを編集します。ライブラリ内にサンプルファイルが `jtalkbot-config-sample.json` として入っていますので、これをコピー、リネームして使ってください。

__NOTE__: バージョン 0.6.0 で設定ファイルの項目名を変更しました。
__NOTE__: バージョン 0.5.0 で設定ファイルの項目名を変更しました。

#### `jtalk-config.json` ファイルの例

```JSON
{
    "token": "__ENTER_YOUR_TOKEN_HERE__",
    "open_jtalk_flags": "-x /opt/local/lib/open_jtalk/dic -m /opt/local/lib/open_jtalk/voice/mei/mei_normal.htsvoice",
    "voice_hello": "みなさんこんにちは。",
    "text_start": "読み上げを始めます。",
    "text_end": "読み上げを終わります。"
}
```

#### `token`

文字列型。Discord によって発行されたボットアカウントのトークンを記述します。

#### `open_jtalk_flags`

文字列型。`open_jtalk` コマンドに渡すコマンドラインオブションを記述します。読み上げに使用されます。

#### `voice_hello`

文字列型。ボットが Discord の音声チャンネルに接続したとき最初に発声するあいさつを記述します。

#### `text_start`

文字列型。ボットがテキストチャンネルの投稿の読み上げを開始するときにそのテキストチャンネルに投稿するメッセージを記述します。

#### `text_end`

文字列型。ボットがテキストチャンネルの投稿の読み上げを停止するときにそのテキストチャンネルに投稿するメッセージを記述します。

### ボットの実行

パッケージと一緒にインストールされる `jtalkbot` コマンドを実行します。このとき次の順で設定ファイルを探し、最初に見つかったものを読みこみます。

1. `./jtalkbot-config.json`
2. `~/jtalkbot-config.json`
2. `~/.local/jtalkbot-config.json`
3. `{パッケージのインストール先ディレクトリ}/jtalkbot-config.json`
4. 環境変数 `JTALKBOT_CONFIG` で指定されたファイル

起動するとログを表示しながら待機し続けます。

```
~/app/jtalkbot % jtalkbot
INFO:jtalkbot.__main__:config file: /Users/xxxx/jtalkbot-config.json
INFO:jtalkbot.__main__:Opus library is loaded.
INFO:jtalkbot.__main__:Logged in as MyBot#nnnn.
```

ボットを停止するときは `Ctrl+C` を押します。

### ボットの動作

ボットアカウントが招待されている Discord サーバー（ギルドともいいます）において、そのサーバーのオーナーであるユーザー（ギルドマスター）がボイスチャンネルに接続したとき、同じボイスチャンネルに同時に接続します。接続中は、そのボイスチャンネルと __同名のテキストチャンネル__ に投稿されたメッセージをボイスチャンネルにて読み上げます。サーバーのオーナーがボイスチャンネルから切断すると読み上げ動作を停止し、同時にボイスチャンネルからも切断します。

現時点ではこれだけです。
