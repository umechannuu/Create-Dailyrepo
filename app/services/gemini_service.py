"""Gemini API Service - Async version with structured output"""
import google.generativeai as genai
from typing import List, Dict, Optional
from app.core.config import settings
from app.models.report import DailyReport
from utils.formatter import format_slack_events


# Gemini APIの設定
# モジュールロード時に事前初期化（コールドスタート対策）
genai.configure(api_key=settings.GEMINI_API_KEY)

# Gemini APIが受け入れるスキーマ定義（辞書形式）
# Pydanticモデルの$defs/$ref/title/default等は非対応のため、直接定義
DAILY_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "work_content": {
            "type": "array",
            "description": "今日の作業内容。複数の話題に分けて記載",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "話題のタイトル"},
                    "items": {
                        "type": "array",
                        "description": "箇条書き項目のリスト",
                        "items": {"type": "string"}
                    }
                },
                "required": ["title", "items"]
            }
        },
        "insights": {
            "type": "array",
            "description": "得られた知見。複数の話題に分けて記載",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "話題のタイトル"},
                    "items": {
                        "type": "array",
                        "description": "箇条書き項目のリスト",
                        "items": {"type": "string"}
                    }
                },
                "required": ["title", "items"]
            }
        },
        "next_tasks": {
            "type": "array",
            "description": "次回の予定候補のリスト",
            "items": {"type": "string"}
        },
        "suggested_todos": {
            "type": "array",
            "description": "AIが提案する具体的なTODO項目",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "TODO項目のタイトル"},
                    "priority": {"type": "string", "description": "優先度（高・中・低のいずれか）"},
                    "estimated_time": {"type": "string", "description": "想定所要時間。不明なら空文字"},
                    "related_topic": {"type": "string", "description": "関連する話題。不明なら空文字"},
                    "deadline": {"type": "string", "description": "期限。不明なら空文字"}
                },
                "required": ["title", "priority", "estimated_time", "related_topic", "deadline"]
            }
        },
        "unfinished_tasks": {
            "type": "array",
            "description": "今日完了しなかった作業のリスト。なければ空リスト",
            "items": {"type": "string"}
        }
    },
    "required": ["work_content", "insights", "next_tasks", "suggested_todos", "unfinished_tasks"]
}


async def summarize_with_gemini_async(
    formatted_text: str,
    past_context: Optional[str] = None
) -> str:
    """
    Gemini APIを使って作業内容を非同期で要約（Structured Output使用）
    
    Args:
        formatted_text: フォーマットされたSlackメッセージ
        past_context: 過去の日報テキスト（オプション）
        
    Returns:
        要約された日報テキスト（Markdown形式）
    """
    import asyncio
    
    # Structured outputを使用してモデルを設定（辞書形式スキーマ）
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": DAILY_REPORT_SCHEMA,
        }
    )
    
    # 過去の日報コンテキストを構築
    past_context_section = ""
    past_analysis_instructions = ""
    if past_context:
        past_context_section = f"""
【過去の日報（参考）】
{past_context}
"""
        past_analysis_instructions = """
5. 過去の日報で未完了だったタスクの進捗を確認
6. 継続作業の文脈を維持し、過去との関連性を踏まえて記載
7. 過去の日報と重複する内容は簡潔にまとめる"""
    
    prompt = f"""
あなたは優秀なプロジェクトマネージャーです。
以下のSlackでの作業メモを分析し、日報とTODO提案を作成してください。

【今日のSlackメッセージ】
{formatted_text}
{past_context_section}
【分析指示】
1. 今日の作業内容を話題ごとに整理
2. 得られた知見を抽出
3. 未完了の作業を特定
4. 次回の作業として必要なTODOを具体的に提案{past_analysis_instructions}

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
- unfinished_tasks: 今日完了しなかった作業（なければ空リスト）
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
        raise



async def summarize_channel_messages_async(
    channel_name: str,
    messages: List[Dict],
    past_context: Optional[str] = None
) -> str:
    """
    特定チャンネルのメッセージを非同期で要約
    
    Args:
        channel_name: チャンネル名
        messages: メッセージのリスト
        past_context: 過去の日報テキスト（オプション）
        
    Returns:
        要約された日報テキスト
    """
    formatted_text = format_slack_events(messages)
    summary = await summarize_with_gemini_async(formatted_text, past_context)
    
    return summary
