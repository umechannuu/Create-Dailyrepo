"""Slack API Service - Async version"""
import httpx
from typing import List, Dict
from app.core.config import settings
from utils.formatter import extract_urls


async def fetch_slack_messages_async(channel_id: str, oldest: float, latest: float) -> List[Dict]:
    """
    指定したチャンネルの期間内のメッセージを非同期で取得
    
    Args:
        channel_id: Slackチャンネル・DMのID
        oldest: 開始時刻（UNIXタイムスタンプ）
        latest: 終了時刻（UNIXタイムスタンプ）
        
    Returns:
        メッセージのリスト
    """
    url = "https://slack.com/api/conversations.history"
    headers = {
        "Authorization": f"Bearer {settings.SLACK_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "channel": channel_id,
        "oldest": oldest,
        "latest": latest,
        "limit": 1000
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        data = response.json()
    
    if not data.get("ok"):
        print(f"Error fetching messages from {channel_id}: {data.get('error')}")
        return []
    
    messages = data.get("messages", [])
    
    # 各メッセージにチャンネル名とURL情報を追加
    for msg in messages:
        msg['channel_name'] = settings.CHANNEL_NAME_MAP.get(channel_id, channel_id)
        
        # テキストからURLを抽出
        text = msg.get('text', '')
        urls = extract_urls(text)
        if urls:
            msg['urls'] = urls
    
    return messages


async def fetch_all_channels_messages_async(oldest: float, latest: float) -> List[Dict]:
    """
    すべての対象チャンネルからメッセージを非同期で取得
    
    Args:
        oldest: 開始時刻（UNIXタイムスタンプ）
        latest: 終了時刻（UNIXタイムスタンプ）
        
    Returns:
        全チャンネルのメッセージリスト
    """
    import asyncio
    
    # 全チャンネルを並列処理
    tasks = [
        fetch_slack_messages_async(channel_id, oldest, latest)
        for channel_id in settings.CHANNEL_NAME_MAP.keys()
    ]
    
    results = await asyncio.gather(*tasks)
    
    # 結果を統合
    all_messages = []
    for messages in results:
        all_messages.extend(messages)
    
    # 時刻順にソート
    all_messages.sort(key=lambda x: float(x.get('ts', 0)))
    
    return all_messages
