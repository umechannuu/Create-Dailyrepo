"""Google Gemini API クライアント"""
import os
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv
from utils.formatter import format_slack_events


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)


def summarize_with_gemini(formatted_text: str) -> str:
    """
    Gemini APIを使って作業内容を要約
    
    Args:
        formatted_text: フォーマットされたSlackメッセージ
        
    Returns:
        要約された日報テキスト
    """
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

    
    response = model.generate_content(prompt)
    return response.text


def summarize_channel_messages(channel_name: str, messages: List[Dict]) -> str:
    """
    特定チャンネルのメッセージを要約
    
    Args:
        channel_name: チャンネル名
        messages: メッセージのリスト
        
    Returns:
        要約された日報テキスト
    """    
    formatted_text = format_slack_events(messages)
    summary = summarize_with_gemini(formatted_text)
    
    return summary
