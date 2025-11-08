"""API endpoints"""
from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Request
from typing import Optional
import httpx
import json

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


async def background_report_task(hours: int, response_url: Optional[str] = None):
    """バックグラウンドで日報生成を実行"""
    try:
        print(f"[INFO] バックグラウンドで日報生成を開始... (過去{hours}時間)")
        result = await generate_daily_report_async(hours=hours)
        print("[INFO] 日報生成が完了しました")
        
        # 完了通知をSlackに送信
        if response_url:
            completion_message = {
                "text": f"[SUCCESS] 過去{hours}時間の日報生成が完了しました！Notionをご確認ください。",
                "response_type": "in_channel"
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(response_url, json=completion_message)
            except Exception as e:
                print(f"[WARNING] Slack通知送信失敗（無視します）: {e}")
                
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
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(response_url, json=error_message)
            except Exception as notify_error:
                print(f"[WARNING] エラー通知送信失敗（無視します）: {notify_error}")


@router.post("/slack/command")
async def handle_slack_command(
    background_tasks: BackgroundTasks,
    command: str = Form(...),
    response_url: Optional[str] = Form(None),
    trigger_id: Optional[str] = Form(None)
):
    """Slackのスラッシュコマンドを処理"""
    
    if command != "/dailyreport":
        raise HTTPException(status_code=400, detail="無効なコマンドです。")
    
    # インタラクティブなUIを表示（時間選択）
    return {
        "response_type": "ephemeral",
        "text": "日報の時間範囲を選択してください",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*日報を生成します* \n取得するログの時間範囲を選択してください："
                }
            },
            {
                "type": "actions",
                "block_id": "time_range_selection",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "過去1時間"
                        },
                        "value": "1",
                        "action_id": "select_hours_1"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "過去6時間"
                        },
                        "value": "6",
                        "action_id": "select_hours_6"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "過去12時間"
                        },
                        "value": "12",
                        "action_id": "select_hours_12"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "過去24時間"
                        },
                        "value": "24",
                        "action_id": "select_hours_24",
                        "style": "primary"
                    }
                ]
            }
        ]
    }


@router.post("/slack/interactive")
async def handle_slack_interactive(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Slackのインタラクティブコンポーネント（ボタンクリック）を処理"""
    
    # フォームデータからpayloadを取得
    form_data = await request.form()
    payload_str = form_data.get("payload")
    
    if not payload_str:
        raise HTTPException(status_code=400, detail="payloadが見つかりません")
    
    payload = json.loads(payload_str)
    
    # アクションの取得
    actions = payload.get("actions", [])
    if not actions:
        raise HTTPException(status_code=400, detail="アクションが見つかりません")
    
    action = actions[0]
    action_id = action.get("action_id", "")
    
    # 時間範囲の取得
    if action_id.startswith("select_hours_"):
        hours = int(action.get("value", "24"))
        response_url = payload.get("response_url")
        
        # バックグラウンドタスクを追加
        background_tasks.add_task(background_report_task, hours, response_url)
        
        # 即座にレスポンスを返す
        return {
            "response_type": "in_channel",
            "replace_original": True,
            "text": f"[INFO] 過去{hours}時間の日報生成を開始しました。完了までしばらくお待ちください..."
        }
    
    return {
        "response_type": "ephemeral",
        "text": "不明なアクションです"
    }
