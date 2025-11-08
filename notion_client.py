"""
Notion API クライアント
Gemini出力(Markdown形式)をNotionページに綺麗に登録する
"""

import os
import re
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")

# Slackチャンネル名 → Notionタグ
CHANNEL_TAG_MAP = {
    "作業-研究": "研究",
    "作業-epic": "EpicAI",
    "作業-kaggle": "kaggle",
    "作業-個人": "個人作業"
}



def create_notion_blocks_from_markdown(summary: str) -> List[Dict]:
    """
    Gemini出力(Markdown形式)からNotionブロックを生成する
    """
    blocks = []

    for line in summary.splitlines():
        line = line.strip()
        if not line:
            continue

        # セクション見出し
        if line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line[3:].strip()}}]
                }
            })
        # サブ見出し
        elif line.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": line[4:].strip()}}]
                }
            })
        # 箇条書き
        elif line.startswith("- "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]
                }
            })
        # 通常テキスト(geminiのブロック生成が上手くいかない場合に使用する)
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                }
            })
    return blocks


def post_daily_report_to_notion(
    date: str,
    channel_name: str,
    summary: str,
    urls: Optional[List[str]] = None
):
    """
    Notionに日報ページを作成
    
    Args:
        date: 日付（YYYY-MM-DD）
        channel_name: Slackチャンネル名
        summary: GeminiからのMarkdown形式サマリ
        urls: 参考URLリスト（オプション）
    """
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    tag_name = CHANNEL_TAG_MAP.get(channel_name, channel_name)
    title = f"{date} - {channel_name}"

    # Markdown → Notionブロック化
    children = create_notion_blocks_from_markdown(summary)

    if urls:
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "参考文献"}}]
            }
        })
        for url_item in urls:
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": url_item, "link": {"url": url_item}}
                        }
                    ]
                }
            })

    data = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "タグ": {"multi_select": [{"name": tag_name}]}
        },
        "children": children
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"✓ Notionページ作成成功: {title}")
        return response.json()
    else:
        print(f"✗ Notionページ作成失敗: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def create_multiple_reports(
    date: str,
    channel_summaries: Dict[str, str],
    channel_urls: Optional[Dict[str, List[str]]] = None
):
    results = []
    for channel_name, summary in channel_summaries.items():
        urls = channel_urls.get(channel_name) if channel_urls else None
        result = post_daily_report_to_notion(date, channel_name, summary, urls)
        results.append({
            'channel': channel_name,
            'success': result is not None,
            'result': result
        })
    return results
