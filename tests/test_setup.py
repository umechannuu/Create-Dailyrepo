"""環境変数とインポートのテスト"""
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

print("=== 環境変数チェック ===")
print(f"SLACK_TOKEN: {'設定済み' if os.getenv('SLACK_TOKEN') else '未設定'}")
print(f"GEMINI_API_KEY: {'設定済み' if os.getenv('GEMINI_API_KEY') else '未設定'}")
print(f"NOTION_TOKEN: {'設定済み' if os.getenv('NOTION_TOKEN') else '未設定'}")
print(f"NOTION_DB_ID: {'設定済み' if os.getenv('NOTION_DB_ID') else '未設定'}")
print(f"PORT: {os.getenv('PORT', '8080')}")

print("\n=== パッケージチェック ===")
try:
    import flask
    print("✓ Flask")
except ImportError:
    print("✗ Flask")

try:
    import requests
    print("✓ requests")
except ImportError:
    print("✗ requests")

try:
    import google.generativeai
    print("✓ google-generativeai")
except ImportError:
    print("✗ google-generativeai")

print("\n=== モジュールチェック ===")
try:
    from slack_client import fetch_slack_messages
    print("✓ slack_client")
except ImportError as e:
    print(f"✗ slack_client: {e}")

try:
    from gemini_client import summarize_with_gemini
    print("✓ gemini_client")
except ImportError as e:
    print(f"✗ gemini_client: {e}")

try:
    from notion_client import post_daily_report_to_notion
    print("✓ notion_client")
except ImportError as e:
    print(f"✗ notion_client: {e}")

try:
    from utils.formatter import format_slack_events
    print("✓ utils.formatter")
except ImportError as e:
    print(f"✗ utils.formatter: {e}")

try:
    from utils.time_utils import get_today_range
    print("✓ utils.time_utils")
except ImportError as e:
    print(f"✗ utils.time_utils: {e}")

print("\n✓ すべてのチェックが完了しました")
