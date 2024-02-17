# palworld-discord-server-manager

自分用

## requirements

- python 3.12.1

## 使い方

- https://discord.com/developers/applications にてbotを作成
- 使いたいサーバーにボットを作成して招待
- `cp .env.example .env`
  - `.env.example`をもとにパスなどを設定
  - `DISCORD_TOKEN`にはBOTのシークレットを設定
- `palworld-discord-server-manager.service.example`を参考にsystemdに登録
  - 自動起動の設定などが必要
- `requirements.txt`をもとに依存パッケージをインストール
- `start.sh`のpythonパスとスクリプトへのパスを適切に書き換え
