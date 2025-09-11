import requests
import json
from config import load_api_key

# APIエンドポイントのURL
# 例: PCプラットフォームのプレイヤー 'mametaro2022' の情報を取得
url = "https://api.mozambiquehe.re/bridge?platform=PC&player=mametaro2022"

# リクエストヘッダー
headers = {
    "Authorization": load_api_key()
}

try:
    # GETリクエストを送信
    response = requests.get(url, headers=headers)

    # レスポンスのステータスコードを確認
    if response.status_code == 200:
        # レスポンスのJSONをパース
        data = response.json()
        # パースしたデータをファイルに保存（見やすくするためにインデント）
        with open("api_response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("API response saved to api_response.json")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
