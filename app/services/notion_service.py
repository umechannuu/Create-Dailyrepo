"""Notion API Service - Async version"""
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo
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


async def _fetch_page_blocks_as_text(page_id: str) -> str:
    """
    Notionページのブロック内容をプレーンテキストとして取得
    
    Args:
        page_id: NotionページID
        
    Returns:
        ページ内容のプレーンテキスト（取得失敗時は空文字列）
    """
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params={"page_size": 100})
        
        if response.status_code != 200:
            print(f"[WARNING] ブロック取得失敗 (page_id={page_id}): {response.status_code}")
            return ""
        
        data = response.json()
        blocks = data.get("results", [])
        
        if not blocks:
            return ""
        
        lines = []
        for block in blocks:
            block_type = block.get("type", "")
            block_data = block.get(block_type, {})
            
            # rich_textからテキストを抽出
            rich_text = block_data.get("rich_text", [])
            text_content = "".join([rt.get("plain_text", "") for rt in rich_text])
            
            if not text_content:
                continue
            
            # ブロックタイプに応じたフォーマット
            if block_type == "heading_2":
                lines.append(f"## {text_content}")
            elif block_type == "heading_3":
                lines.append(f"### {text_content}")
            elif block_type == "bulleted_list_item":
                lines.append(f"- {text_content}")
            elif block_type == "numbered_list_item":
                lines.append(f"- {text_content}")
            else:
                lines.append(text_content)
        
        return "\n".join(lines)
        
    except Exception as e:
        print(f"[WARNING] ブロック取得中にエラー (page_id={page_id}): {e}")
        return ""


async def fetch_recent_reports_async(days: int = 3) -> str:
    """
    Notion DBから直近N日間の日報を取得し、過去の文脈テキストとして返す
    
    ページやセクションが存在しない場合も安全に空文字列を返す。
    
    Args:
        days: 取得する日数（デフォルト3日）
        
    Returns:
        過去日報のテキスト（ページが見つからない場合は空文字列）
    """
    jst = ZoneInfo("Asia/Tokyo")
    now = datetime.now(jst)
    
    # 対象期間の開始日（N日前の0時）
    start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    # 今日は除外（今日の分はこれから生成する）
    today = now.strftime("%Y-%m-%d")
    
    url = "https://api.notion.com/v1/databases/{}/query".format(settings.NOTION_DB_ID)
    headers = {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # タイトルに日付を含むページをフィルタ（日付降順）
    query_body = {
        "filter": {
            "property": "Name",
            "title": {
                "contains": ""
            }
        },
        "sorts": [
            {
                "property": "Name",
                "direction": "descending"
            }
        ],
        "page_size": 20
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=query_body)
        
        if response.status_code != 200:
            print(f"[WARNING] Notion DB検索失敗: {response.status_code}")
            return ""
        
        data = response.json()
        pages = data.get("results", [])
        
        if not pages:
            print("[INFO] 過去の日報ページが見つかりませんでした")
            return ""
        
        # 日付でフィルタリング（タイトルからYYYY-MM-DDを抽出）
        import re
        date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
        
        relevant_pages = []
        for page in pages:
            # ページタイトルを取得
            title_prop = page.get("properties", {}).get("Name", {})
            title_parts = title_prop.get("title", [])
            title = "".join([t.get("plain_text", "") for t in title_parts])
            
            # タイトルから日付を抽出
            date_match = date_pattern.search(title)
            if not date_match:
                continue
            
            page_date = date_match.group(1)
            
            # 今日のページは除外、対象期間内のみ含める
            if page_date >= today:
                continue
            if page_date < start_date:
                continue
            
            relevant_pages.append({
                "id": page["id"],
                "title": title,
                "date": page_date
            })
        
        if not relevant_pages:
            print("[INFO] 対象期間の過去日報が見つかりませんでした")
            return ""
        
        print(f"[INFO] 過去日報 {len(relevant_pages)} ページを取得中...")
        
        # 各ページのブロック内容を取得
        import asyncio
        
        context_sections = []
        for page_info in relevant_pages:
            content = await _fetch_page_blocks_as_text(page_info["id"])
            if content:
                context_sections.append(
                    f"--- {page_info['title']} ---\n{content}"
                )
            else:
                print(f"[INFO] ページ内容が空です: {page_info['title']}")
        
        if not context_sections:
            print("[INFO] 過去日報の内容を取得できませんでした")
            return ""
        
        result = "\n\n".join(context_sections)
        print(f"[INFO] 過去日報の文脈テキスト: {len(result)} 文字")
        return result
        
    except Exception as e:
        print(f"[WARNING] 過去日報の取得中にエラー: {e}")
        return ""
