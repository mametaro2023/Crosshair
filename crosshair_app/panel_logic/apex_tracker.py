
import time
import threading
import requests
from PyQt5 import QtCore

class ApexTracker(QtCore.QObject):
    # Signals to communicate with the GUI thread
    data_updated = QtCore.pyqtSignal(dict)
    error_occurred = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = "97e0ee7baafc1182f0679b24f02623c8" # From test.py
        self.base_url = "https://api.mozambiquehe.re/bridge"
        self.platform = "PC"
        self.username = ""
        self.last_score = None
        self._is_running = False
        self._thread = None

    def set_credentials(self, platform, username):
        self.platform = platform
        self.username = username

    def start_tracking(self):
        if self._is_running:
            return
        if not self.username:
            self.error_occurred.emit("ユーザー名が入力されていません。")
            return

        self.last_score = None
        self._is_running = True
        self._thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self._thread.start()

    def stop_tracking(self):
        self._is_running = False

    def _tracking_loop(self):
        initial_data_fetched = False
        while self._is_running:
            try:
                headers = {"Authorization": self.api_key}
                params = {"platform": self.platform, "player": self.username}
                response = requests.get(self.base_url, headers=headers, params=params, timeout=10)

                if not self._is_running:
                    break

                if response.status_code == 200:
                    data = response.json()
                    if data.get("Error"): # API can return 200 with an error message
                        if not initial_data_fetched:
                            self.error_occurred.emit(f'APIエラー: {data["Error"]}')
                            break # Stop tracking if initial fetch fails
                        else:
                            print(f'Apex Tracker: API Error - {data["Error"]}') # Log subsequent errors
                    
                    else:
                        rank_info = data.get("global", {}).get("rank", {})
                        current_score = rank_info.get("rankScore")

                        if current_score is not None:
                            if self.last_score is None or current_score != self.last_score:
                                update_payload = {
                                    "current_score": current_score,
                                    "last_score": self.last_score,
                                    "rank_name": rank_info.get("rankName"),
                                    "rank_div": rank_info.get("rankDiv")
                                }
                                self.data_updated.emit(update_payload)
                                self.last_score = current_score
                            initial_data_fetched = True # Mark as successful
                        elif not initial_data_fetched:
                            # This can happen if the player has no rank data yet
                            self.error_occurred.emit("ランクデータが見つかりません。ランクマッチをプレイしていますか？")
                            break

                else:
                    if not initial_data_fetched:
                        self.error_occurred.emit(f"APIサーバーエラー: {response.status_code}")
                        break # Stop tracking
                    else:
                        print(f"Apex Tracker: API Error - {response.status_code}")

            except requests.exceptions.RequestException as e:
                if not initial_data_fetched:
                    self.error_occurred.emit(f"ネットワークエラー: {e}")
                    break # Stop tracking
                else:
                    print(f"Apex Tracker: Network Error - {e}")
            
            # Wait for 30 seconds, but check for stop signal every second
            for _ in range(30):
                if not self._is_running:
                    break
                time.sleep(1)
        
        self._is_running = False
