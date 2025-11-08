"""Notion API Service - Async version"""
import httpx
from typing import Dict, List, Optional
from app.core.config import settings


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
        # 通常テキスト
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                }
            })
    return blocks


async def post_daily_report_to_notion_async(
    date: str,
    channel_name: str,
    summary: str,
    urls: Optional[List[str]] = None
) -> Optional[Dict]:
    """
    Notionに日報ページを非同期で作成
    
    Args:
        date: 日付（YYYY-MM-DD）
        channel_name: Slackチャンネル名
        summary: GeminiからのMarkdown形式サマリ
        urls: 参考URLリスト（オプション）
        
    Returns:
        作成されたNotionページの情報（失敗時はNone）
    """
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    tag_name = settings.CHANNEL_TAG_MAP.get(channel_name, channel_name)
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
        "parent": {"database_id": settings.NOTION_DB_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "タグ": {"multi_select": [{"name": tag_name}]}
        },
        "children": children
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"[SUCCESS] Notionページ作成成功: {title}")
        return response.json()
    else:
        print(f"[ERROR] Notionページ作成失敗: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


async def create_multiple_reports_async(
    date: str,
    channel_summaries: Dict[str, str],
    channel_urls: Optional[Dict[str, List[str]]] = None
) -> List[Dict]:
    """
    複数チャンネルの日報を非同期で一括作成
    
    Args:
        date: 日付（YYYY-MM-DD）
        channel_summaries: チャンネル名をキーとした要約の辞書
        channel_urls: チャンネル名をキーとしたURLリストの辞書
        
    Returns:
        作成結果のリスト
    """
    import asyncio
    
    tasks = []
    for channel_name, summary in channel_summaries.items():
        urls = channel_urls.get(channel_name) if channel_urls else None
        task = post_daily_report_to_notion_async(date, channel_name, summary, urls)
        tasks.append((channel_name, task))
    
    results = []
    for channel_name, task in tasks:
        result = await task
        results.append({
            'channel': channel_name,
            'success': result is not None,
            'result': result
        })
    
    return results
