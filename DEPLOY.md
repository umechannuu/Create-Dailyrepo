# 🚀 Google Cloud Run デプロイ - 完全ガイド

## ✅ 準備完了！

すべてのファイルが作成され、デプロイの準備が整いました。

## 📋 作成されたファイル一覧

### デプロイ関連
- ✅ `Dockerfile` - コンテナイメージ定義
- ✅ `.dockerignore` - ビルド除外ファイル
- ✅ `deploy-simple.sh` - 簡単デプロイスクリプト（推奨）
- ✅ `deploy.sh` - 詳細設定デプロイスクリプト
- ✅ `check-deploy.sh` - デプロイ準備チェック

### ドキュメント
- ✅ `docs/deploy-summary.md` - デプロイ完了まとめ
- ✅ `docs/deploy-cloudrun.md` - 詳細ガイド
- ✅ `docs/quickstart-deploy.md` - クイックスタート
- ✅ `docs/deploy-checklist.md` - チェックリスト

### コード変更
- ✅ `main.py` - 非同期処理対応
- ✅ `requirements.txt` - gunicorn追加

## 🎯 次にやること

### ステップ1: gcloud CLI のインストール

```bash
# macOS (Homebrew)
brew install --cask google-cloud-sdk

# または公式サイトからダウンロード
# https://cloud.google.com/sdk/docs/install
```

インストール後、シェルを再起動してください。

### ステップ2: gcloud の初期設定

```bash
# 認証
gcloud auth login

# プロジェクトを作成または選択
gcloud projects list  # 既存プロジェクト確認

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# デフォルトリージョンを設定
gcloud config set run/region asia-northeast1
```

### ステップ3: デプロイ前チェック

```bash
./check-deploy.sh
```

すべて ✓ になれば準備完了！

### ステップ4: デプロイ実行

```bash
./deploy-simple.sh
```

初回は5-10分かかります。コーヒーでも飲んで待ちましょう☕

### ステップ5: 環境変数を設定

デプロイ完了後、以下を実行：

```bash
gcloud run services update daily-report-bot \
  --region asia-northeast1 \
  --set-env-vars="SLACK_TOKEN=xoxb-9837354861649-9837372812721-tcjCN3HwGu35AwRq3Tg5MQoH,SLACK_SIGNING_SECRET=9e0d94b9541032f97d9cc94995a2f30d,GEMINI_API_KEY=AIzaSyD9__cKfEJgJBfCPDkutdvBVbiWWEmA5dA,NOTION_TOKEN=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,NOTION_DB_ID=10b0fc5ef14a4414b8818f08d2d333a4"
```

### ステップ6: サービスURLを取得

```bash
gcloud run services describe daily-report-bot \
  --region asia-northeast1 \
  --format='value(status.url)'
```

出力例: `https://daily-report-bot-xxxxx-an.a.run.app`

### ステップ7: Slackアプリを設定

1. https://api.slack.com/apps を開く
2. 「Create Note」アプリを選択
3. 「Slash Commands」→ `/dailyreport` を編集
4. Request URL に `https://YOUR_SERVICE_URL/slack/command` を設定
5. 保存

### ステップ8: テスト！

Slackで実行：
```
/dailyreport
```

✅ 「日報生成を開始しました」と表示されれば成功！

## 📊 よくある質問

### Q: gcloud CLIのインストールが必要？
**A:** はい。Cloud Runへのデプロイには必須です。

### Q: コストはかかる？
**A:** 無料枠内（月2百万リクエスト）なら0円です。

### Q: デプロイに失敗したら？
**A:** ログを確認してください：
```bash
gcloud builds log $(gcloud builds list --limit 1 --format="value(id)")
```

### Q: 環境変数を変更したい
**A:** いつでも再設定できます：
```bash
gcloud run services update daily-report-bot \
  --region asia-northeast1 \
  --set-env-vars="KEY=VALUE,..."
```

### Q: ローカルでテストしたい
**A:** 以下を実行：
```bash
uv run python main.py
```

## 🔧 トラブルシューティング

### gcloudコマンドが見つからない

シェルを再起動するか、PATHを設定：
```bash
# .zshrc または .bash_profile に追加
source '/usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.zsh.inc'
```

### デプロイが遅い

初回は時間がかかります（5-10分）。2回目以降は2-3分です。

### Slackコマンドがタイムアウト

バックグラウンド処理なので、即座に応答が返ります。
Notionへの反映は数分かかります。

### 環境変数が効かない

Cloud Runコンソールで確認：
https://console.cloud.google.com/run

## 📚 詳細ドキュメント

- **完全ガイド**: [deploy-cloudrun.md](docs/deploy-cloudrun.md)
- **クイックスタート**: [quickstart-deploy.md](docs/quickstart-deploy.md)
- **チェックリスト**: [deploy-checklist.md](docs/deploy-checklist.md)
- **まとめ**: [deploy-summary.md](docs/deploy-summary.md)

## 🎉 デプロイ完了後

成功したら：
1. ✅ Cloud Runコンソールでサービスを確認
2. ✅ ログを監視
3. ✅ Slackで実際に使ってみる
4. ✅ Notionに日報が作成されるか確認

## 🔒 セキュリティ強化（推奨）

本番運用では Secret Manager を使用：

```bash
# シークレット作成
echo -n "xoxb-..." | gcloud secrets create slack-token --data-file=-
echo -n "AIza..." | gcloud secrets create gemini-api-key --data-file=-
echo -n "secret_..." | gcloud secrets create notion-token --data-file=-

# サービスに設定
gcloud run services update daily-report-bot \
  --region asia-northeast1 \
  --set-secrets="SLACK_TOKEN=slack-token:latest,GEMINI_API_KEY=gemini-api-key:latest,NOTION_TOKEN=notion-token:latest"
```

詳細: [deploy-cloudrun.md](docs/deploy-cloudrun.md#secret-managerを使用セキュア推奨)

---

**準備完了！🚀**

gcloud CLI をインストールして、`./deploy-simple.sh` を実行しましょう！
