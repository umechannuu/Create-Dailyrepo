"""Slack API クライアント"""
import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
from utils.formatter import extract_urls

load_dotenv()

SLACK_TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL_NAME_MAP = {
    "C09PT0PR0MV": "作業-研究",
    "C09QC16DAJY": "作業-epic",
    "C09Q6CYB8MU": "作業-kaggle",
    "C09R2PC3J7J": "作業-個人"
}


def fetch_slack_messages(channel_id: str, oldest: float, latest: float) -> List[Dict]:
    """
    指定したチャンネルの期間内のメッセージを取得
    
    Args:
        channel_id: Slackチャンネル・DMのID
        oldest: 開始時刻（UNIXタイムスタンプ）
        latest: 終了時刻（UNIXタイムスタンプ）
        
    Returns:
        メッセージのリスト
    """
    url = "https://slack.com/api/conversations.history"
    headers = {
        "Authorization": f"Bearer {SLACK_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "channel": channel_id,
        "oldest": oldest,
        "latest": latest,
        "limit": 1000
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if not data.get("ok"):
        print(f"Error fetching messages: {data.get('error')}")
        return []
    
    messages = data.get("messages", [])
    
    # 各メッセージにチャンネル名とURL情報を追加
    for msg in messages:
        msg['channel_name'] = CHANNEL_NAME_MAP.get(channel_id, channel_id)
        
        # テキストからURLを抽出
        text = msg.get('text', '')
        urls = extract_urls(text)
        if urls:
            msg['urls'] = urls
    
    return messages


def fetch_all_channels_messages(oldest: float, latest: float) -> List[Dict]:
    """
    すべての対象チャンネルからメッセージを取得
    
    Args:
        oldest: 開始時刻（UNIXタイムスタンプ）
        latest: 終了時刻（UNIXタイムスタンプ）
        
    Returns:
        全チャンネルのメッセージリスト
    """
    all_messages = []
    
    for channel_id in CHANNEL_NAME_MAP.keys():
        messages = fetch_slack_messages(channel_id, oldest, latest)
        all_messages.extend(messages)
    
    # 時刻順にソート
    all_messages.sort(key=lambda x: float(x.get('ts', 0)))
    
    return all_messages
