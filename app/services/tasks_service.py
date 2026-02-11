"""Cloud Tasks Service - 非同期タスク実行"""
import json
from typing import Optional
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
import os

from app.core.config import settings


def create_task_client():
    """Cloud Tasksクライアントを作成"""
    return tasks_v2.CloudTasksClient()


async def enqueue_report_generation(
    oldest: float,
    latest: float,
    range_description: str,
    response_url: Optional[str] = None
):
    """
    日報生成タスクをCloud Tasksキューに投入
    
    Args:
        oldest: 開始時刻（UNIXタイムスタンプ）
        latest: 終了時刻（UNIXタイムスタンプ）
        range_description: 期間の説明文
        response_url: Slack response URL
    """
    # 環境変数から設定を取得
    project = os.getenv("GCP_PROJECT")
    location = os.getenv("GCP_REGION", "asia-northeast1")
    queue = "daily-report-queue"
    
    if not project:
        print("[WARNING] GCP_PROJECT環境変数が未設定。Cloud Tasksをスキップします")
        return None
    
    # Cloud Tasksクライアント
    client = create_task_client()
    parent = client.queue_path(project, location, queue)
    
    # タスクのペイロード
    payload = {
        "oldest": oldest,
        "latest": latest,
        "range_description": range_description,
        "response_url": response_url
    }
    
    # HTTPリクエストとしてタスクを作成
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{os.getenv('CLOUD_RUN_URL', 'http://localhost:8080')}/tasks/generate-report",
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(payload).encode(),
        }
    }
    
    # タスクをキューに投入
    response = client.create_task(request={"parent": parent, "task": task})
    print(f"[INFO] Cloud Tasksにタスクを投入しました: {response.name}")
    
    return response
