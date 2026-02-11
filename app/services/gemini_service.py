"""Gemini API Service - Async version with structured output"""
import google.generativeai as genai
from typing import List, Dict
from app.core.config import settings
from app.models.report import DailyReport
from utils.formatter import format_slack_events


# Gemini APIの設定
# モジュールロード時に事前初期化（コールドスタート対策）
genai.configure(api_key=settings.GEMINI_API_KEY)


async def summarize_with_gemini_async(formatted_text: str) -> str:
    """
    Gemini APIを使って作業内容を非同期で要約（Structured Output使用）
    
    Args:
        formatted_text: フォーマットされたSlackメッセージ
        
    Returns:
        要約された日報テキスト（Markdown形式）
    """
    import asyncio
    
    # Structured outputを使用してモデルを設定
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": DailyReport,
        }
    )
    
    prompt = f"""
あなたは優秀なプロジェクトマネージャーです。
以下のSlackでの作業メモを分析し、日報とTODO提案を作成してください。

【今日のSlackメッセージ】
{formatted_text}

【分析指示】
1. 今日の作業内容を話題ごとに整理
2. 得られた知見を抽出
3. 未完了の作業を特定
4. 次回の作業として必要なTODOを具体的に提案

【TODO提案の観点】
- 今日の作業の続きとして必要なこと
- 発見した課題の解決策
- 学んだことを活かす次のステップ
- 優先度（高・中・低）と所要時間も判断して付与

【出力形式】
以下の構造化されたJSONで出力してください：
- work_content: 今日の作業内容を話題ごとに整理
- insights: 得られた知見を話題ごとに整理
- next_tasks: 次回の予定候補（シンプルな箇条書き）
- suggested_todos: 具体的なTODO項目（title, priority, estimated_time, related_topic, deadline を含む）
- unfinished_tasks: 今日完了しなかった作業（あれば）
"""
    
    
    try:
        # 非同期実行（CPUバウンドな処理をスレッドプールで実行）
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, model.generate_content, prompt)
        
        print(f"[DEBUG] Gemini API レスポンス受信 - 長さ: {len(response.text)} 文字")
        
        # JSONレスポンスをPydanticモデルにパース
        report = DailyReport.model_validate_json(response.text)
        
        print(f"[DEBUG] Pydanticモデルパース成功")
        print(f"[DEBUG]   - work_content: {len(report.work_content)}件")
        print(f"[DEBUG]   - suggested_todos: {len(report.suggested_todos)}件")
        
        # Markdown形式に変換して返す
        markdown = report.to_markdown()
        print(f"[DEBUG] Markdown変換完了 - {len(markdown)} 文字")
        
        return markdown
        
    except Exception as e:
        print(f"[ERROR] Gemini処理中にエラー: {type(e).__name__}: {str(e)}")
        print(f"[ERROR] レスポンステキスト: {response.text if 'response' in locals() else 'レスポンス取得前'}")
        raise  # エラーを再送出して呼び出し元でキャッチ



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
