"""
ローカル開発用起動スクリプト

FastAPI + Uvicornで起動します。
本番環境ではgunicorn.conf.pyを使用してください。
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )
