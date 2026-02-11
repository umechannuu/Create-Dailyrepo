#!/bin/bash

echo "Cloud Tasksをセットアップします..."
echo ""

PROJECT_ID=$(gcloud config get-value project)
REGION="asia-northeast1"
SERVICE_NAME="daily-report-bot"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ GCPプロジェクトが設定されていません"
    echo "gcloud config set project YOUR-PROJECT-ID を実行してください"
    exit 1
fi

echo "設定情報:"
echo "  プロジェクト: $PROJECT_ID"
echo "  リージョン: $REGION"
echo ""

# 1. Cloud Tasks APIを有効化
echo "[ステップ1/4] Cloud Tasks APIを有効化中..."
gcloud services enable cloudtasks.googleapis.com

if [ $? -ne 0 ]; then
    echo "❌ API有効化に失敗しました"
    exit 1
fi

# 2. タスクキューを作成
echo "[ステップ2/4] タスクキューを作成中..."
gcloud tasks queues create daily-report-queue \
  --location=$REGION \
  --max-attempts=3 \
  --max-concurrent-dispatches=1 \
  --max-dispatches-per-second=1 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ キュー作成成功"
else
    echo "⚠️  キューはすでに存在します（スキップ）"
fi

# 3. Cloud RunのURLを取得
echo "[ステップ3/4] Cloud Run URLを取得中..."
CLOUD_RUN_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)' 2>/dev/null)

if [ -z "$CLOUD_RUN_URL" ]; then
    echo "⚠️  Cloud Runサービスが見つかりません"
    echo "先に ./deploy-app.sh でデプロイしてください"
    CLOUD_RUN_URL="https://YOUR-SERVICE-URL.run.app"
fi

echo "  Cloud Run URL: $CLOUD_RUN_URL"

# 4. 環境変数を設定
echo "[ステップ4/4] Cloud Runに環境変数を設定中..."

# 既存の環境変数を取得
EXISTING_VARS=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(spec.template.spec.containers[0].env[*].name)' 2>/dev/null)

# .envファイルから環境変数を読み込む
if [ -f .env ]; then
    source .env
    
    gcloud run services update $SERVICE_NAME \
      --region $REGION \
      --set-env-vars "\
USE_CLOUD_TASKS=true,\
GCP_PROJECT=$PROJECT_ID,\
GCP_REGION=$REGION,\
CLOUD_RUN_URL=$CLOUD_RUN_URL,\
SLACK_TOKEN=$SLACK_TOKEN,\
GEMINI_API_KEY=$GEMINI_API_KEY,\
NOTION_TOKEN=$NOTION_TOKEN,\
NOTION_DB_ID=$NOTION_DB_ID,\
TZ=Asia/Tokyo"
else
    echo "⚠️  .envファイルが見つかりません"
    echo "最小限の設定のみ行います"
    
    gcloud run services update $SERVICE_NAME \
      --region $REGION \
      --set-env-vars "\
USE_CLOUD_TASKS=true,\
GCP_PROJECT=$PROJECT_ID,\
GCP_REGION=$REGION,\
CLOUD_RUN_URL=$CLOUD_RUN_URL"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Cloud Tasksのセットアップが完了しました！"
    echo ""
    echo "設定内容:"
    echo "  - Cloud Tasks API: 有効化済み"
    echo "  - キュー名: daily-report-queue"
    echo "  - 最大リトライ: 3回"
    echo "  - Cloud Run設定: USE_CLOUD_TASKS=true"
    echo ""
    echo "次のステップ:"
    echo "1. Slackで /dailyreport を実行してテスト"
    echo "2. ログ確認:"
    echo "   gcloud run services logs tail $SERVICE_NAME --region $REGION"
    echo "3. タスクキュー確認:"
    echo "   gcloud tasks list --queue=daily-report-queue --location=$REGION"
else
    echo ""
    echo "❌ 環境変数の設定に失敗しました"
    exit 1
fi
