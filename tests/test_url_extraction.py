"""URL抽出機能のテスト"""
from utils.formatter import extract_urls, extract_all_urls_from_messages

# テストケース1: 単純なURL
text1 = "今日はhttps://github.com/user/repoを見ました"
urls1 = extract_urls(text1)
print(f"テスト1: {urls1}")
assert urls1 == ['https://github.com/user/repo'], "テスト1失敗"

# テストケース2: 複数URL
text2 = "参考: https://example.com と https://docs.python.org を確認"
urls2 = extract_urls(text2)
print(f"テスト2: {urls2}")
assert len(urls2) == 2, "テスト2失敗"

# テストケース3: URLなし
text3 = "URLは含まれていません"
urls3 = extract_urls(text3)
print(f"テスト3: {urls3}")
assert urls3 == [], "テスト3失敗"

# テストケース4: メッセージからの抽出
messages = [
    {
        'text': 'https://github.com/example',
        'urls': ['https://github.com/example']
    },
    {
        'text': 'https://docs.python.org',
        'urls': ['https://docs.python.org']
    },
    {
        'text': '重複: https://github.com/example',
        'urls': ['https://github.com/example']
    }
]
all_urls = extract_all_urls_from_messages(messages)
print(f"テスト4: {all_urls}")
assert len(all_urls) == 2, "テスト4失敗（重複排除）"

print("\n✓ すべてのURL抽出テストが成功しました！")
