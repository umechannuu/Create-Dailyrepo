#!/bin/bash

echo "Google Cloud Runにデプロイします..."
echo ""

# .envファイルの存在確認
if [ ! -f .env ]; then
    echo ".envファイルが見つかりません"
    echo "環境変数は事前に ./setup-env.sh で設定してください"
    echo ""
fi

# プロジェクトID（必要に応じて変更してください）
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="daily-report-bot"
REGION="asia-northeast1"

echo "デプロイ設定:"
echo "  プロジェクト: $PROJECT_ID"
echo "  サービス名: $SERVICE_NAME"
echo "  リージョン: $REGION"
echo ""
echo "環境変数は ./setup-env.sh で事前に設定する必要があります"
echo ""

# デプロイ実行（無料枠最適化版）
echo "無料枠を最大限活用する設定でデプロイします..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --timeout 300 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --cpu-throttling \
  --no-cpu-boost

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ デプロイが完了しました！"
    echo ""
    echo "サービスURL:"
    gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
    echo ""
    echo "次のステップ:"
    echo "1. 環境変数が設定されているか確認:"
    echo "   gcloud run services describe $SERVICE_NAME --region $REGION --format='get(spec.template.spec.containers[0].env)'"
    echo "2. 環境変数が未設定の場合: ./setup-env.sh を実行"
    echo "3. 上記のURLをSlackアプリのRequest URLに設定"
    echo "4. Request URL: <サービスURL>/slack/command"
else
    echo ""
    echo "❌ デプロイに失敗しました"
    exit 1
fi
