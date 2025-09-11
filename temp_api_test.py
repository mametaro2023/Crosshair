import requests

from crosshair_app.config import load_api_key

YOUR_API_KEY = load_api_key()  # Replace with your actual API key
PLAYER_UID = "1006594244470" # Replace with the player's UID
PLATFORM = "PC"  # Options: PC, PS4, X1
PLAYER_NAME = "mametaro2022"  # Replace with the player's name
ACTION = "add"

url = f"https://api.mozambiquehe.re/bridge?auth={YOUR_API_KEY}&uid={PLAYER_UID}&platform={PLATFORM}"
# https://api.mozambiquehe.re/games?auth={YOUR_API_KEY}&uid={PLAYER_UID}
# https://api.mozambiquehe.re/nametouid?auth={YOUR_API_KEY}&player={PLAYER_NAME}&platform={PLATFORM}
# https://api.mozambiquehe.re/bridge?auth={YOUR_API_KEY}&uid={PLAYER_UID}&platform={PLATFORM}
# https://api.mozambiquehe.re/bridge?auth={YOUR_API_KEY}&uid={PLAYER_UID}&platform={PLATFORM}&history=1&action={ACTION}

print(f"Attempting to fetch data from: {url}")

try:
    response = requests.get(url)
    print("Raw API Response:")
    print(response.text)
    response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
    data = response.json()
    print("API Response:")
    import json
    print(json.dumps(data, indent=4))
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")