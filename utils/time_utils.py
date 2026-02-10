"""時刻関連のユーティリティ関数"""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
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


def parse_time_range(text: Optional[str]) -> Tuple[float, float, str]:
    """
    ユーザー入力から時間範囲をパース

    Args:
        text: ユーザー入力（None、時間数、または日時文字列）

    Returns:
        (oldest, latest, range_description) のタプル

    Examples:
        parse_time_range(None)                  -> 18時間前〜現在
        parse_time_range("6")                   -> 6時間前〜現在
        parse_time_range("2026-01-06 09:00")    -> 指定日時〜現在
        parse_time_range("2026-01-06")          -> 指定日0時〜現在
    """
    jst = ZoneInfo('Asia/Tokyo')
    now = datetime.now(jst)
    latest = now.timestamp()

    if not text or text.strip() == "":
        # デフォルト: 18時間前
        oldest = (now - timedelta(hours=18)).timestamp()
        return oldest, latest, "過去18時間"

    text = text.strip()

    # パターン1: 数字のみ（時間数）
    if re.match(r'^\d+$', text):
        hours = int(text)
        if hours < 1 or hours > 168:  # 1時間〜7日間
            raise ValueError(
                f"時間数は1〜168の範囲で指定してください（指定値: {hours}）"
            )
        oldest = (now - timedelta(hours=hours)).timestamp()
        return oldest, latest, f"過去{hours}時間"

    # パターン2: 日時指定（YYYY-MM-DD HH:MM）
    datetime_pattern = r'^(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})$'
    match = re.match(datetime_pattern, text)
    if match:
        date_str, hour, minute = match.groups()
        try:
            start_dt = datetime.strptime(
                f"{date_str} {int(hour):02d}:{minute}",
                "%Y-%m-%d %H:%M"
            ).replace(tzinfo=jst)

            if start_dt > now:
                raise ValueError("未来の日時は指定できません")
            if (now - start_dt).days > 7:
                raise ValueError("7日以上前の日時は指定できません")

            oldest = start_dt.timestamp()
            return oldest, latest, f"{date_str} {int(hour):02d}:{minute} 〜 現在"
        except ValueError as e:
            if "未来" in str(e) or "7日" in str(e):
                raise
            raise ValueError(f"日時形式が不正です: {text}")

    # パターン3: 日付のみ（YYYY-MM-DD）→ その日の0時から
    date_only_pattern = r'^(\d{4}-\d{2}-\d{2})$'
    if re.match(date_only_pattern, text):
        try:
            start_dt = datetime.strptime(text, "%Y-%m-%d").replace(
                hour=0, minute=0, second=0, tzinfo=jst
            )
            if start_dt > now:
                raise ValueError("未来の日付は指定できません")
            if (now - start_dt).days > 7:
                raise ValueError("7日以上前の日付は指定できません")

            oldest = start_dt.timestamp()
            return oldest, latest, f"{text} 00:00 〜 現在"
        except ValueError as e:
            if "未来" in str(e) or "7日" in str(e):
                raise
            raise ValueError(f"日付形式が不正です: {text}")

    raise ValueError(f"認識できない形式です: {text}")

