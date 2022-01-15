#!/bin/bash
DIR=.dic
CURRENT_DIR=$(pwd)
# open_jtalkの確認
open_jtalk -h
if [ $? = 0 ]; then
  echo "open_jtalkはインストール済"
else
  echo "open_jtalkがインストールされていないため、インストールを試みる"
  install-pkg -h
  if [ $? = 0 ]; then
    install-pkg open-jtalk open-jtalk-mecab-naist-jdic
  else
    brew -v
    if [ $? = 0 ]; then
      brew install open-jtalk
    else
      echo "DL方法が分かりません。。。"
    fi
  fi
fi

if [ -e ${DIR} ]; then
  echo "dicは準備済"
else
  echo "dicを準備する"
  mkdir ${DIR}
  cd ${DIR}
  DIR_DIC=~/.apt/var/lib/mecab/dic/open-jtalk/naist-jdic
  if [ -e ${DIR_DIC} ]; then
    cp ${DIR_DIC}/*.* ./
  else
    JTALK=$(which open_jtalk)
    sed -h
    if [ $? = 1 ]; then
      DIR_DIC=`echo ${JTALK} | sed -e "s/bin/lib/"`
      if [ -e ${DIR_DIC}/dic ]; then
        cp ${DIR_DIC}/dic/*.* ./
      else
        cd ${CURRENT_DIR}
        rmdir ${DIR}
        echo "辞書配置でエラーです。DIR_DICを編集して、あなたがDLしたopen_jtalkのdicディレクトリに書き換えて再実行してください！"
      fi
    else
      cd ${CURRENT_DIR}
      rmdir ${DIR}
      echo "sedがないので辞書の場所さがすの無理でした"
    fi
  fi
fi

cd ${CURRENT_DIR}

# ダウンロード
./download.sh

# pythonの依存ファイルインストール
poetry install

# プログラムを実行
poetry run python discordjtalkbot/discordjtalkbot.py