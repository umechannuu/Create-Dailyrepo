"""Gunicorn configuration with Uvicorn workers"""
import os

# サーバソケット
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"

# Uvicornワーカー
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.getenv("WORKERS", "2"))

# タイムアウト設定
timeout = 300
keepalive = 5

# ログ設定
accesslog = "-"
errorlog = "-"
loglevel = "info"

# プロセス名
proc_name = "daily-report-bot"
