import time
import requests
from PyQt5.QtCore import QObject, pyqtSignal, QThread

class StatsTracker(QObject):
    """
    Worker thread to fetch Apex Legends stats periodically.
    """
    stats_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, platform, player):
        super().__init__()
        self.api_key = load_api_key()
        self.platform = platform
        self.player = player
        self.is_running = False
        self._url = f"https://api.mozambiquehe.re/bridge?platform={platform}&player={player}"

    def run(self):
        self.is_running = True
        while self.is_running:
            try:
                response = requests.get(self._url, headers={"Authorization": self.api_key})
                if response.status_code == 200:
                    data = response.json()
                    if "Error" in data:
                        self.error_occurred.emit(data["Error"])
                        self.stop()
                    else:
                        self.stats_updated.emit(data)
                else:
                    error_msg = f"Error {response.status_code}: {response.text}"
                    self.error_occurred.emit(error_msg)
                    self.stop() # Stop on persistent errors
                
                # Wait for 30 seconds before next request
                for _ in range(30):
                    if not self.is_running:
                        break
                    time.sleep(1)

            except requests.exceptions.RequestException as e:
                self.error_occurred.emit(f"Network Error: {e}")
                self.stop()
    
    def stop(self):
        self.is_running = False
