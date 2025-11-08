"""API endpoints"""
from fastapi import APIRouter, BackgroundTasks, Form, HTTPException
from typing import Optional
import httpx

from app.services.report_service import generate_daily_report_async

router = APIRouter()


@router.get("/")
async def health_check():
    """ヘルスチェック用エンドポイント"""
    return {
        "status": "ok",
        "message": "Daily Report Bot is running"
    }


@router.get("/test")
async def test_generation():
    """テスト用エンドポイント（手動で日報生成）"""
    try:
        result = await generate_daily_report_async()
        return result
    except Exception as e:
        print(f"[ERROR] テスト実行中にエラー: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


async def background_report_task(response_url: Optional[str] = None):
    """バックグラウンドで日報生成を実行"""
    try:
        print("[INFO] バックグラウンドで日報生成を開始...")
        result = await generate_daily_report_async()
        print("[INFO] 日報生成が完了しました")
        
        # 完了通知をSlackに送信
        if response_url:
            completion_message = {
                "text": "[SUCCESS] 日報生成が完了しました！Notionをご確認ください。",
                "response_type": "in_channel"
            }
            async with httpx.AsyncClient() as client:
                await client.post(response_url, json=completion_message)
                
    except Exception as e:
        print(f"[ERROR] エラーが発生: {e}")
        import traceback
        traceback.print_exc()
        
        # エラー通知をSlackに送信
        if response_url:
            error_message = {
                "text": f"[ERROR] エラーが発生しました: {str(e)}",
                "response_type": "ephemeral"
            }
            async with httpx.AsyncClient() as client:
                await client.post(response_url, json=error_message)


@router.post("/slack/command")
async def handle_slack_command(
    background_tasks: BackgroundTasks,
    command: str = Form(...),
    response_url: Optional[str] = Form(None)
):
    """Slackのスラッシュコマンドを処理"""
    
    if command != "/dailyreport":
        raise HTTPException(status_code=400, detail="無効なコマンドです。")
    
    # バックグラウンドタスクを追加
    background_tasks.add_task(background_report_task, response_url)
    
    # 即座にレスポンスを返す（3秒以内）
    return {
        "response_type": "in_channel",
        "text": "[INFO] 日報生成を開始しました。完了までしばらくお待ちください..."
    }
