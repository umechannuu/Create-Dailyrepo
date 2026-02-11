#!/bin/bash

echo "Cloud Schedulerでウォームアップジョブを設定します..."
echo ""

# プロジェクトとサービス情報
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="daily-report-bot"
REGION="asia-northeast1"

# サービスURLを取得
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)')

if [ -z "$SERVICE_URL" ]; then
    echo "❌ サービスが見つかりません"
    echo "先に ./deploy-app.sh でデプロイしてください"
    exit 1
fi

echo "設定情報:"
echo "  サービスURL: $SERVICE_URL"
echo "  スケジュール: 毎日8時（日報生成の直前）"
echo ""

# Cloud Scheduler APIを有効化
echo "Cloud Scheduler APIを有効化中..."
gcloud services enable cloudscheduler.googleapis.com

# ウォームアップジョブを作成
echo "ウォームアップジョブを作成中..."
gcloud scheduler jobs create http daily-report-warmup \
  --location $REGION \
  --schedule "0 8 * * *" \
  --uri "${SERVICE_URL}/healthz" \
  --http-method GET \
  --time-zone "Asia/Tokyo" \
  --description "Daily Report Bot のコールドスタート対策用ウォームアップ"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ウォームアップジョブの設定が完了しました！"
    echo ""
    echo "設定内容:"
    echo "  - 毎日8時にヘルスチェックエンドポイントを実行"
    echo "  - コールドスタートを防ぎ、スムーズな日報生成を実現"
    echo ""
    echo "次のステップ:"
    echo "1. 手動でテスト実行:"
    echo "   gcloud scheduler jobs run daily-report-warmup --location $REGION"
    echo "2. スケジュール変更（必要に応じて）:"
    echo "   gcloud scheduler jobs update http daily-report-warmup --location $REGION --schedule '新しいcron式'"
    echo ""
    echo "注意: Cloud Schedulerは月間3ジョブまで無料です"
else
    echo ""
    echo "❌ ウォームアップジョブの設定に失敗しました"
    exit 1
fi
