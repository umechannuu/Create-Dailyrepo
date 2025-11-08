"""FastAPI application entry point"""
import sys
from fastapi import FastAPI
from dotenv import load_dotenv

from app.api.routes import router
from app.core.config import settings

# 環境変数読み込み
load_dotenv()

# 標準出力のバッファリングを無効化
sys.stdout.flush()

# FastAPIアプリケーション
app = FastAPI(
    title="Daily Report Bot",
    description="Slack → Gemini → Notion 自動日報生成システム",
    version="2.0.0"
)

# ルーターを登録
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
