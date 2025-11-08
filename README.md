# Slack Daily Report Generator

Slackの複数チャンネルから当日のメッセージを収集し、Gemini APIで自動要約してNotionに日報を投稿するシステムです。

## システム概要

1. Slackで `/dailyreport` コマンドを実行
2. 指定チャンネルから前日のメッセージを取得
3. Gemini 2.5 Flash でチャンネルごとに要約生成
4. Notionデータベースにチャンネルごとのページを作成
5. メッセージ内のURLを参考文献として自動添付

## 主要機能

- Slackスラッシュコマンド対応（非同期処理）
- 複数チャンネルの一括処理
- AI要約による日報自動生成
- URL自動検出と参考文献リンク生成
- チャンネル別のタグ付け
- Google Cloud Run対応（本番環境）

## 技術スタック

- Python 3.12+ / uv（パッケージマネージャー）
- Flask + Gunicorn
- Slack Web API
- Google Gemini 2.5 Flash API
- Notion REST API
- Docker / Google Cloud Run

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd daily_report
```

### 2. 環境変数の設定

`.env` ファイルを作成：

```bash
# Slack
SLACK_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# Gemini
GEMINI_API_KEY=your-api-key

# Notion
NOTION_TOKEN=secret_your-integration-token
NOTION_DB_ID=your-database-id

# その他
TZ=Asia/Tokyo
PORT=8080
```

### 3. 依存関係のインストール

```bash
uv sync
```

### 4. 対象チャンネルの設定

`slack_client.py` の `CHANNEL_NAME_MAP` を編集：

```python
CHANNEL_NAME_MAP = {
    "C09PT0PR0MV": "作業-研究",
    "C09QC16DAJY": "作業-epic",
    "C09Q6CYB8MU": "作業-kaggle",
    "C09R2PC3J7J": "作業-個人"
}
```

各チャンネルにボットを招待してください。

### 5. Notionデータベースの準備

以下のプロパティを持つデータベースを作成：

- Name（Title）: タイトル
- Tags（Multi-select）: タグ（研究、EpicAI、kaggle、個人作業）

Notionインテグレーションをデータベースに接続してください。

### 6. Slackアプリの設定

1. https://api.slack.com/apps で新規アプリを作成
2. OAuth & Permissions で以下のスコープを追加：
   - `channels:history`
   - `chat:write`
   - `commands`
3. Slash Commands で `/dailyreport` を作成
   - Request URL: `https://your-server.com/slack/command`
4. ワークスペースにインストール

## 使い方

### ローカル開発

```bash
# サーバ起動
uv run python main.py

# ブラウザでテスト
# http://localhost:8080/test
```

### 本番環境（Google Cloud Run）

```bash
# デプロイ
./deploy-app.sh

# デプロイ後、SlackアプリのRequest URLを更新
# https://<service-url>.run.app/slack/command
```

### Slackでの実行

Slackで以下を入力：

```
/dailyreport
```

処理は非同期で実行されます：
1. 即座に「日報生成を開始しました」メッセージが表示
2. バックグラウンドで処理実行（2-3分）
3. 完了後、Slackに通知

## 処理の流れ

1. スラッシュコマンド受信
2. 前日0時〜24時のメッセージを各チャンネルから取得
3. チャンネルごとにメッセージをグループ化
4. Gemini APIで要約生成（作業内容・知見・予定の3セクション）
5. URLを抽出して参考文献リストを作成
6. Notionにチャンネル別ページを作成

## プロジェクト構成

```
daily_report/
├── main.py                 # Flaskアプリケーション
├── slack_client.py         # Slackメッセージ取得
├── gemini_client.py        # Gemini要約生成
├── notion_client.py        # Notion投稿処理
├── utils/
│   ├── formatter.py        # メッセージ整形・URL抽出
│   └── time_utils.py       # 時刻処理（zoneinfo使用）
├── requirements.txt        # Python依存パッケージ
├── Dockerfile              # コンテナイメージ定義
├── deploy-simple.sh        # Cloud Runデプロイスクリプト
└── .env                    # 環境変数（要作成）
```
