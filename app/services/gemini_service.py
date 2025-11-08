"""Gemini API Service - Async version"""
import google.generativeai as genai
from typing import List, Dict
from app.core.config import settings
from utils.formatter import format_slack_events


# Gemini APIの設定
genai.configure(api_key=settings.GEMINI_API_KEY)


async def summarize_with_gemini_async(formatted_text: str) -> str:
    """
    Gemini APIを使って作業内容を非同期で要約
    
    Args:
        formatted_text: フォーマットされたSlackメッセージ
        
    Returns:
        要約された日報テキスト
    """
    import asyncio
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
以下は今日のSlackでの作業メモです。
これを元に、Notionに直接貼れる「日報形式のMarkdown」で要約してください。

【フォーマット指定】
- 必ず以下の3つの見出し構造で出力してください。
- 各見出しはMarkdownの見出し記法（##, ###）で明示。
- 箇条書きには `-` を使用してください。
- フォーマット以外の余計な説明は一切不要です。

## 今日の作業内容
### 話題1（短いタイトルをつける）
- 箇条書き内容

### 話題2
- 箇条書き内容

## 得られた知見
### 話題1
- 箇条書き内容

### 話題2
- 箇条書き内容

## 次回の予定候補
- 箇条書き内容

【Slackメッセージ】
{formatted_text}
"""
    
    # 非同期実行（CPUバウンドな処理をスレッドプールで実行）
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, model.generate_content, prompt)
    
    return response.text


async def summarize_channel_messages_async(channel_name: str, messages: List[Dict]) -> str:
    """
    特定チャンネルのメッセージを非同期で要約
    
    Args:
        channel_name: チャンネル名
        messages: メッセージのリスト
        
    Returns:
        要約された日報テキスト
    """
    formatted_text = format_slack_events(messages)
    summary = await summarize_with_gemini_async(formatted_text)
    
    return summary
