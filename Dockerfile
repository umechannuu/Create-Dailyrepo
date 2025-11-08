# Python 3.12のスリムイメージを使用
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのファイルをコピー
COPY . .

# 環境変数でポートを設定（Cloud Runから提供される）
ENV PORT=8080
ENV PYTHONPATH=/app

# Cloud Runのヘルスチェック用
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/')"

# FastAPI + Gunicorn + Uvicorn workersで起動
CMD exec gunicorn app.main:app -c gunicorn.conf.py
