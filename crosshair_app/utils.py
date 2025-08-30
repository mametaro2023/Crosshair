import sys
import os
import json
import threading
import time
from urllib import request
import tempfile # 追加
import subprocess # 追加
import zipfile # 追加
from PyQt5 import QtCore, QtWidgets
import ctypes
from packaging.version import Version

try:
    import psutil
except ImportError:
    psutil = None

IS_WINDOWS = os.name == 'nt'
if IS_WINDOWS:
    import winreg

APP_NAME = "Crosshair"
GAME_PROCESS_NAMES = ["r5apex.exe", "r5apex_dx12.exe"]

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

def download_mame_png_if_missing(parent_widget=None):
    """mame.pngが存在しない場合にGitHubからダウンロードする"""
    if os.path.exists("mame.png"):
        return

    def download_task(msg_box_to_close=None):
        url = "https://raw.githubusercontent.com/mametaro2023/Crosshair/main/mame.png"
        try:
            with request.urlopen(url) as response, open("mame.png", 'wb') as out_file:
                if response.status == 200:
                    out_file.write(response.read())
                    print("mame.png のダウンロードが完了しました。")
                    if parent_widget:
                        QtCore.QMetaObject.invokeMethod(parent_widget, "show_download_complete_message", QtCore.Qt.QueuedConnection)
                else:
                    raise Exception(f"サーバーエラー: {response.status}")
        except Exception as e:
            print(f"mame.png のダウンロードに失敗しました: {e}")
            if parent_widget:
                QtCore.QMetaObject.invokeMethod(parent_widget, "show_download_error_message", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, str(e)))
        finally:
            if msg_box_to_close:
                QtCore.QMetaObject.invokeMethod(msg_box_to_close, "accept", QtCore.Qt.QueuedConnection)

    if parent_widget:
        msg_box = QtWidgets.QMessageBox(parent_widget)
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setText("mame.png をダウンロードしています...")
        msg_box.setStandardButtons(QtWidgets.QMessageBox.NoButton) # ボタンを非表示
        msg_box.setModal(False)
        msg_box.show()
        
        # UIが固まらないように別スレッドでダウンロード
        thread = threading.Thread(target=download_task, args=(msg_box,))
        thread.daemon = True
        thread.start()
    else:
        # GUIがない場合のフォールバック
        download_task()

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
            current_state = any(p.name() in self.process_name for p in psutil.process_iter(['name']))
            if current_state != last_state:
                last_state = current_state # Update the local variable
                # UIの更新はCrosshairOverlayのset_master_enabledに任せる
                QtCore.QMetaObject.invokeMethod(self.overlay, "set_master_enabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, current_state), QtCore.Q_ARG(bool, False)) # manual_toggle=False を明示的に渡す
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
                if Version(latest_version_str) > Version(current_version_str):
                    if not data.get('assets'):
                        print("リリースにアセットが見つかりません。")
                        return None
                    
                    return {
                        "latest_version": latest_version_str,
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

def parse_valorant_crosshair_code(code):
    settings = {}
    tokens = code.split(';')

    # Predefined colors for 'c' parameter
    valorant_colors = {
        '1': '#00FF00', # Green
        '2': '#7FFF00', # Chartreuse
        '3': '#DFFF00', # Lime
        '4': '#FFFF00', # Yellow
        '5': '#00FFFF', # Cyan
        '6': '#FF00FF', # Magenta
        '7': '#FF0000', # Red
    }

    param_map = {
        'o': ('crosshair_outline_alpha', float),
        't': ('crosshair_outline_width', int),
        'a': ('dot_alpha', float), # Add this line for dot transparency
        'z': ('dot_radius', lambda x: int(float(x) / 2)), # Valorant 'z' is diameter, our 'dot_radius' is radius
        '0a': ('crosshair_inner_alpha', float), # Changed from crosshair_alpha to crosshair_inner_alpha
        '0l': ('crosshair_hline_length', int),
        '0v': ('crosshair_vline_length', int),
        '0o': ('crosshair_gap', int), # Corrected from '0g' to '0o'
        '0t': ('crosshair_thickness', int),
    }

    # Find the starting point of actual parameters
    start_index = 0
    if 'P' in tokens:
        try:
            p_index = tokens.index('P')
            start_index = p_index + 1 # Parameters start after 'P'
        except ValueError:
            pass # 'P' not found, start from beginning

    # Initialize crosshair color to default white
    settings['crosshair_color'] = '#FFFFFF'
    
    # Iterate through tokens in pairs (key, value)
    i = start_index
    while i < len(tokens) - 1:
        key = tokens[i]
        value_str = tokens[i+1]

        if key == 'c':
            try:
                color_code = value_str
                if color_code in valorant_colors:
                    settings['crosshair_color'] = valorant_colors[color_code]
                elif color_code == '8':
                    # Custom color, next token should be 'u' and its value
                    if i + 2 < len(tokens) and tokens[i+2] == 'u':
                        custom_hex = tokens[i+3]
                        
                        # If the hex code is longer than 6 characters, assume the extra characters are alpha
                        # and take only the first 6 characters for the color part (RRGGBB).
                        # This handles cases like B045B0F (7 chars) or FFC7FFFF (8 chars)
                        if len(custom_hex) > 6:
                            custom_hex_color_part = custom_hex[:6]
                        else:
                            custom_hex_color_part = custom_hex # Use as is if 6 or fewer characters

                        # Ensure it's a valid hex color (RRGGBB format)
                        if len(custom_hex_color_part) == 6 and all(c in '0123456789abcdefABCDEF' for c in custom_hex_color_part.lower()):
                            settings['crosshair_color'] = '#' + custom_hex_color_part
                        i += 2 # Skip 'u' and its value
                # Move to next pair
                i += 2
                continue
            except (ValueError, IndexError):
                # Malformed color code, ignore and move on
                i += 2
                continue
        
        if key in param_map:
            internal_key, convert_func = param_map[key]
            try:
                settings[internal_key] = convert_func(value_str)
            except ValueError:
                # Ignore invalid values
                pass
        
        # Move to next pair
        i += 2

    # Handle dot visibility 'd'
    settings['dot_visible'] = False # Default to hidden
    if 'd' in tokens:
        try:
            d_index = tokens.index('d')
            if d_index + 1 < len(tokens) and tokens[d_index + 1] == '1':
                settings['dot_visible'] = True
        except ValueError:
            pass # 'd' not found as a key, already defaulted to False

    # Handle 0v default to 0l if 0v is not present
    if 'crosshair_hline_length' in settings and 'crosshair_vline_length' not in settings:
        settings['crosshair_vline_length'] = settings['crosshair_hline_length']

    # Handle 0t default to 2 if 0t is not present
    if 'crosshair_thickness' not in settings:
        settings['crosshair_thickness'] = 2

    # Handle crosshair outline visibility 'h'
    settings['crosshair_outline_enabled'] = True # Default to visible
    if 'h' in tokens:
        try:
            h_index = tokens.index('h')
            if h_index + 1 < len(tokens) and tokens[h_index + 1] == '0':
                settings['crosshair_outline_enabled'] = False
        except ValueError:
            pass # 'h' not found as a key, already defaulted to True

    # Set crosshair_alpha to 1.0 if no advanced crosshair parameters are present
    advanced_crosshair_params = ['crosshair_hline_length', 'crosshair_vline_length', 'crosshair_gap', 'crosshair_thickness']
    is_advanced_crosshair = any(param in settings for param in advanced_crosshair_params)

    if not is_advanced_crosshair:
        settings['crosshair_alpha'] = 1.0 # Set overall crosshair alpha to 1.0 for non-advanced crosshairs

    return settings