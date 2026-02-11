"""API endpoints"""
from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Request
from typing import Optional
import httpx
import os

from app.services.report_service import generate_daily_report_async
from utils.time_utils import parse_time_range

router = APIRouter()


@router.get("/")
async def health_check():
    """ヘルスチェック用エンドポイント"""
    return {
        "status": "ok",
        "message": "Daily Report Bot is running"
    }


@router.get("/healthz")
async def healthz():
    """軽量ヘルスチェック用（依存なし、Cloud Scheduler用）"""
    return {"status": "ok"}


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


async def background_report_task(
    response_url: Optional[str] = None,
    oldest: Optional[float] = None,
    latest: Optional[float] = None
):
    """バックグラウンドで日報生成を実行"""
    try:
        print("[INFO] バックグラウンドで日報生成を開始...")
        result = await generate_daily_report_async(oldest=oldest, latest=latest)
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
    command: str = Form(...),
    text: Optional[str] = Form(None),
    response_url: Optional[str] = Form(None)
):
    """Slackのスラッシュコマンドを処理（Cloud Tasks版）"""
    
    if command != "/dailyreport":
        raise HTTPException(status_code=400, detail="無効なコマンドです。")
    
    # 時間範囲をパース
    try:
        oldest, latest, range_description = parse_time_range(text)
    except ValueError as e:
        return {
            "response_type": "ephemeral",
            "text": f"[ERROR] 時間指定エラー: {str(e)}\n使用例: `/dailyreport 6` (6時間前から) または `/dailyreport 2026-01-06 09:00`"
        }
    
    # Cloud Tasksを使用するかどうか判定
    use_cloud_tasks = os.getenv("USE_CLOUD_TASKS", "false").lower() == "true"
    
    if use_cloud_tasks:
        # Cloud Tasksにタスクを投入（無料枠・確実）
        from app.services.tasks_service import enqueue_report_generation
        try:
            await enqueue_report_generation(oldest, latest, range_description, response_url)
            return {
                "response_type": "in_channel",
                "text": f"[INFO] 日報生成タスクを投入しました。\n対象期間: {range_description}"
            }
        except Exception as e:
            print(f"[ERROR] Cloud Tasks投入失敗: {e}")
            # フォールバック: 同期処理
            await background_report_task(response_url, oldest, latest)
            return {
                "response_type": "in_channel",
                "text": f"[INFO] 日報生成を完了しました（同期処理）。\n対象期間: {range_description}"
            }
    else:
        # 同期処理版（Cloud Tasks未設定時）
        print(f"[INFO] 日報生成を開始（同期処理）: {range_description}")
        await background_report_task(response_url, oldest, latest)
        return {
            "response_type": "in_channel",
            "text": f"[INFO] 日報生成を完了しました。\n対象期間: {range_description}"
        }


@router.post("/tasks/generate-report")
async def execute_report_task(request: Request):
    """Cloud Tasksから呼び出される日報生成タスク"""
    
    # リクエストボディを取得
    body = await request.json()
    oldest = body.get("oldest")
    latest = body.get("latest")
    range_description = body.get("range_description")
    response_url = body.get("response_url")
    
    print(f"[INFO] Cloud Tasksタスク実行開始: {range_description}")
    
    # 日報生成を実行
    await background_report_task(response_url, oldest, latest)
    
    return {"status": "success", "message": "日報生成タスクが完了しました"}


@router.post("/slack/command-sync")
async def handle_slack_command_sync(
    command: str = Form(...),
    text: Optional[str] = Form(None),
    response_url: Optional[str] = Form(None)
):
    """Slackのスラッシュコマンドを処理（同期処理版・レガシー）"""
    
    if command != "/dailyreport":
        raise HTTPException(status_code=400, detail="無効なコマンドです。")
    
    # 時間範囲をパース
    try:
        oldest, latest, range_description = parse_time_range(text)
    except ValueError as e:
        return {
            "response_type": "ephemeral",
            "text": f"[ERROR] 時間指定エラー: {str(e)}\n使用例: `/dailyreport 6` (6時間前から) または `/dailyreport 2026-01-06 09:00`"
        }
    
    # 処理を完全に待ってから応答
    print(f"[INFO] 日報生成を開始（同期処理）: {range_description}")
    await background_report_task(response_url, oldest, latest)
    
    # 処理完了後にレスポンス
    return {
        "response_type": "in_channel",
        "text": f"[INFO] 日報生成を完了しました。\n対象期間: {range_description}"
    }
