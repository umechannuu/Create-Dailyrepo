#!/bin/bash

# Cloud Runへの簡単デプロイ（gcloud run deploy --source を使用）

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 設定
SERVICE_NAME="daily-report-bot"
REGION="asia-northeast1"

echo -e "${GREEN}=== Daily Report Bot - Cloud Run 簡単デプロイ ===${NC}\n"

# 1. プロジェクトの確認
echo -e "${YELLOW}現在のGCPプロジェクト:${NC}"
gcloud config get-value project

read -p "このプロジェクトでデプロイしますか？ (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "デプロイを中止しました"
    exit 1
fi

# 2. 必要なAPIの有効化
echo -e "\n${YELLOW}必要なAPIを有効化中...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# 3. ソースからデプロイ（Dockerfileを自動検出）
echo -e "\n${YELLOW}Cloud Runにデプロイ中...${NC}"
gcloud run deploy ${SERVICE_NAME} \
  --source . \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10

if [ $? -ne 0 ]; then
    echo "デプロイに失敗しました"
    exit 1
fi

# 4. サービスURLの取得
echo -e "\n${YELLOW}サービス情報を取得中...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo -e "\n${GREEN}=== デプロイ完了 ===${NC}"
echo -e "サービスURL: ${GREEN}${SERVICE_URL}${NC}"
echo -e "\n${YELLOW}次のステップ:${NC}"
echo -e "1. 環境変数を設定:"
echo -e "   ${GREEN}gcloud run services update ${SERVICE_NAME} --region ${REGION} \\${NC}"
echo -e "   ${GREEN}  --set-env-vars=\"SLACK_TOKEN=xoxb-...,GEMINI_API_KEY=AIza...,NOTION_TOKEN=secret_...,NOTION_DB_ID=...\"${NC}"
echo -e "\n2. Slackアプリの設定:"
echo -e "   Request URL: ${GREEN}${SERVICE_URL}/slack/command${NC}"
echo -e "\n3. テスト:"
echo -e "   Slackで ${GREEN}/dailyreport${NC} コマンドを実行\n"
