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

4. [準備作業(Homebrew)](#準備作業Homebrew)

5. [本作業](#本作業)

6. [使いかた](#使いかた)

7. [Botの実行](#Botの実行)

8. [Botの動作](#Botの動作)

9. [Dockerでの動かし方](#dockerでの動かし方)

## 動作環境

以下のプログラム／ライブラリが正常に動作しているシステムが必要です。  
(Repl.itでは自動で設定されるようにシェルを作りましたので、準備は不要です)

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

### repl.itで使用する際の注意

repl.itの場合は、**ブランチをfor-replit**にしてください  
`git clone -b for-replit https://github.com/tetsuya-ki/discord-jtalkbot.git`  
jsonにトークンを書き込まないようにしてください(公開されてしまうため)。  
その代わり、環境変数はサイドバーのSecrets(Environment variables)で指定してください。  
(discordjtalkbot-config.jsonにトークンを記述しては**いけません**。二度目)  
Herokuで使えるかは試してないから分かりません。

### 準備作業(Homebrew)

何も対策せずに実行すると、PyAudioをインストール中に`portaudio.hが見つからない`旨のエラーが発生したため、[Qiitaの記事](https://qiita.com/mayfair/items/abb59ebf503cc294a581#%E5%95%8F%E9%A1%8C)を参考に、portaudioをインストールし、「インストールされたライブラリおよびインクルードファイルの位置を指定」した上でpip installします。

```sh
brew install open-jtalk
brew install opus
brew install portaudio
sudo env LDFLAGS="-L/usr/local/lib" CFLAGS="-I/usr/local/include" pip3 install pyaudio
```

### 本作業

`git clone` します。その後、start.shとdownload.shに実行権限を与え、start.shを実行します。

### 例

  ```sh
  ~/ $ git clone https://github.com/tetsuya-ki/discord-jtalkbot.git
  ~/ $ cd discord-jtalkbot
  ~/ $ chmod 755 start.sh download.sh 
  ~/ $ ls -la start.sh download.sh
  -rwxr-xr-x  1 mac_mini  staff  964 12 25 11:32 download.sh
  -rwxr-xr-x  1 mac_mini  staff  635 12 25 11:32 start.sh
  ~/ $ ./start.sh
  ```

## 使いかた

### 設定ファイルの準備

はじめに `discordjtalkbot-config.json` ファイルを編集します。  
ライブラリ内にサンプルファイルが `discordjtalkbot-config.sample.json` として入っていますので、これをコピー、リネームして使ってください。

#### discordjtalkbot-config.json

  ```JSON
  {
    "token": "__ENTER_YOUR_TOKEN_HERE__",
    "aq_dev_key": "000-000-000",
    "open_jtalk_flags": "-x /dic -m .hts_voice/mei_normal.htsvoice",
    "voice_hello": "みなさんこんにちは。",
    "text_start": "読み上げを始めます。",
    "text_end": "読み上げを終わります。",
    "voices": ".hts_voice/nitech_jp_atr503_m001.htsvoice,.hts_voice/mei_angry.htsvoice,.hts_voice/mei_bashful.htsvoice,.hts_voice/mei_happy.htsvoice,.hts_voice/mei_normal.htsvoice,.hts_voice/mei_sad.htsvoice",
    "except_prefix": "!,$,/",
    "read_name": "True",
    "read_system_message": "True",
    "read_all_guild": "False",
    "owner_connect": "True",
    "owner_disconnect": "True"
  }
  ```

#### `token`

文字列型。Discordによって発行されたBotアカウントのトークンを記述します(**トークンは厳重に管理し公開されないようにしてください**)
＊replitなどの場合Secretを保管するところに登録し、jsonには記載しないこと！

#### `aq_dev_key`

文字列型。[AquesTalk2](https://www.a-quest.com/products/aquestalk_2.html)の開発ライセンスキーを記述します(**開発ライセンスキーは厳重に管理し公開されないようにしてください**)
＊replitなどの場合Secretを保管するところに登録し、jsonには記載しないこと！

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

#### `owner_connect`

文字列型。オーナー追従機能・接続（オーナーが接続すると、そのボイスチャンネルに接続する機能）が動くかを決めます（デフォルトはTrue/オフにしたい場合はFalseを指定）

#### `owner_disconnect`

文字列型。オーナー追従機能・切断（オーナーが切断すると、ボイスチャンネルから切断する機能）が動くかを決めます（デフォルトはTrue/オフにしたい場合はFalseを指定）

### Botの実行

 `python3 discordjtalkbot/discordJtalkbot.py` コマンドを実行します。  
 下記設定ファイルを参照し、処理を開始します。  
 `{Clone先ディレクトリ}/discordjtalkbot/cogs/modules/files/discordjtalkbot-config.json`

起動するとログを表示しながら待機し続けます。

```sh
~/discord-jtalkbot $ ./start.sh
INFO:discordJtalkbot.py$__main__:Opus library is loaded.
INFO:discordJtalkbot.py$__main__:discordjtalkbot/discordJtalkbot.py is running.
INFO:cogs.autoreadercog:We have logged in as MyBot#nnnn.
```

Botを停止するときは `Ctrl+C` を押します。

### AquesTalk2を使う場合

[AQUESTの評価版ダウンロード](https://www.a-quest.com/download.html)から以下の圧縮ファイルをダウンロードします

- AquesTalk2 Mac(v2.3.0で確認)
- AqKanji2Koe-A Mac(v3.0.0で確認)
  - なお、**評価版は「ナ行、マ行」の音韻がすべて「ヌ」になる制限があります。**
- この項目の記載は[個人利用](https://www.a-quest.com/licence_free.html)である前提で記載しています
  - このリポジトリの内容について、株式会社アクエストには問い合わせしないようにしてください(迷惑になってしまうため)
  - やらないと思いますが、学校利用、商用利用などはできません(個人で趣味の範囲でお楽しみください)

#### ディレクトリ構成

```sh
./discordjtalkbot/cogs/modules/secret/
┝aq_dic/...→辞書ファイルが配置される
┝aq_dic_large/...→辞書ファイル(大)が配置される
┝AqKanji2Koe.framework/...
┝AquesTalk2.framework/...→製品版SDKの場合
┝AquesTalk2Eva.framework/...→評価版の場合
┝output_file/...→出力ファイルが配置される
┗phont/...→phontファイルが配置される
```

#### ディレクトリ構成の手順

![移動元](https://gyazo.com/7e25b832d182d3683f12315bd43881d3.png)
![移動先](https://gyazo.com/c41fc1d0f2617e3fe10824c848772778.png)
![移動先](https://gyazo.com/e36a27b29dacd31d2a8e9f9960595ffc.png)

#### サンプル実行

以下を実行する

```sh
discordjtalkbot/cogs/modules/secret/secret_bou.py
```

#### エラーが発生した場合の手順

認証できない的なエラーが発生した場合、以下の手順で対応すること
＊ゴミ箱に入れないでください。とりあえずキャンセル押してください(「RuntimeError: ライブラリが読み込めませんでした」になる想定)

- 方針としては以下(この後画像つきで説明します)

1. System Preferences.appを開く
2. 「一般」タブにする(デフォルトのはず)
3. 一番下の「変更するにはカギをクリックします。」を選択し、パスワードを入力。変更できる状態にする
4. ダウンロードしたアプリケーションの実行許可を「App Storeと確認済みの開発元からのアプリケーションを許可」(下側)にする
5. 「このまま許可」するを選ぶ
6. もう一度実行する

- System Preferences.appで許可する

![System Preferences.appで許可する](https://gyazo.com/feea53ae309cb6a8029c4774cb19c88d.png)

- ボタン押すと下に書いてあった文章が消える

![ボタン押すと下に書いてあった文章が消える](https://gyazo.com/68d29fb126e0ae7c48abe04ce273cfb9.png)

- [再実行](#サンプル実行)する
  - 開いても良いか聞かれたら「開く」を選択する

![再実行する](https://gyazo.com/1e302341df8979e73339b94f28e630ca.png)

- エラーなく完了する想定

![エラーなく完了](https://gyazo.com/d4e6a078728d8eab39242565f1f340b3.png)

#### 実行

- [jsonファイル](#discordjtalkbot-config.json)でvoicesをAquesTalk2対応のリストに差し替える
- ![差し替え前](https://gyazo.com/bde459bfd1f403f8f82b4c10db0bce68)
  - voicesをリネームし、vocies_等の他とかぶらない文字列にする
  - voices_yukkuriをvoicesにリネームする
    - ![差し替え前](https://gyazo.com/cf3c5baad62915fb5c6d813f07cd4fb5)
  - ./start.shで起動し、何か文字列を投稿する(デフォルトのみopenjtalkのため)
    - AquesTalk2の音声になっていることを確認する
    - お疲れ様でした。。。

### AquesTalk2の開発者キーがある場合

#### ローカルの場合

- 環境変数「AQ_DEV_KEY」に開発者キーをセットする
  - `export AQ_DEV_KEY=開発者キー`で設定できます(毎回やらないとダメかも知れません)
- jsonファイルに直接記載する
  - 前述のdiscordjtalkbot-config.jsonの`"aq_dev_key": "000-000-000",`にある「**000-000-000**」へ開発者キーを記載し、保存する
    - 公開されてしまうので、ローカル環境のみで実施すること！
    - こちらの場合、小文字なので注意

#### ローカル以外の場合

- 注意: **この機能を公開されて誰でもアクセスできるサイト(replit等)で動作させることはやめてください(株式会社アクエストの著作物を再頒布してしまうため)**
- 環境変数「AQ_DEV_KEY」に開発者キーをセットする
  - こちらの場合、大文字なので注意

### Botの動作

- オーナー追従機能
  - Botアカウントが招待されているDiscordサーバー（ギルドともいいます）において、そのサーバーのオーナーであるユーザー（ギルドマスター）がボイスチャンネルに接続したとき、同じボイスチャンネルへ同時に接続します。
  - サーバーのオーナーがボイスチャンネルから切断すると読み上げ動作を停止し、同時にボイスチャンネルからも切断します。
    - `discordjtalkbot-config.json`の`owner_connect`,`owner_disconnect`で機能を停止できます。
- コマンドによる接続/切断/再生停止機能
  - `$connect`やP`$c`(エイリアス)で、Botがコマンドしたメンバーの接続しているボイスチャンネルに接続します。
  - `$disconnect`や`$d`(エイリアス)で、Botがボイスチャンネルから切断します。
  - `$stop`や`$s`(エイリアス)で、Botの読み上げを停止させることができます。
  - `$set チャンネル名(もしくは、#チャンネル)`で、読み上げるチャンネルを1つだけにできます。
    - `$reset`で、すべてのチャンネルを読み上げるようにできます。
- Help機能
  - `$help`で、このBotで使用できるコマンドが表示されます
  - `$help connect`や`$help stop`で、それぞれの「機能の説明」や「使用できるエイリアス」が表示されます
- さびしんぼ機能
  - メンバーの切断により、ボイスチャンネルに接続しているメンバーがBotのみになった場合、Botもボイスチャンネルから切断します。
- 声色設定機能:
  - discordjtalkbot-config.jsonに、`voices`を追加し、以下のような設定
    - open_jtalkの場合は`start.sh`から相対パスを`,`でセパレート
    - AquestTalk2の場合は**phont/xxxx**のような相対パスを`,`でセパレート
  - すると、メンバーごとに適当な声色を振り分けます
  - `"voices": ".hts_voice/nitech_jp_atr503_m001.htsvoice,.hts_voice/mei_angry.htsvoice"`,
    - ↑↑↑open_jtalkのみのパターン↑↑↑
  - `"voices": "phont/aq_f1c.phont,phont/aq_f3a.phont,phont/aq_huskey.phont`,
    - ↑↑↑AquestTalk2のみのパターン↑↑↑
  - `"voices": ".hts_voice/nitech_jp_atr503_m001.htsvoice,phont/aq_f1c.phont"`,
    - ↑↑↑混在のパターン↑↑↑
  - 声色を使い切った場合、また最初から振り分けます（声色が重複して設定されます）
- 接続時の動作
  - 接続中は、**すべてのチャンネルに投稿されたメッセージ**をボイスチャンネルにて読み上げます
  - URLは「URL省略」と発言します。「||」で囲われた部分は「ネタバレ」で読み替えます

### Dockerでの動かし方

Docker Hubのページは以下です。  
<https://hub.docker.com/r/tk2812/discord-jtalkbot>
＊オートでDockerイメージをビルドできなくなってしまったので、古い可能性が高いです。。。

#### Pull from Docker Hub

`docker pull tk2812/discord-jtalkbot:latest`

#### Run docker container  

TOKENを環境変数で指定し、docker runする。

`docker run -e TOKEN=XXXXXXXX tk2812/discord-jtalkbot:latest`

#### Build Dockerfile(memo)

- 開発用にDockerイメージを作成  
`docker build -t discord-jtalkbot:dev .`

- 開発用のDockerイメージからコンテナを作成  
`docker run -e TOKEN=XXXXXXXX discord-jtalkbot:dev`
