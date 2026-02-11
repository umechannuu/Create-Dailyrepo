# Slack Daily Report Generator

Slackの複数チャンネルから当日のメッセージを収集し、Gemini APIで自動要約してNotionに日報を投稿するシステムです。

## システム概要

1. Slackで `/dailyreport` コマンドを実行（時間指定オプション対応）
2. 指定チャンネルから対象期間のメッセージを非同期で取得
3. Gemini 2.5 Flash でチャンネルごとに並列要約・TODO提案を生成
4. Notionデータベースにチャンネルごとのページを並列作成
5. メッセージ内のURLを参考文献として自動添付

## 主要機能

- FastAPI + 非同期処理による高速化
- チャンネルごとの並列処理（Slack取得、Gemini要約、Notion投稿）
- Slackスラッシュコマンド対応（BackgroundTasks使用）
- AI要約による日報自動生成
- AI提案TODO（優先度・所要時間付き）
- 時間指定機能（時間数 / 日時 / 日付で期間指定可能）
- URL自動検出と参考文献リンク生成
- チャンネル別のタグ付け
- 軽量ヘルスチェック（`/healthz`）
- Google Cloud Run対応（Gunicorn + Uvicorn workers）

## 技術スタック

- Python 3.12+ / uv（パッケージマネージャー）
- FastAPI（非同期Webフレームワーク）
- Gunicorn + Uvicorn workers（本番環境）
- httpx（非同期HTTPクライアント）
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

`app/core/config.py` の `CHANNEL_NAME_MAP` を編集：

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
# サーバ起動（開発モード）
uv run python run.py

# または直接FastAPIアプリを起動
uv run uvicorn app.main:app --reload --port 8080

# ブラウザでテスト
# http://localhost:8080/test
```

### 本番環境（Google Cloud Run）

**詳細なデプロイ手順は [デプロイガイド](docs/deploy_guide.md) を参照してください。**

```bash
# 無料枠を最大限活用する設定でデプロイ
./deploy-app.sh

# 環境変数を設定
./setup-env.sh

# （オプション）コールドスタート対策のウォームアップ設定
./setup-warmup.sh

# デプロイ後、SlackアプリのRequest URLを更新
# https://<service-url>.run.app/slack/command
```

### Slackでの実行

Slackで以下を入力：

```
/dailyreport          # デフォルト（過去18時間）
/dailyreport 6        # 過去6時間
/dailyreport 24       # 過去24時間
/dailyreport 2026-01-06 09:00  # 指定日時から現在まで
/dailyreport 2026-01-06        # 指定日の0時から現在まで
```

処理は非同期で実行されます：
1. 即座に「日報生成を開始しました」メッセージと対象期間が表示
2. バックグラウンドで並列処理実行（1-2分に短縮）
3. 完了後、Slackに通知

## 処理の流れ

1. スラッシュコマンド受信（FastAPI）、時間範囲をパース
2. BackgroundTasksでバックグラウンド処理開始
3. 指定期間のメッセージを全チャンネルから並列取得（httpx）
4. チャンネルごとにメッセージをグループ化
5. 各チャンネルを並列処理：
   - Gemini APIで要約・TODO提案生成（asyncio.gather）
   - URLを抽出して参考文献リストを作成
6. Notionにチャンネル別ページを並列作成（httpx）
7. 完了通知をSlackに送信

## プロジェクト構成

```
daily_report/
├── app/                        # FastAPIアプリケーション
│   ├── __init__.py
│   ├── main.py                 # FastAPIエントリーポイント
│   ├── core/                   # コア設定
│   │   ├── __init__.py
│   │   └── config.py           # 環境変数・設定管理
│   ├── api/                    # APIエンドポイント
│   │   ├── __init__.py
│   │   └── routes.py           # ルート定義
│   └── services/               # ビジネスロジック
│       ├── __init__.py
│       ├── slack_service.py    # Slack API（非同期）
│       ├── gemini_service.py   # Gemini API（非同期）
│       ├── notion_service.py   # Notion API（非同期）
│       └── report_service.py   # 日報生成オーケストレーション
├── utils/                      # ユーティリティ
│   ├── __init__.py
│   ├── formatter.py            # メッセージ整形・URL抽出
│   └── time_utils.py           # 時刻処理（zoneinfo使用）
├── run.py                      # ローカル開発用起動スクリプト
├── gunicorn.conf.py            # Gunicorn設定（本番環境）
├── requirements.txt            # Python依存パッケージ
├── Dockerfile                  # コンテナイメージ定義
├── deploy-simple.sh            # Cloud Runデプロイスクリプト
└── .env                        # 環境変数（要作成）

※ 旧ファイル（main.py, slack_client.py, gemini_client.py, notion_client.py）は
  互換性のため残していますが、実際にはapp/配下の新しい構成を使用します。
```
