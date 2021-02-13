#!/bin/bash
# open_jtalkの確認
open_jtalk -h
if [ $? = 0 ]; then
  echo "open_jtalkはインストール済"
else
  echo "open_jtalkがインストールされていないため、インストールを試みる"
  install-pkg open-jtalk open-jtalk-mecab-naist-jdic
fi

# ダウンロード
./download.sh

# pythonの依存ファイルインストール
poetry install

# プログラムを実行
poetry run python discordjtalkbot/discordjtalkbot.py