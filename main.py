"""Slack → Gemini → Notion 自動日報生成システム"""
import os
import sys
import requests
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
from datetime import datetime

from slack_client import fetch_all_channels_messages
from gemini_client import summarize_channel_messages
from notion_client import create_multiple_reports
from utils.formatter import group_messages_by_channel
from utils.time_utils import get_today_range, get_yesterday_range

# 環境変数読み込み
load_dotenv()

# 標準出力のバッファリングを無効化（Cloud Runでログをリアルタイム表示）
sys.stdout.flush()

app = Flask(__name__)


@app.route("/slack/command", methods=["POST"])
def handle_slack_command():
    """Slackのスラッシュコマンドを処理（即座にレスポンス + バックグラウンド処理）"""
    import threading
    
    command = request.form.get("command")
    response_url = request.form.get("response_url")  
    
    if command != "/dailyreport":
        return jsonify({"text": "無効なコマンドです。"}), 400
    
    # バックグラウンドで処理を実行
    def background_task():
        try:
            print("[INFO] バックグラウンドで日報生成を開始...")
            sys.stdout.flush()
            generate_daily_report()
            print("[INFO] 日報生成が完了しました")
            sys.stdout.flush()
            
            # 完了通知をSlackに送信
            if response_url:
                completion_message = {
                    "text": "[SUCCESS] 日報生成が完了しました！Notionをご確認ください。",
                    "response_type": "in_channel"
                }
                requests.post(response_url, json=completion_message)
                
        except Exception as e:
            print(f"[ERROR] エラーが発生: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            
            # エラー通知をSlackに送信
            if response_url:
                error_message = {
                    "text": f"[ERROR]エラーが発生しました: {str(e)}",
                    "response_type": "ephemeral"
                }
                requests.post(response_url, json=error_message)
    
    # スレッドを開始（daemon=Falseで完了まで実行）
    thread = threading.Thread(target=background_task)
    thread.daemon = False
    thread.start()
    
    # 即座にレスポンスを返す（3秒以内）
    return jsonify({
        "response_type": "in_channel",
        "text": "[INFO] 日報生成を開始しました。完了までしばらくお待ちください..."
    })


def generate_daily_report():
    """日報を生成してNotionに投稿"""
    print("[DEBUG] generate_daily_report() 開始")
    
    # 今日の範囲を取得
    print("[DEBUG] 時刻範囲を取得中...")
    oldest, latest = get_today_range()
    print(f"[DEBUG] 時刻範囲: {oldest} - {latest}")
    
    # 全チャンネルのメッセージ取得
    print("[DEBUG] Slackメッセージを取得中...")
    messages = fetch_all_channels_messages(oldest, latest)
    print(f"[DEBUG] 取得したメッセージ数: {len(messages)}")
    
    if not messages:
        print("[WARNING] メッセージが見つかりませんでした")
        return
    
    # チャンネルごとにグループ化
    print("[DEBUG] チャンネルごとにグループ化中...")
    channel_messages = group_messages_by_channel(messages)
    print(f"[DEBUG] グループ化されたチャンネル数: {len(channel_messages)}")
    
    # チャンネルごとに要約とURL抽出
    print("[DEBUG] Gemini APIで要約中...")
    channel_summaries = {}
    channel_urls = {}
    
    for channel_name, msgs in channel_messages.items():
        print(f"[DEBUG] - {channel_name}: {len(msgs)}件のメッセージを処理中")
        
        try:
            # 要約生成
            print(f"[DEBUG]   要約を生成中...")
            summary = summarize_channel_messages(channel_name, msgs)
            channel_summaries[channel_name] = summary
            print(f"[DEBUG]   要約完了: {len(summary)} 文字")
            
            # URLを抽出
            from utils.formatter import extract_all_urls_from_messages
            urls = extract_all_urls_from_messages(msgs)
            if urls:
                channel_urls[channel_name] = urls
                print(f"[DEBUG]   → {len(urls)}件のURLを検出")
        except Exception as e:
            print(f"[ERROR] {channel_name} の処理中にエラー: {e}")
            import traceback
            traceback.print_exc()
    
    # Notionに投稿
    print("[DEBUG] Notionに投稿中...")
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[DEBUG] 日付: {today}")
    
    try:
        results = create_multiple_reports(today, channel_summaries, channel_urls)
        print(f"[DEBUG] Notion投稿結果: {len(results)}件")
        
        # 結果表示
        for result in results:
            status = "成功" if result['success'] else "失敗"
            print(f"[DEBUG]   - {result['channel']}: {status}")
    except Exception as e:
        print(f"[ERROR] Notion投稿中にエラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("[DEBUG] generate_daily_report() 完了")


@app.route("/", methods=["GET"])
def index():
    """ヘルスチェック用エンドポイント"""
    return jsonify({
        "status": "ok",
        "message": "Daily Report Bot is running"
    })


@app.route("/test", methods=["GET"])
def test_generation():
    """テスト用エンドポイント（手動で日報生成）"""
    try:
        generate_daily_report()
        return jsonify({
            "status": "success",
            "message": "日報生成が完了しました"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
