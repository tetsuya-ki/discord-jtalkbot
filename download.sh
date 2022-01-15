#!/bin/bash

FILE=.hts_voice/nitech_jp_atr503_m001.htsvoice
if [ -f ${FILE} ]; then
  echo "ダウンロード済"
else
  mkdir .dl_hts_voice
  cd .dl_hts_voice

  DL_FILE=master.zip
  if [ -f ${DL_FILE} ]; then
    echo "ダウンロード済"
  else
    # download voices
    DL1=https://github.com/icn-lab/htsvoice-tohoku-f01/archive/master.zip
    DL2=http://sourceforge.net/projects/open-jtalk/files/HTS%20voice/hts_voice_nitech_jp_atr503_m001-1.05/hts_voice_nitech_jp_atr503_m001-1.05.tar.gz
    DL3=http://sourceforge.net/projects/mmdagent/files/MMDAgent_Example/MMDAgent_Example-1.7/MMDAgent_Example-1.7.zip
    wget -h
    if [ $? = 0 ]; then
      wget ${DL1}
      wget ${DL2}
      wget ${DL3}
    else
      curl -h
      if [ $? = 0 ]; then
        curl -OL ${DL1}
        curl -OL ${DL2}
        curl -OL ${DL3}
      else
        echo "DLコマンドが分かりません。。。"
      fi # curl END
    fi # wget END
  fi # DL END
  # unarchoved voices
  unzip -o master.zip
  tar -xvzof hts_voice_nitech_jp_atr503_m001-1.05.tar.gz
  unzip -o MMDAgent_Example-1.7.zip

  cd ..
  HTS_DIR=.hts_voice
  if [ -e ${HTS_DIR} ]; then
    echo "hts_voiceは準備済"
  else
    mkdir ${HTS_DIR} 
  fi

  # move voices
  mv .dl_hts_voice/htsvoice-tohoku-f01-master/*.htsvoice .hts_voice
  mv .dl_hts_voice/MMDAgent_Example-1.7/Voice/mei/*.htsvoice .hts_voice
  mv .dl_hts_voice/hts_voice_nitech_jp_atr503_m001-1.05/*.htsvoice .hts_voice

  # delete dl directory
  rm -rf .dl_hts_voice
fi