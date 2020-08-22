# jtalkbot

## A Discord bot talking Japanese

Discord のテキストチャンネルに投稿されたメッセージを同名のボイスチャンネルで読み上げるボットプログラムです。


## 動作環境

以下のプログラム／ライブラリが正常に動作しているシステムが必要です。

- Python 3.8
- Open JTalk（`open_jtalk` コマンド）
- Opus ライブラリ（discord.py の音声機能に必要）


## 導入

`pip install jtalkbot-mshibata` します。

依存関係が設定されているのでプログラムの実行に必要な discord.py などのモジュールはあわせて自動的にインストールされます。

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
