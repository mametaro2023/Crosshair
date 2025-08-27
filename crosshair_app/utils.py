import sys
import os
from PyQt5 import QtCore

try:
    import psutil
except ImportError:
    psutil = None

try:
    import winreg
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

APP_NAME = "CrosshairOverlay"
GAME_PROCESS_NAME = "r5apex_dx12.exe"

def get_executable_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

def add_to_startup(app_name, path):
    if not IS_WINDOWS: return False
    try:
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as registry_key:
            winreg.SetValueEx(registry_key, app_name, 0, winreg.REG_SZ, path)
        return True
    except Exception as e:
        print(f"スタートアップ登録に失敗: {e}")
        return False

def remove_from_startup(app_name):
    if not IS_WINDOWS: return False
    try:
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE) as registry_key:
            winreg.DeleteValue(registry_key, app_name)
        return True
    except FileNotFoundError:
        return True
    except Exception as e:
        print(f"スタートアップからの削除に失敗: {e}")
        return False

def is_in_startup(app_name):
    if not IS_WINDOWS: return False
    try:
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_READ) as registry_key:
            winreg.QueryValueEx(registry_key, app_name)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False

class GameMonitorThread(QtCore.QThread):
    gameRunning = QtCore.pyqtSignal(bool)

    def __init__(self, process_name, parent=None):
        super().__init__(parent)
        self.process_name = process_name
        self.is_running = True
        self._game_is_running = False

    def run(self):
        if not psutil:
            print("psutilライブラリが見つかりません。ゲーム監視機能は無効です。")
            return

        try:
            initial_state = any(proc.info['name'] == self.process_name for proc in psutil.process_iter(['name']))
            if initial_state != self._game_is_running:
                self._game_is_running = initial_state
                self.gameRunning.emit(initial_state)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

        while self.is_running:
            self.sleep(5)
            try:
                found = any(proc.info['name'] == self.process_name for proc in psutil.process_iter(['name']))
                
                if found != self._game_is_running:
                    self._game_is_running = found
                    self.gameRunning.emit(found)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def stop(self):
        self.is_running = False
