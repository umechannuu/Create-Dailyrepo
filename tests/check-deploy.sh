#!/bin/bash

# デプロイ準備チェックスクリプト

echo "=========================================="
echo "  Cloud Run デプロイ準備チェック"
echo "=========================================="
echo

# 1. gcloud のインストール確認
echo "1. gcloud CLI のインストール確認..."
if command -v gcloud &> /dev/null; then
    echo "   ✓ gcloud がインストールされています"
    gcloud --version | head -1
else
    echo "   ✗ gcloud がインストールされていません"
    echo "     インストール: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo

# 2. 認証確認
echo "2. 認証状態の確認..."
if gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    echo "   ✓ 認証済み: $ACCOUNT"
else
    echo "   ✗ 認証されていません"
    echo "     実行: gcloud auth login"
    exit 1
fi
echo

# 3. プロジェクト確認
echo "3. GCPプロジェクトの確認..."
PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT" ]; then
    echo "   ✗ プロジェクトが設定されていません"
    echo "     実行: gcloud config set project YOUR_PROJECT_ID"
    exit 1
else
    echo "   ✓ プロジェクト: $PROJECT"
fi
echo

# 4. 環境変数の確認
echo "4. 環境変数の確認..."
if [ -f .env ]; then
    echo "   ✓ .env ファイルが存在します"
    
    # 必要な環境変数をチェック
    source .env
    
    if [ -n "$SLACK_TOKEN" ]; then
        echo "   ✓ SLACK_TOKEN"
    else
        echo "   ✗ SLACK_TOKEN が設定されていません"
    fi
    
    if [ -n "$GEMINI_API_KEY" ]; then
        echo "   ✓ GEMINI_API_KEY"
    else
        echo "   ✗ GEMINI_API_KEY が設定されていません"
    fi
    
    if [ -n "$NOTION_TOKEN" ]; then
        echo "   ✓ NOTION_TOKEN"
    else
        echo "   ✗ NOTION_TOKEN が設定されていません"
    fi
    
    if [ -n "$NOTION_DB_ID" ]; then
        echo "   ✓ NOTION_DB_ID"
    else
        echo "   ✗ NOTION_DB_ID が設定されていません"
    fi
else
    echo "   ✗ .env ファイルが見つかりません"
fi
echo

# 5. 必要なファイルの確認
echo "5. 必要なファイルの確認..."
files=("Dockerfile" "requirements.txt" "main.py" "deploy-simple.sh")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file が見つかりません"
    fi
done
echo

echo "=========================================="
echo "  チェック完了"
echo "=========================================="
echo
echo "次のステップ:"
echo "  1. デプロイを実行:"
echo "     ./deploy-simple.sh"
echo
echo "  2. 環境変数を設定:"
echo "     gcloud run services update daily-report-bot \\"
echo "       --region asia-northeast1 \\"
echo "       --set-env-vars=\"SLACK_TOKEN=...,GEMINI_API_KEY=...,NOTION_TOKEN=...,NOTION_DB_ID=...\""
echo
echo "  3. Slackアプリを設定"
echo
echo "詳細: docs/deploy-summary.md を参照"
echo
