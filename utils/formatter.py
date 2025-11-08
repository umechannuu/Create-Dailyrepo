"""Slackメッセージをフォーマットするユーティリティ"""
import re
from utils.time_utils import format_timestamp


def extract_urls(text):
    """
    テキストからURLを抽出(正規表現)
    
    Args:
        text: メッセージテキスト
        
    Returns:
        list: 抽出されたURLのリスト
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]ぁ-ん々〆〤ァ-ヴー]+'
    urls = re.findall(url_pattern, text)
    return urls


def format_slack_events(messages):
    """
    Slackメッセージを時系列でフォーマット
    
    Args:
        messages: Slack APIから取得したメッセージのリスト
        
    Returns:
        str: フォーマットされたテキスト
    """
    if not messages:
        return "今日のメッセージはありませんでした。"
    
    # チャンネルごとにメッセージをグループ化
    channel_messages = {}
    
    for msg in messages:
        channel_name = msg.get('channel_name', 'その他')
        if channel_name not in channel_messages:
            channel_messages[channel_name] = []
        channel_messages[channel_name].append(msg)
    
    # フォーマット
    formatted_text = ""
    
    for channel_name, msgs in sorted(channel_messages.items()):
        formatted_text += f"\n\n## {channel_name}\n\n"
        
        for msg in sorted(msgs, key=lambda x: float(x.get('ts', 0))):
            timestamp = format_timestamp(msg.get('ts', 0), "%H:%M")
            text = msg.get('text', '').strip()
            
            # 添付ファイル情報
            files = msg.get('files', [])
            file_info = ""
            if files:
                file_names = [f.get('name', 'ファイル') for f in files]
                file_info = f" [添付: {', '.join(file_names)}]"
            
            # URL情報
            urls = msg.get('urls', [])
            url_info = ""
            if urls:
                url_info = f" [URL: {len(urls)}件]"
            
            formatted_text += f"- [{timestamp}] {text}{file_info}{url_info}\n"
    
    return formatted_text.strip()


def group_messages_by_channel(messages):
    """
    メッセージをチャンネルごとにグループ化
    
    Args:
        messages: Slack APIから取得したメッセージのリスト
        
    Returns:
        dict: チャンネル名をキーとしたメッセージの辞書
    """
    channel_messages = {}
    
    for msg in messages:
        channel_name = msg.get('channel_name', 'その他')
        if channel_name not in channel_messages:
            channel_messages[channel_name] = []
        channel_messages[channel_name].append(msg)
    
    return channel_messages


def extract_all_urls_from_messages(messages):
    """
    すべてのメッセージからURLを抽出（重複排除）
    
    Args:
        messages: メッセージのリスト
        
    Returns:
        list: ユニークなURLのリスト
    """
    all_urls = set()
    
    for msg in messages:
        urls = msg.get('urls', [])
        all_urls.update(urls)
    
    return sorted(list(all_urls))
