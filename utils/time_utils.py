"""時刻関連のユーティリティ関数"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def get_jst_now():
    """JSTで現在時刻を取得"""
    jst = ZoneInfo('Asia/Tokyo')
    return datetime.now(jst)


def get_today_range():
    """現在時刻から18時間前までの開始時刻と終了時刻をUNIXタイムスタンプで取得"""
    jst = ZoneInfo('Asia/Tokyo')
    now = datetime.now(jst)
    
    # 18時間前
    start = now - timedelta(hours=18)
    # 現在時刻
    end = now
    
    return start.timestamp(), end.timestamp()


def get_yesterday_range():
    """昨日の開始時刻と終了時刻をUNIXタイムスタンプで取得"""
    jst = ZoneInfo('Asia/Tokyo')
    now = datetime.now(jst)
    yesterday = now - timedelta(days=1)
    
    # 昨日の0時
    start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    # 昨日の23:59:59
    end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return start.timestamp(), end.timestamp()


def format_timestamp(ts, fmt="%Y-%m-%d %H:%M:%S"):
    """UNIXタイムスタンプをJST時刻文字列に変換"""
    jst = ZoneInfo('Asia/Tokyo')
    dt = datetime.fromtimestamp(float(ts), tz=jst)
    return dt.strftime(fmt)


def get_time_range_by_hours(hours: int = 24):
    """
    指定した時間数の範囲でUNIXタイムスタンプを取得
    
    Args:
        hours: 現在時刻から遡る時間数（デフォルト: 24時間）
    
    Returns:
        (oldest, latest) のタプル（UNIXタイムスタンプ）
    """
    jst = ZoneInfo('Asia/Tokyo')
    now = datetime.now(jst)
    
    # 指定時間前
    start = now - timedelta(hours=hours)
    # 現在時刻
    end = now
    
    return start.timestamp(), end.timestamp()
