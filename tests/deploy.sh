#!/bin/bash

# Google Cloud Runへのデプロイスクリプト

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# プロジェクト設定
PROJECT_ID="your-gcp-project-id"
SERVICE_NAME="daily-report-bot"
REGION="asia-northeast1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${GREEN}=== Daily Report Bot - Cloud Run デプロイ ===${NC}\n"

# 1. プロジェクトIDの確認
echo -e "${YELLOW}1. GCPプロジェクトIDを確認してください${NC}"
echo "   現在の設定: ${PROJECT_ID}"
read -p "   このまま続けますか？ (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}デプロイを中止しました${NC}"
    exit 1
fi

# 2. 必要なAPIの有効化
echo -e "\n${YELLOW}2. 必要なAPIを有効化${NC}"
gcloud services enable cloudbuild.googleapis.com --project=${PROJECT_ID}
gcloud services enable run.googleapis.com --project=${PROJECT_ID}
gcloud services enable containerregistry.googleapis.com --project=${PROJECT_ID}

# 3. Dockerイメージのビルドとプッシュ
echo -e "\n${YELLOW}3. Dockerイメージをビルド${NC}"
docker build -t ${IMAGE_NAME} .

if [ $? -ne 0 ]; then
    echo -e "${RED}Dockerビルドに失敗しました${NC}"
    exit 1
fi

echo -e "\n${YELLOW}4. イメージをGoogle Container Registryにプッシュ${NC}"
docker push ${IMAGE_NAME}

if [ $? -ne 0 ]; then
    echo -e "${RED}イメージのプッシュに失敗しました${NC}"
    exit 1
fi

# 4. Cloud Runにデプロイ
echo -e "\n${YELLOW}5. Cloud Runにデプロイ${NC}"
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --project ${PROJECT_ID}

if [ $? -ne 0 ]; then
    echo -e "${RED}Cloud Runへのデプロイに失敗しました${NC}"
    exit 1
fi

# 5. サービスURLの取得
echo -e "\n${YELLOW}6. サービスURLを取得${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format 'value(status.url)')

echo -e "\n${GREEN}=== デプロイ完了 ===${NC}"
echo -e "サービスURL: ${GREEN}${SERVICE_URL}${NC}"
echo -e "\nSlackアプリの設定:"
echo -e "  Request URL: ${GREEN}${SERVICE_URL}/slack/command${NC}"
echo -e "\n次のステップ:"
echo -e "  1. Slackアプリの設定でRequest URLを更新"
echo -e "  2. Cloud Runコンソールで環境変数を設定:"
echo -e "     - SLACK_TOKEN"
echo -e "     - SLACK_SIGNING_SECRET"
echo -e "     - GEMINI_API_KEY"
echo -e "     - NOTION_TOKEN"
echo -e "     - NOTION_DB_ID"
echo -e "  3. Slackで /dailyreport コマンドをテスト\n"
