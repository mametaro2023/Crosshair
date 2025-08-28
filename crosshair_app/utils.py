import sys
import os
import json
import threading
import time
from urllib import request
import tempfile # 追加
import subprocess # 追加
import zipfile # 追加

try:
    import psutil
except ImportError:
    psutil = None

IS_WINDOWS = os.name == 'nt'
if IS_WINDOWS:
    import winreg

APP_NAME = "Crosshair"
GAME_PROCESS_NAME = "r5apex.exe"

def get_executable_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(sys.argv[0])

def is_in_startup(name):
    if not IS_WINDOWS: return False
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, name)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"スタートアップの確認中にエラー: {e}")
        return False

def add_to_startup(name, path):
    if not IS_WINDOWS: return False
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, f'"{path}"')
        return True
    except Exception as e:
        print(f"スタートアップへの追加中にエラー: {e}")
        return False

def remove_from_startup(name):
    if not IS_WINDOWS: return False
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.DeleteValue(key, name)
        return True
    except FileNotFoundError:
        return True # Already removed
    except Exception as e:
        print(f"スタートアップからの削除中にエラー: {e}")
        return False

def is_admin():
    if not IS_WINDOWS: return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class GameMonitorThread(threading.Thread):
    def __init__(self, process_name, overlay):
        super().__init__()
        self.process_name = process_name
        self.overlay = overlay
        self.running = True
        self.daemon = True

    def run(self):
        last_state = False
        while self.running:
            current_state = any(p.name() == self.process_name for p in psutil.process_iter(['name']))
            if current_state != last_state:
                self.overlay.panel.on_game_state_changed(current_state)
                last_state = current_state
            time.sleep(2)
        self.overlay.panel.on_monitor_thread_finished()

    def stop(self):
        self.running = False
        
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

from distutils.version import LooseVersion

def check_for_updates(current_version):
    """GitHubリリースページをチェックして新しいバージョンがないか確認する"""
    # TODO: ユーザーのGitHubリポジトリに合わせて変更する
    url = "https://api.github.com/repos/mametaro2023/Crosshair/releases/latest"
    try:
        with request.urlopen(url) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                tag_name = data['tag_name']

                # 'ver' プレフィックスを削除して比較
                latest_version_str = tag_name.lstrip('ver')
                current_version_str = current_version.lstrip('ver')
                
                
                # バージョン比較
                if LooseVersion(latest_version_str) > LooseVersion(current_version_str):
                    if not data.get('assets'):
                        print("リリースにアセットが見つかりません。")
                        return None
                    
                    return {
                        "latest_version": latest_version,
                        "download_url": data['assets'][0]['browser_download_url'],
                        "release_notes": data['body']
                    }
    except Exception as e:
        print(f"アップデートの確認中にエラー: {e}")
    return None

def download_asset_with_progress(url, progress_callback):
    """アセットを一時フォルダにダウンロードし、進捗をコールバックする"""
    try:
        temp_dir = tempfile.gettempdir()
        filename = os.path.basename(url)
        save_path = os.path.join(temp_dir, filename)

        with request.urlopen(url) as response:
            total_size = int(response.getheader('Content-Length', 0))
            chunk_size = 8192
            bytes_read = 0
            with open(save_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_read += len(chunk)
                    if total_size > 0:
                        progress = int(bytes_read * 100 / total_size)
                        progress_callback(progress)
        return save_path
    except Exception as e:
        print(f"ダウンロードエラー: {e}")
        return None

def create_updater_script(new_asset_path, old_exe_path, new_exe_in_temp_path):
    """自己更新用のバッチファイルを生成する"""
    old_dir = os.path.dirname(old_exe_path)
    old_exe_name = os.path.basename(old_exe_path) # crosshair.exe

    script_path = os.path.join(tempfile.gettempdir(), "updater.bat")
    
    script_content = f"""
@echo off
echo アプリケーションを更新しています...
echo 終了処理を待機中...
taskkill /F /IM {old_exe_name} > NUL 2>&1
timeout /t 3 /nobreak > NUL

echo ファイルを更新しています...
rem 古い実行ファイルを削除
del "{old_exe_path}" > NUL 2>&1
rem 新しい実行ファイルをリネームして配置
move /Y "{new_exe_in_temp_path}" "{old_exe_path}"

echo 更新完了。アプリケーションを再起動します...
call "{old_exe_path}"

echo 一時ファイルをクリーンアップしています...
rem ZIPファイルと展開した一時ディレクトリを削除
del "{new_asset_path}" > NUL 2>&1
rmdir /S /Q "{os.path.dirname(new_exe_in_temp_path)}" > NUL 2>&1
del "%~f0" > NUL 2>&1
"""
    
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
        
    return script_path

def run_updater_and_exit(script_path):
    """バッチファイルを別プロセスで実行し、自身は終了する"""
    subprocess.Popen(f'"{script_path}"', shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
    sys.exit(0)

def extract_and_find_exe(zip_path):
    """ZIPファイルを一時ディレクトリに展開し、その中の実行ファイル（.exe）のパスを返す"""
    temp_extract_dir = os.path.join(tempfile.gettempdir(), os.urandom(8).hex()) # ユニークな一時ディレクトリ
    os.makedirs(temp_extract_dir)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        
        found_exe = None
        for root, _, files in os.walk(temp_extract_dir):
            for file in files:
                if file.lower().endswith('.exe'):
                    found_exe = os.path.join(root, file)
                    break
            if found_exe:
                break
        return found_exe
    except Exception as e:
        print(f"ZIP展開またはEXE検索エラー: {e}")
        return None
