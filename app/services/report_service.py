"""Daily report generation service - Async version"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from app.services.slack_service import fetch_all_channels_messages_async
from app.services.gemini_service import summarize_channel_messages_async
from app.services.notion_service import (
    create_multiple_reports_async,
    fetch_recent_reports_async
)
from utils.formatter import group_messages_by_channel, extract_all_urls_from_messages
from utils.time_utils import get_today_range


async def process_channel_async(
    channel_name: str, 
    messages: List[Dict],
    past_context: Optional[str] = None
) -> Tuple[str, str, List[str]]:
    """
    単一チャンネルの処理を非同期で実行
    
    Args:
        channel_name: チャンネル名
        messages: メッセージリスト
        past_context: 過去の日報テキスト（オプション）
        
    Returns:
        (チャンネル名, 要約, URLリスト)
    """
    print(f"[DEBUG] - {channel_name}: {len(messages)}件のメッセージを処理中")
    
    # 要約生成とURL抽出を並行実行
    summary_task = summarize_channel_messages_async(channel_name, messages, past_context)
    urls = extract_all_urls_from_messages(messages)
    
    summary = await summary_task
    
    print(f"[DEBUG]   要約完了: {len(summary)} 文字")
    if urls:
        print(f"[DEBUG]   → {len(urls)}件のURLを検出")
    
    return channel_name, summary, urls


async def generate_daily_report_async(
    oldest: Optional[float] = None,
    latest: Optional[float] = None
) -> Dict:
    """
    日報を非同期で生成してNotionに投稿

    Args:
        oldest: 開始時刻（UNIXタイムスタンプ）、Noneの場合はデフォルト
        latest: 終了時刻（UNIXタイムスタンプ）、Noneの場合は現在時刻

    Returns:
        処理結果の辞書
    """
    print("[DEBUG] generate_daily_report_async() 開始")

    # 時刻範囲を取得（パラメータがない場合はデフォルト）
    print("[DEBUG] 時刻範囲を取得中...")
    if oldest is None or latest is None:
        oldest, latest = get_today_range()
    print(f"[DEBUG] 時刻範囲: {oldest} - {latest}")
    
    # 全チャンネルのメッセージを非同期で取得（過去日報も並行取得）
    print("[DEBUG] Slackメッセージと過去日報を取得中...")
    messages_task = fetch_all_channels_messages_async(oldest, latest)
    past_context_task = fetch_recent_reports_async(days=3)
    
    # 過去日報取得は失敗しても処理を続行
    try:
        past_context = await past_context_task
    except Exception as e:
        print(f"[WARNING] 過去日報の取得に失敗しました（無視して続行）: {e}")
        past_context = ""
    
    messages = await messages_task
    print(f"[DEBUG] 取得したメッセージ数: {len(messages)}")
    if past_context:
        print(f"[DEBUG] 過去日報のコンテキスト: {len(past_context)} 文字")
    else:
        print("[DEBUG] 過去日報のコンテキストなし（初回実行または取得失敗）")
    
    if not messages:
        print("[WARNING] メッセージが見つかりませんでした")
        return {
            "status": "no_messages",
            "message": "メッセージが見つかりませんでした"
        }
    
    # チャンネルごとにグループ化
    print("[DEBUG] チャンネルごとにグループ化中...")
    channel_messages = group_messages_by_channel(messages)
    print(f"[DEBUG] グループ化されたチャンネル数: {len(channel_messages)}")
    
    # チャンネルごとに並列処理
    print("[DEBUG] チャンネルごとに並列処理中...")
    tasks = [
        process_channel_async(channel_name, msgs, past_context)
        for channel_name, msgs in channel_messages.items()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 結果を整理
    channel_summaries = {}
    channel_urls = {}
    
    for result in results:
        if isinstance(result, Exception):
            print(f"[ERROR] チャンネル処理中にエラー: {result}")
            continue
        
        channel_name, summary, urls = result
        print(f"[DEBUG] チャンネル要約取得: {channel_name} - {len(summary)} 文字")
        channel_summaries[channel_name] = summary
        if urls:
            channel_urls[channel_name] = urls
    
    # channel_summariesの確認
    print(f"[DEBUG] 要約取得件数: {len(channel_summaries)}件")
    if not channel_summaries:
        print("[WARNING] 要約が1件も取得できませんでした")
        return {
            "status": "error",
            "message": "全てのチャンネルで要約生成に失敗しました",
            "channels_processed": 0
        }
    
    # Notionに並列投稿
    print("[DEBUG] Notionに投稿中...")
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[DEBUG] 日付: {today}")
    
    notion_results = await create_multiple_reports_async(
        today, 
        channel_summaries, 
        channel_urls
    )
    
    print(f"[DEBUG] Notion投稿結果: {len(notion_results)}件")
    
    # 結果表示
    for result in notion_results:
        status = "成功" if result['success'] else "失敗"
        print(f"[DEBUG]   - {result['channel']}: {status}")
    
    print("[DEBUG] generate_daily_report_async() 完了")
    
    return {
        "status": "success",
        "message": "日報生成が完了しました",
        "channels_processed": len(channel_summaries),
        "notion_results": notion_results
    }
