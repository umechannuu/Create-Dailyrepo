#!/bin/bash

echo "🔐 Cloud Run環境変数を設定します..."
echo ""

# .envファイルから環境変数を読み込む
if [ ! -f .env ]; then
    echo "❌ .envファイルが見つかりません"
    echo "プロジェクトルートに.envファイルを作成してください"
    exit 1
fi

# .envファイルから必要な変数を取得
source .env

# 必須変数のチェック
if [ -z "$SLACK_TOKEN" ] || [ -z "$GEMINI_API_KEY" ] || [ -z "$NOTION_TOKEN" ] || [ -z "$NOTION_DB_ID" ]; then
    echo "❌ 以下の環境変数が.envに設定されていません:"
    [ -z "$SLACK_TOKEN" ] && echo "  - SLACK_TOKEN"
    [ -z "$GEMINI_API_KEY" ] && echo "  - GEMINI_API_KEY"
    [ -z "$NOTION_TOKEN" ] && echo "  - NOTION_TOKEN"
    [ -z "$NOTION_DB_ID" ] && echo "  - NOTION_DB_ID"
    exit 1
fi

SERVICE_NAME="daily-report-bot"
REGION="asia-northeast1"

echo "📋 設定する環境変数:"
echo "  - SLACK_TOKEN: ${SLACK_TOKEN:0:20}..."
echo "  - GEMINI_API_KEY: ${GEMINI_API_KEY:0:20}..."
echo "  - NOTION_TOKEN: ${NOTION_TOKEN:0:20}..."
echo "  - NOTION_DB_ID: $NOTION_DB_ID"
echo "  - TZ: Asia/Tokyo"
echo ""

# Cloud Runに環境変数を設定
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars "SLACK_TOKEN=$SLACK_TOKEN,GEMINI_API_KEY=$GEMINI_API_KEY,NOTION_TOKEN=$NOTION_TOKEN,NOTION_DB_ID=$NOTION_DB_ID,TZ=Asia/Tokyo"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 環境変数の設定が完了しました！"
    echo ""
    echo "次のステップ:"
    echo "1. ./deploy-simple.sh でアプリケーションをデプロイ"
    echo "2. Slackで /dailyreport を実行してテスト"
else
    echo ""
    echo "❌ 環境変数の設定に失敗しました"
    exit 1
fi
