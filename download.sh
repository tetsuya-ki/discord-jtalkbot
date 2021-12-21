#!/bin/bash

FILE=.hts_voice/nitech_jp_atr503_m001.htsvoice
if [ -f ${FILE} ]; then
  echo "ダウンロード済"
else
  mkdir .dl_hts_voice
  cd .dl_hts_voice

  # download voices
  wget https://github.com/icn-lab/htsvoice-tohoku-f01/archive/master.zip
  wget  http://sourceforge.net/projects/open-jtalk/files/HTS%20voice/hts_voice_nitech_jp_atr503_m001-1.05/hts_voice_nitech_jp_atr503_m001-1.05.tar.gz
  wget  http://sourceforge.net/projects/mmdagent/files/MMDAgent_Example/MMDAgent_Example-1.7/MMDAgent_Example-1.7.zip

  # unarchoved voices
  unzip master.zip
  tar -xvzof hts_voice_nitech_jp_atr503_m001-1.05.tar.gz
  unzip MMDAgent_Example-1.7.zip

  mkdir .hts_voice
  cd .hts_voice

  # move voices
  mv ../.dl_hts_voice/htsvoice-tohoku-f01-master/*.htsvoice ./
  mv ../.dl_hts_voice/MMDAgent_Example-1.7/Voice/mei/*.htsvoice ./
  mv ../.dl_hts_voice/hts_voice_nitech_jp_atr503_m001-1.05/*.htsvoice ./

  # delete dl directory
  rm -rf ../.dl_hts_voice
fi