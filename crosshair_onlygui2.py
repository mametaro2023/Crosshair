import sys
import threading
import json
import os
import keyboard
from pynput import mouse
from PyQt5 import QtCore, QtGui, QtWidgets
try:
    import psutil
except ImportError:
    psutil = None
# OS固有の機能のために、OSを判定する
try:
    # Windowsレジストリを操作するためのライブラリ
    import winreg
    IS_WINDOWS = True
except ImportError:
    # winregがなければWindowsではないと判断
    IS_WINDOWS = False

# スタートアップ登録時に使用するアプリケーション名
APP_NAME = "CrosshairOverlay"
GAME_PROCESS_NAME = "r5apex_dx12.exe"

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".crosshair_config.json")
DEFAULT_PRESET_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "CrosshairPresets")
PRESET_EXTENSION = ".mametaro"

# --- Dark Theme Helpers -------------------------------------------------------

def apply_dark_theme(app: QtWidgets.QApplication) -> None:
    app.setStyle("Fusion")

    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(24, 26, 27))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(224, 224, 224))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(32, 34, 37))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(44, 47, 51))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(45, 47, 54))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(224, 224, 224))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(224, 224, 224))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(45, 47, 54))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(224, 224, 224))
    palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 0, 0))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 204, 102))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(12, 12, 12))
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor(0, 204, 204))
    app.setPalette(palette)

    # Global stylesheet for a sleek dark look
    app.setStyleSheet(
        """
        QWidget { color: #E0E0E0; font-family: 'Noto Sans JP', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }
        QDialog { background-color: #181A1B; }
        QMenuBar { background-color: #181A1B; color: #E0E0E0; border-bottom: 1px solid #2C2F33; }
        QMenuBar::item { spacing: 6px; padding: 6px 10px; background: transparent; }
        QMenuBar::item:selected { background: #2C2F33; border-radius: 4px; }
        QMenu { background-color: #202225; color: #E0E0E0; border: 1px solid #2C2F33; }
        QMenu::item { padding: 6px 16px; }
        QMenu::item:selected { background: #2C2F33; }

        QPushButton { background-color: #2D2F36; border: 1px solid #3C4048; padding: 8px 12px; border-radius: 6px; color: #E0E0E0; }
        QPushButton:hover { background-color: #3A3F47; }
        QPushButton:pressed { background-color: #2A2E36; }
        QPushButton[accent="true"] { background-color: #00b35a; border: 1px solid #1fd47b; color: #0b0b0b; }
        QPushButton[accent="true"]:hover { background-color: #00cc66; }
        QPushButton[accent="true"]:pressed { background-color: #00a34d; }

        QPushButton#masterToggleButton {
            background-color: #a12a2a; /* 無効化ボタンは赤系に */
            border: 1px solid #c24d4d;
            font-weight: bold;
            padding: 10px 12px; /* 少し縦に大きくする */
        }
        QPushButton#masterToggleButton:hover { background-color: #b83a3a; }

        QPushButton#masterToggleButtonActive {
            background-color: #008a45; /* 有効化ボタンは緑系に */
            border: 1px solid #10a35a;
            font-weight: bold;
            padding: 10px 12px;
        }
        QPushButton#masterToggleButtonActive:hover { background-color: #00a35a; }        

        QComboBox { background-color: #2D2F36; border: 1px solid #3C4048; border-radius: 6px; padding: 6px 10px; }
        QComboBox QAbstractItemView { background-color: #202225; color: #E0E0E0; selection-background-color: #2C2F33; }

        QLabel { color: #E0E0E0; }

        QSlider::groove:horizontal { height: 6px; background: #3C4048; border-radius: 3px; }
        QSlider::handle:horizontal { background: #00FF66; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }

        QCheckBox { spacing: 8px; }
        QCheckBox::indicator { width: 18px; height: 18px; }
        QCheckBox::indicator:unchecked { border: 1px solid #3C4048; background: #2D2F36; border-radius: 4px; }
        QCheckBox::indicator:checked { border: 1px solid #00cc55; background: #00FF66; border-radius: 4px; }

        QFrame#SeparatorLine { background-color: #3C4048; max-height: 1px; min-height: 1px; }

        QToolTip { background-color: #2D2F36; color: #E0E0E0; border: 1px solid #3C4048; }
        """
    )

# -----------------------------------------------------------------------------


def load_config():
    defaults = {
        "crosshair_visible": True,
        "dot_visible": True,
        "dot_radius": 5,
        "crosshair_color": "#00FF66",
        "dot_outer_color": "#FFFFFF",
        "dot_inner_color": "#000000",
        "disabled_keys": [],
        "crosshair_alpha": 1.0,
        "dot_alpha": 1.0,
        "fade_on_shoot": False,
        "last_selected": "デフォルト設定",
        "preset_folder": DEFAULT_PRESET_FOLDER,
        "monitor_apex": False
    }
    
    if not os.path.exists(CONFIG_FILE):
        return defaults

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

        # --- ここからが移行処理のロジック ---
        # "crosshair_visible" のような古いキーが存在するかチェック
        if "crosshair_visible" in config:
            print("古い形式の設定ファイルを検出しました。新しいプリセット形式に変換します。")
            
            # 1. 古い設定をプリセットとして保存
            imported_preset_name = "旧バージョンからのインポート設定"
            preset_folder = config.get("preset_folder", DEFAULT_PRESET_FOLDER)
            os.makedirs(preset_folder, exist_ok=True)
            imported_preset_path = os.path.join(preset_folder, imported_preset_name + PRESET_EXTENSION)
            
            # 古いconfigの内容全体がプリセットデータになる
            with open(imported_preset_path, "w", encoding="utf-8") as f_preset:
                json.dump(config, f_preset, indent=4)
            
            # 2. メインの設定ファイル(.crosshair_config.json)を新しい形式で上書き
            new_main_config = {
                "last_selected": imported_preset_name,
                "preset_folder": preset_folder
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f_main:
                json.dump(new_main_config, f_main, indent=4)
            
            print(f"設定を '{imported_preset_name}' として保存しました。")

            # 3. 起動時はインポートした設定を適用して返す
            # defaultsとマージして、不足しているキー（fade_on_shootなど）を補完する
            for key, value in defaults.items():
                config.setdefault(key, value)
            return config
            
        # --- 移行処理ここまで ---

        # 通常通り（新しい形式の）設定ファイルを読み込む
        else:
            # プリセットフォルダのパスを先に読み込む
            defaults["preset_folder"] = config.get("preset_folder", DEFAULT_PRESET_FOLDER)
            for key, value in defaults.items():
                config.setdefault(key, value)
            return config
            
    except Exception as e:
        print(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
        # エラーが発生した場合はデフォルト値を返す
        return defaults

    return defaults

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("設定保存に失敗:", e)

def get_executable_path():
    """
    実行ファイルのパスを取得する。
    PyInstallerでexe化された場合と、スクリプトとして実行された場合の両方に対応。
    """
    if getattr(sys, 'frozen', False):
        # exeとして実行されている場合
        return sys.executable
    else:
        # スクリプトとして実行されている場合 (python.exe "C:\path\to\script.py")
        return f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

def add_to_startup(app_name, path):
    """指定されたアプリケーションをWindowsのスタートアップに登録する"""
    if not IS_WINDOWS: return False
    try:
        # レジストリキーを開く（存在しない場合は作成される）
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as registry_key:
            winreg.SetValueEx(registry_key, app_name, 0, winreg.REG_SZ, path)
        return True
    except Exception as e:
        print(f"スタートアップ登録に失敗: {e}")
        return False

def remove_from_startup(app_name):
    """指定されたアプリケーションをWindowsのスタートアップから削除する"""
    if not IS_WINDOWS: return False
    try:
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE) as registry_key:
            winreg.DeleteValue(registry_key, app_name)
        return True
    except FileNotFoundError:
        # もともとキーが存在しない場合は成功とみなす
        return True
    except Exception as e:
        print(f"スタートアップからの削除に失敗: {e}")
        return False

def is_in_startup(app_name):
    """アプリケーションがスタートアップに登録されているか確認する"""
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

        # 最初の状態を確認して、必要なら即時通知
        try:
            initial_state = any(proc.info['name'] == self.process_name for proc in psutil.process_iter(['name']))
            if initial_state != self._game_is_running:
                self._game_is_running = initial_state
                self.gameRunning.emit(initial_state)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # プロセスが早く消えたり、アクセス権がなくてもクラッシュしないようにする
            pass


        while self.is_running:
            self.sleep(5) # 5秒待機
            try:
                found = any(proc.info['name'] == self.process_name for proc in psutil.process_iter(['name']))
                
                if found != self._game_is_running:
                    self._game_is_running = found
                    self.gameRunning.emit(found)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def stop(self):
        self.is_running = False
    

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, preset_folder_path=""):
        super().__init__(parent)
        self.setWindowTitle("環境設定")
        self.setLayout(QtWidgets.QVBoxLayout())

        path_layout = QtWidgets.QHBoxLayout()
        self.path_label = QtWidgets.QLabel(preset_folder_path)
        self.browse_btn = QtWidgets.QPushButton("参照")
        self.browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.browse_btn)

        self.layout().addLayout(path_layout)

        close_btn = QtWidgets.QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        self.layout().addWidget(close_btn)

    def browse_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "フォルダを選択", self.path_label.text())
        if folder:
            self.path_label.setText(folder)

    def get_selected_path(self):
        return self.path_label.text()


class CrosshairOverlay(QtWidgets.QWidget):
        
    def _set_dirty_and_update_display(self):
        """ダーティフラグを立て、プリセット表示を「新しいプリセット」に更新する"""
        if not self.is_dirty:
            self.is_dirty = True
            # コンボボックスの表示を「--- 新しいプリセット ---」(インデックス0) に変更
            self.preset_box.setCurrentIndex(0)

    def _on_click(self, x, y, button, pressed):
        """マウスのクリックイベントを処理するコールバック関数"""
        if button == mouse.Button.left:
            self.is_shooting = pressed
            # GUIの更新はメインスレッドから呼び出す必要があるため、
            # invokeMethodを使って安全にupdate()を呼び出します。
            QtCore.QMetaObject.invokeMethod(self, "update", QtCore.Qt.QueuedConnection)

    def _mouse_listener(self):
        """マウスイベントリスナーを開始し、実行し続ける"""
        with mouse.Listener(on_click=self._on_click) as listener:
            listener.join()


    # --- ControlPanelのインナークラス定義 ---
    class ControlPanel(QtWidgets.QWidget):
        def __init__(self, overlay):
            super().__init__()
            self.overlay = overlay
            self.setWindowTitle("Crosshair Control Panel")
            self.setGeometry(100, 100, 400, 100) # 少し幅を広げる

        def closeEvent(self, event):
            # ダーティフラグがONの場合のみ、保存確認を行う
            if self.overlay.is_dirty:
                reply = QtWidgets.QMessageBox.question(
                    self, "保存されていません",
                    "現在の設定はプリセットとして保存されていません。保存しますか？",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel
                )
                if reply == QtWidgets.QMessageBox.Yes:
                    # 保存がキャンセルされた場合は、ウィンドウを閉じない
                    if not self.overlay.save_preset(): 
                        event.ignore()
                        return
                elif reply == QtWidgets.QMessageBox.Cancel:
                    # ユーザーがキャンセルを選んだら、ウィンドウを閉じない
                    event.ignore()
                    return
            
            # ダーティでない、または「はい」「いいえ」が選ばれた場合はウィンドウを閉じる
            event.accept()
            self.overlay.close()


    def __init__(self):
        super().__init__()
        self.UNSAVED_PRESET_TEXT = "--- 新しいプリセット ---"
        self.is_dirty = False
        self._panel_animations = []
        self.master_enabled = True # オーバーレイ全体の有効/無効フラグ
        self.game_monitor_thread = None

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.WindowTransparentForInput |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # --- 射撃時フェード用のプロパティ ---
        self.fade_on_shoot_enabled = False # ON/OFF状態
        self.is_shooting = False           # 現在射撃中かどうかの状態

        # マウスリスナーを別スレッドで開始
        # daemon=Trueにすることで、メインプログラム終了時にスレッドも自動で終了させます
        self.mouse_listener_thread = threading.Thread(target=self._mouse_listener, daemon=True)
        self.mouse_listener_thread.start() 
    
        self.showFullScreen()

        screen = QtWidgets.QApplication.primaryScreen().size()
        self.center_x = screen.width() // 2
        self.center_y = screen.height() // 2
        self.size = 20

        config = load_config()
        self.monitor_apex = config.get("monitor_apex", False)

        # --- プリセット関連のプロパティを初期化 ---
        self.preset_folder = config.get("preset_folder", DEFAULT_PRESET_FOLDER)
        os.makedirs(self.preset_folder, exist_ok=True)
        self.default_config = {
            "crosshair_visible": True, "dot_visible": True, "dot_radius": 5,
            "crosshair_color": "#00FF66", "dot_outer_color": "#FFFFFF",
            "dot_inner_color": "#000000", "disabled_keys": [],
            "crosshair_alpha": 1.0, "dot_alpha": 1.0,
            "crosshair_shape": "十字", # ★形状のデフォルト値
        }
        self.last_selected_preset = config.get("last_selected", "デフォルト設定")
        self.presets = {"デフォルト設定": self.default_config}

        # 設定値を適用
        self.apply_config(self.get_current_preset_config())

        self.disabled_keys = config.get("disabled_keys", [])
        for k in self.disabled_keys:
            try: keyboard.block_key(k)
            except Exception as e: print(f"キー {k} の無効化に失敗: {e}")

    def get_current_preset_config(self):
        # 最後に選択されたプリセットの設定を読み込む
        if os.path.exists(CONFIG_FILE):
             try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                preset_name = config.get("last_selected", "デフォルト設定")
                preset_folder = config.get("preset_folder", DEFAULT_PRESET_FOLDER)
                
                if preset_name == "デフォルト設定":
                    # ★デフォルト設定にも形状を追加
                    default_with_shape = self.default_config.copy()
                    default_with_shape["crosshair_shape"] = "十字"
                    return default_with_shape

                preset_file = os.path.join(preset_folder, preset_name + PRESET_EXTENSION)
                if os.path.exists(preset_file):
                    with open(preset_file, "r", encoding="utf-8") as f:
                        return json.load(f)

             except Exception:
                pass
        return self.default_config


    def apply_config(self, config):
        self.crosshair_visible = config.get("crosshair_visible", True)
        self.dot_visible = config.get("dot_visible", True)
        self.dot_radius = config.get("dot_radius", 5)
        self.crosshair_color = config.get("crosshair_color", "#00FF66")
        self.dot_outer_color = config.get("dot_outer_color", "#FFFFFF")
        self.dot_inner_color = config.get("dot_inner_color", "#000000")
        self.crosshair_alpha = config.get("crosshair_alpha", 1.0)
        self.dot_alpha = config.get("dot_alpha", 1.0)
        self.fade_on_shoot_enabled = config.get("fade_on_shoot", False) 
        self.crosshair_shape = config.get("crosshair_shape", "十字") # ★形状を適用
        # disabled_keys は直接適用せず、起動時のみ読み込む
        self.update() # GUIを再描画

    # --- 以下、PresetManagerから移植したメソッド群 ---

    def load_presets(self):
        self.preset_box.blockSignals(True)
        self.preset_box.clear()
        
        # 1. 未保存状態を示す項目をリストの先頭に追加
        self.preset_box.addItem(self.UNSAVED_PRESET_TEXT)
        
        # 2. デフォルト設定と保存済みプリセットを追加
        self.preset_box.addItem("デフォルト設定")
        self.presets = {"デフォルト設定": self.default_config}

        for file in os.listdir(self.preset_folder):
            if file.endswith(PRESET_EXTENSION):
                name = os.path.splitext(file)[0]
                path = os.path.join(self.preset_folder, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.presets[name] = data
                    self.preset_box.addItem(name)
                except Exception as e:
                    print(f"プリセット読み込み失敗: {file}: {e}")

        # 3. 状態に応じて表示を決定
        if self.is_dirty:
            # ダーティ状態なら、表示は「--- 新しいプリセット ---」に固定
            self.preset_box.setCurrentIndex(0)
        elif self.last_selected_preset in self.presets:
            # ダーティでなければ、最後に選択したプリセットを表示
            index = self.preset_box.findText(self.last_selected_preset)
            self.preset_box.setCurrentIndex(index)
        else:
            # それ以外はデフォルト（「--- 新しいプリセット ---」）
            self.preset_box.setCurrentIndex(0)

        self.preset_box.blockSignals(False)

    def save_preset(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.panel, "プリセットを保存", os.path.join(self.preset_folder, "preset" + PRESET_EXTENSION),
            f"プリセットファイル (*{PRESET_EXTENSION})")
        if path:
            if not path.endswith(PRESET_EXTENSION):
                path += PRESET_EXTENSION
            try:
                # get_config() で現在の設定を取得して保存
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.get_config(), f, indent=4)
                
                self.last_selected_preset = os.path.splitext(os.path.basename(path))[0]
                self.save_global_config()
                self.load_presets()
                self.is_dirty = False
                return True # 保存成功
            except Exception as e:
                QtWidgets.QMessageBox.critical(self.panel, "保存失敗", str(e))
        return False # 保存キャンセル or 失敗

    def load_selected_preset(self):
        name = self.preset_box.currentText()
        # ★ガード節を追加
        if name == self.UNSAVED_PRESET_TEXT:
            return
        

        config_to_load = self.presets.get(name, self.default_config)
        self.apply_config(config_to_load)
        
        self.last_selected_preset = name
        self.save_global_config()
        print(f"プリセット {name} を読み込みました")
        
        # コントロールパネルのUIに設定を反映
        self.update_control_panel_ui()
        self.update() # オーバーレイを再描画
        self.is_dirty = False

    def open_settings(self):
        dlg = SettingsDialog(self.panel, self.preset_folder)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_path = dlg.get_selected_path()
            if new_path:
                self.preset_folder = new_path
                os.makedirs(self.preset_folder, exist_ok=True)
                self.save_global_config() # フォルダの変更も保存
                self.load_presets()

    def save_global_config(self):
        config = {
            "last_selected": self.last_selected_preset, 
            "preset_folder": self.preset_folder,
            "monitor_apex": self.monitor_apex
        }
        # 他の設定はメインのconfigファイルには保存しない
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"グローバル設定の保存に失敗: {e}")
    
    # --- 移植メソッド群ここまで ---

    class KeyCaptureDialog(QtWidgets.QDialog):
        def __init__(self, parent=None, message="キーを押してください", key_callback=None):
            super().__init__(parent)
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
            self.setWindowTitle("キー入力待機")
            self.setWindowModality(QtCore.Qt.ApplicationModal)
            self.setLayout(QtWidgets.QVBoxLayout())
            
            self.label = QtWidgets.QLabel(message)
            self.layout().addWidget(self.label)
            
            self.key_callback = key_callback
            self.captured_key = None
            self.hook = None

            cancel_button = QtWidgets.QPushButton("キャンセル")
            cancel_button.clicked.connect(self.reject) # rejectを呼び出すように変更
            self.layout().addWidget(cancel_button)
            self.resize(300, 100)

        def _on_key_press(self, event):
            # keyboardライブラリのイベントから直接キー名を取得
            key = event.name
            
            # Enterキーは無効化対象外
            if key == "enter":
                # このコールバックは別スレッドで実行されるため、
                # GUI操作はメインスレッドに依頼する必要がある
                QtCore.QMetaObject.invokeMethod(self, "_show_enter_error", QtCore.Qt.QueuedConnection)
                return

            self.captured_key = key
            # キーが取得できたらダイアログを閉じる
            QtCore.QMetaObject.invokeMethod(self, "accept", QtCore.Qt.QueuedConnection)
            return True # 他のフックにイベントを伝播させない

        @QtCore.pyqtSlot()
        def _show_enter_error(self):
            """メインスレッドでエラーメッセージを表示するためのスロット"""
            QtWidgets.QMessageBox.information(self, "無効化不可", "Enterキーは無効化できません。")

        def exec_(self):
            # ダイアログが表示される直前にキーボードフックを開始
            # suppress=Trueにすることで、押されたキーが他のアプリケーションに入力されるのを防ぐ
            self.hook = keyboard.on_press(self._on_key_press, suppress=True)
            
            # 親クラスのexec_を呼び出してダイアログをモーダルで表示
            result = super().exec_()
            
            # ダイアログが閉じたら必ずフックを解除する
            keyboard.unhook(self.hook)
            
            # ダイアログが正常に(acceptで)閉じられた場合、コールバックを実行
            if result == QtWidgets.QDialog.Accepted and self.key_callback and self.captured_key:
                self.key_callback(self.captured_key)
            
            return result

        # keyPressEvent は不要なので削除します

    def get_config(self):
        # 現在のUIの状態から設定辞書を作成して返す
        return {
            "crosshair_visible": self.crosshair_visible,
            "dot_visible": self.dot_visible,
            "dot_radius": self.dot_radius,
            "crosshair_color": self.crosshair_color,
            "dot_outer_color": self.dot_outer_color,
            "dot_inner_color": self.dot_inner_color,
            "disabled_keys": self.disabled_keys,
            "crosshair_alpha": self.crosshair_alpha,
            "dot_alpha": self.dot_alpha,
            "fade_on_shoot": self.fade_on_shoot_enabled,
            "crosshair_shape": self.crosshair_shape, # ★形状を保存
        }

    def paintEvent(self, event):
        # マスターが無効なら、何も描画しない
        if not self.master_enabled:
            return
                
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # 射撃状態に応じて一時的な透明度を決定
        ch_alpha = self.crosshair_alpha
        dot_alpha = self.dot_alpha
        if self.fade_on_shoot_enabled and self.is_shooting:
            ch_alpha *= 0.3
            dot_alpha *= 0.3

        if self.crosshair_visible:
            color = QtGui.QColor(self.crosshair_color)
            color.setAlphaF(ch_alpha)
            pen = QtGui.QPen(color, 2)
            painter.setPen(pen)
            
            # ★形状に応じて描画処理を分岐
            shape = self.crosshair_shape
            if shape == "十字":
                gap = 10
                painter.drawLine(self.center_x - self.size, self.center_y, self.center_x - gap, self.center_y)
                painter.drawLine(self.center_x + gap, self.center_y, self.center_x + self.size, self.center_y)
                painter.drawLine(self.center_x, self.center_y - self.size, self.center_x, self.center_y - gap)
                painter.drawLine(self.center_x, self.center_y + gap, self.center_x, self.center_y + self.size)
            elif shape == "十字 (ギャップなし)":
                painter.drawLine(self.center_x - self.size, self.center_y, self.center_x + self.size, self.center_y)
                painter.drawLine(self.center_x, self.center_y - self.size, self.center_x, self.center_y + self.size)
            elif shape == "円":
                painter.setBrush(QtCore.Qt.NoBrush) # 中身は塗りつぶさない
                rect = QtCore.QRect(self.center_x - self.size, self.center_y - self.size, self.size * 2, self.size * 2)
                painter.drawEllipse(rect)
            elif shape == "矢印 (シェブロン)":
                arrow_size = self.size // 2
                points = [
                    QtCore.QPoint(self.center_x - arrow_size, self.center_y + arrow_size),
                    QtCore.QPoint(self.center_x, self.center_y),
                    QtCore.QPoint(self.center_x + arrow_size, self.center_y + arrow_size)
                ]
                painter.drawPolyline(QtGui.QPolygon(points))


        if self.dot_visible and self.dot_radius > 0:
            outer_color = QtGui.QColor(self.dot_outer_color)
            outer_color.setAlphaF(dot_alpha) # 決定した透明度を適用
            painter.setBrush(QtGui.QBrush(outer_color))
            painter.setPen(QtGui.QPen(outer_color))
            painter.drawEllipse(QtCore.QRect(self.center_x - self.dot_radius, self.center_y - self.dot_radius, self.dot_radius * 2, self.dot_radius * 2))
            if self.dot_radius > 1:
                inner_r = self.dot_radius - 1
                inner_color = QtGui.QColor(self.dot_inner_color)
                inner_color.setAlphaF(dot_alpha) # 決定した透明度を適用
                painter.setBrush(QtGui.QBrush(inner_color)); painter.setPen(QtGui.QPen(inner_color))
                painter.drawEllipse(QtCore.QRect(self.center_x - inner_r, self.center_y - inner_r, inner_r * 2, inner_r * 2))

    def disable_key(self, key):
        if key == "enter": print("Enterキーは無効化できません。"); return
        if key not in self.disabled_keys: self.disabled_keys.append(key); keyboard.block_key(key)

    def enable_key(self, key):
        if key in self.disabled_keys:
            self.disabled_keys.remove(key)
            try: keyboard.unblock_key(key)
            except KeyError: pass

    def enable_all_keys(self):
        for k in self.disabled_keys:
            try: keyboard.unblock_key(k)
            except: pass
        self.disabled_keys.clear()

    def show_control_panel(self):
        self.panel = self.ControlPanel(self)
        self.panel.setObjectName("controlPanel")
        self.panel.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        # Card-like background to distinguish from desktop
        self.panel.setStyleSheet("#controlPanel { background-color: #181A1B; border: 1px solid #2C2F33; }")

        # Subtle drop shadow for depth
        shadow = QtWidgets.QGraphicsDropShadowEffect(self.panel)
        shadow.setBlurRadius(24)
        shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        shadow.setOffset(0, 12)
        self.panel.setGraphicsEffect(shadow)

        layout = QtWidgets.QVBoxLayout()

        # --- 環境設定メニュー ---
        menu_bar = QtWidgets.QMenuBar()
        settings_menu = menu_bar.addMenu("環境設定")
        settings_menu.addAction("保存先フォルダを変更", self.open_settings)

        settings_menu.addSeparator() # 見やすくするために区切り線を追加

        # スタートアップ設定のアクションを作成
        self.startup_action = QtWidgets.QAction("PC起動時に自動実行する", self.panel, checkable=True)

        if IS_WINDOWS:
            # 現在の状態をチェックして、チェックボックスに反映
            self.startup_action.setChecked(is_in_startup(APP_NAME))
            # アクションがトリガーされたら（クリックされたら）toggle_startupメソッドを呼ぶ
            self.startup_action.triggered.connect(self.toggle_startup)
        else:
            # Windows以外では機能を無効化し、ツールチップで説明を表示
            self.startup_action.setEnabled(False)
            self.startup_action.setToolTip("この機能はWindowsでのみ利用可能です。")
        
        settings_menu.addAction(self.startup_action)

        settings_menu.addSeparator()

        self.apex_monitor_action = QtWidgets.QAction("Apex Legendsを監視して自動切替", self.panel, checkable=True)
        self.apex_monitor_action.setToolTip("Apex Legendsの起動・終了に合わせてオーバーレイのON/OFFを自動で切り替えます。")

        if psutil:
            self.apex_monitor_action.setChecked(self.monitor_apex)
            self.apex_monitor_action.triggered.connect(self.toggle_apex_monitoring)
        else:
            self.apex_monitor_action.setEnabled(False)
            self.apex_monitor_action.setToolTip("この機能を利用するには 'psutil' ライブラリが必要です。(pip install psutil)")
        
        settings_menu.addAction(self.apex_monitor_action)

        layout.setMenuBar(menu_bar)

        # 1. マスター ON/OFF ボタンを作成
        self.master_toggle_btn = QtWidgets.QPushButton("オーバーレイを無効化")
        self.master_toggle_btn.setObjectName("masterToggleButton") # スタイルシートで識別するためのID
        self.master_toggle_btn.setToolTip("クロスヘアとドットの表示をまとめてON/OFFします")
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton)
        self.master_toggle_btn.setIcon(icon)
        self.master_toggle_btn.clicked.connect(self.toggle_master_visibility)
        layout.addWidget(self.master_toggle_btn)

        # マスターボタンと詳細設定の間に区切り線を追加
        line_master = QtWidgets.QFrame()
        line_master.setObjectName("SeparatorLine")
        line_master.setFrameShape(QtWidgets.QFrame.HLine)
        line_master.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line_master)

        # 2. 以降のウィジェットをリストに格納していく
        self.detail_controls = []        

        # --- プリセット機能 ---
        preset_layout = QtWidgets.QHBoxLayout()
        self.preset_box = QtWidgets.QComboBox()
        self.save_btn = QtWidgets.QPushButton("現在の設定を保存")
        self.save_btn.setProperty("accent", True)
        self.save_btn.clicked.connect(self.save_preset)
        preset_layout.addWidget(self.preset_box)
        preset_layout.addWidget(self.save_btn)
        layout.addLayout(preset_layout)
        self.detail_controls.extend([self.preset_box, self.save_btn]) # リストに追加        

        # 水平線を追加
        line = QtWidgets.QFrame()
        line.setObjectName("SeparatorLine")
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)
        self.detail_controls.append(line) # リストに追加        

        # --- 既存のコントロール ---
        self.crosshair_btn = QtWidgets.QPushButton("クロスヘア表示/非表示"); self.crosshair_state = QtWidgets.QLabel()
        self.crosshair_btn.clicked.connect(self.toggle_crosshair_button)
        h1 = QtWidgets.QHBoxLayout(); h1.addWidget(self.crosshair_btn); h1.addWidget(self.crosshair_state); layout.addLayout(h1)
        self.detail_controls.extend([self.crosshair_btn, self.crosshair_state]) # リストに追加        

        # ★形状選択UIを追加
        shape_layout = QtWidgets.QHBoxLayout()
        shape_label = QtWidgets.QLabel("クロスヘア形状")
        self.shape_box = QtWidgets.QComboBox()
        self.shape_box.addItems(["十字", "十字 (ギャップなし)", "円", "矢印 (シェブロン)"])
        self.shape_box.currentTextChanged.connect(self.update_crosshair_shape)
        shape_layout.addWidget(shape_label)
        shape_layout.addWidget(self.shape_box)
        layout.addLayout(shape_layout)
        self.detail_controls.extend([shape_label, self.shape_box])

        self.dot_btn = QtWidgets.QPushButton("ドット表示/非表示"); self.dot_state = QtWidgets.QLabel()
        self.dot_btn.clicked.connect(self.toggle_dot_button)
        h2 = QtWidgets.QHBoxLayout(); h2.addWidget(self.dot_btn); h2.addWidget(self.dot_state); layout.addLayout(h2)
        self.detail_controls.extend([self.dot_btn, self.dot_state]) # リストに追加        

        dotsize_layout = QtWidgets.QHBoxLayout(); dotsize_label = QtWidgets.QLabel("ドットサイズ")
        self.dot_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.dot_slider.setMinimum(0); self.dot_slider.setMaximum(100)
        self.dot_value = QtWidgets.QLabel(); self.dot_slider.valueChanged.connect(self.update_dot_size)
        dotsize_layout.addWidget(dotsize_label); dotsize_layout.addWidget(self.dot_slider); dotsize_layout.addWidget(self.dot_value); layout.addLayout(dotsize_layout)
        self.detail_controls.extend([dotsize_label, self.dot_slider, self.dot_value]) # リストに追加

        def make_color_button(label_text, getter, setter, update_callback):
            layout_ = QtWidgets.QHBoxLayout(); button = QtWidgets.QPushButton(label_text)
            square = QtWidgets.QLabel(); square.setFixedSize(20, 20)
            def pick_color():
                color = QtWidgets.QColorDialog.getColor(QtGui.QColor(getter()))
                if color.isValid(): 
                    setter(color.name())
                    square.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #3C4048; border-radius: 4px;")
                    update_callback()
                    self._set_dirty_and_update_display()
            button.clicked.connect(pick_color)
            layout_.addWidget(button); layout_.addWidget(square); return layout_, square
        
        color_update_cb = lambda: self.update()
        ch_color_layout, self.ch_color_square = make_color_button("クロスヘア色", lambda: self.crosshair_color, self.set_crosshair_color, color_update_cb)
        dot_out_color_layout, self.dot_out_color_square = make_color_button("ドット外枠色", lambda: self.dot_outer_color, self.set_dot_outer_color, color_update_cb)
        dot_in_color_layout, self.dot_in_color_square = make_color_button("ドット内側色", lambda: self.dot_inner_color, self.set_dot_inner_color, color_update_cb)
        layout.addLayout(ch_color_layout); layout.addLayout(dot_out_color_layout); layout.addLayout(dot_in_color_layout)
        # addLayoutはウィジェットを返さないので、レイアウト内のウィジェットを個別に追加
        for i in range(ch_color_layout.count()): self.detail_controls.append(ch_color_layout.itemAt(i).widget())
        for i in range(dot_out_color_layout.count()): self.detail_controls.append(dot_out_color_layout.itemAt(i).widget())
        for i in range(dot_in_color_layout.count()): self.detail_controls.append(dot_in_color_layout.itemAt(i).widget())


        alpha_layout = QtWidgets.QHBoxLayout(); alpha_label = QtWidgets.QLabel("クロスヘア透明度")
        self.alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.alpha_slider.setMinimum(0); self.alpha_slider.setMaximum(100)
        self.alpha_value = QtWidgets.QLabel(); self.alpha_slider.valueChanged.connect(self.update_alpha)
        alpha_layout.addWidget(alpha_label); alpha_layout.addWidget(self.alpha_slider); alpha_layout.addWidget(self.alpha_value); layout.addLayout(alpha_layout)
        self.detail_controls.extend([alpha_label, self.alpha_slider, self.alpha_value]) # リストに追加

        dot_alpha_layout = QtWidgets.QHBoxLayout(); dot_alpha_label = QtWidgets.QLabel("ドット透明度")
        self.dot_alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.dot_alpha_slider.setMinimum(0); self.dot_alpha_slider.setMaximum(100)
        self.dot_alpha_value = QtWidgets.QLabel(); self.dot_alpha_slider.valueChanged.connect(self.update_dot_alpha)
        dot_alpha_layout.addWidget(dot_alpha_label); dot_alpha_layout.addWidget(self.dot_alpha_slider); dot_alpha_layout.addWidget(self.dot_alpha_value); layout.addLayout(dot_alpha_layout)
        self.detail_controls.extend([dot_alpha_label, self.dot_alpha_slider, self.dot_alpha_value]) # リストに追加


        # 射撃時フェード機能のチェックボックス
        self.fade_on_shoot_checkbox = QtWidgets.QCheckBox("射撃中はクロスヘアを薄くする")
        self.fade_on_shoot_checkbox.toggled.connect(self.toggle_fade_on_shoot)
        layout.addWidget(self.fade_on_shoot_checkbox)
        self.detail_controls.append(self.fade_on_shoot_checkbox) # リストに追加

        disable_layout = QtWidgets.QHBoxLayout(); disable_btn = QtWidgets.QPushButton("キーを無効化")
        self.disabled_keys_label = QtWidgets.QLabel(", ".join(self.disabled_keys) if self.disabled_keys else "なし"); self.disabled_keys_label.setWordWrap(True)
        disable_btn.clicked.connect(self.disable_key_gui); disable_layout.addWidget(disable_btn); disable_layout.addWidget(self.disabled_keys_label); layout.addLayout(disable_layout)
        self.detail_controls.extend([disable_btn, self.disabled_keys_label]) # リストに追加

        enable_btn = QtWidgets.QPushButton("キーを有効化"); enable_btn.clicked.connect(self.enable_key_gui); layout.addWidget(enable_btn)
        enable_all_btn = QtWidgets.QPushButton("すべてのキーを有効化"); enable_all_btn.clicked.connect(self.enable_all_keys_gui); layout.addWidget(enable_all_btn)
        self.detail_controls.extend([enable_btn, enable_all_btn]) # リストに追加

        self.panel.setLayout(layout)
        
        # UIの初期状態を設定
        self.update_control_panel_ui()
        
        # プリセットの読み込みと接続
        self.load_presets()
        self.preset_box.currentIndexChanged.connect(self.load_selected_preset)
        
        self.panel.show()

        # もし起動時に監視が有効なら、監視を開始する
        if self.monitor_apex and psutil:
            self.toggle_apex_monitoring(True)

        # Subtle entrance animations
        self.panel.setWindowOpacity(0.0)
        self.animate_panel_show()
        # One-time pulse to hint "保存" action
        self._pulse_once(self.save_btn, QtGui.QColor("#00FF66"))

    def set_master_enabled(self, enabled):
        """オーバーレイ全体の有効/無効をプログラムで設定する"""
        if self.master_enabled == enabled:
            return # 状態が同じなら何もしない

        self.master_enabled = enabled

        # 詳細設定ウィジェットの有効/無効を切り替える
        if hasattr(self, 'detail_controls'):
            for widget in self.detail_controls:
                widget.setEnabled(self.master_enabled)

        # ボタンの外観とテキストを更新する
        if hasattr(self, 'master_toggle_btn'):
            if self.master_enabled:
                self.master_toggle_btn.setText("オーバーレイを無効化")
                icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton)
                self.master_toggle_btn.setIcon(icon)
                self.master_toggle_btn.setObjectName("masterToggleButton")
            else:
                self.master_toggle_btn.setText("オーバーレイを有効化")
                icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton)
                self.master_toggle_btn.setIcon(icon)
                self.master_toggle_btn.setObjectName("masterToggleButtonActive")
            
            self.master_toggle_btn.style().unpolish(self.master_toggle_btn)
            self.master_toggle_btn.style().polish(self.master_toggle_btn)

        # オーバーレイの再描画をトリガー
        self.update()

    def toggle_master_visibility(self):
        """マスターボタンでオーバーレイ全体の有効/無効を切り替える"""
        # 自動監視が有効な場合は、手動操作を許可しないか、あるいは監視をオフにするか
        # ここでは、手動操作が自動設定を上書きし、監視をオフにする仕様とする
        if self.monitor_apex and hasattr(self, 'apex_monitor_action'):
            reply = QtWidgets.QMessageBox.question(
                self.panel, "確認",
                "手動で操作するとApex Legendsの自動監視はオフになります。よろしいですか？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.apex_monitor_action.setChecked(False) # これが toggle_apex_monitoring をトリガーする
            else:
                return # 操作をキャンセル

        self.set_master_enabled(not self.master_enabled)    
        

    def toggle_startup(self, checked):
        """スタートアップ設定のON/OFFを切り替える"""
        path = get_executable_path()
        if checked:
            # チェックボックスがONになった場合
            if add_to_startup(APP_NAME, path):
                QtWidgets.QMessageBox.information(self.panel, "設定完了", "PC起動時に自動実行するよう設定しました。")
            else:
                QtWidgets.QMessageBox.warning(self.panel, "設定失敗", "スタートアップへの登録に失敗しました。\n管理者として実行すると解決する場合があります。")
                self.startup_action.setChecked(False) # 失敗したのでチェックを元に戻す
        else:
            # チェックボックスがOFFになった場合
            if remove_from_startup(APP_NAME):
                QtWidgets.QMessageBox.information(self.panel, "設定完了", "スタートアップ設定を解除しました。")
            else:
                QtWidgets.QMessageBox.warning(self.panel, "設定失敗", "スタートアップからの登録解除に失敗しました。")
                self.startup_action.setChecked(True) # 失敗したのでチェックを元に戻す    

    @QtCore.pyqtSlot(bool)
    def on_game_state_changed(self, is_running):
        """ゲームの実行状態が変わったときに呼ばれるスロット"""
        print(f"ゲーム状態の変更を検知: {'実行中' if is_running else '終了'}")
        if self.monitor_apex:
            self.set_master_enabled(is_running)

    def toggle_apex_monitoring(self, checked):
        """Apex Legendsの監視を開始/停止する"""
        self.monitor_apex = checked
        self.save_global_config()

        if checked:
            if not psutil:
                QtWidgets.QMessageBox.warning(self.panel, "ライブラリ不足", "この機能を利用するには 'psutil' が必要です。コマンドプロンプトで 'pip install psutil' を実行してください。")
                if hasattr(self, 'apex_monitor_action'):
                    self.apex_monitor_action.setChecked(False)
                return

            if self.game_monitor_thread is None:
                self.game_monitor_thread = GameMonitorThread(GAME_PROCESS_NAME, self)
                self.game_monitor_thread.gameRunning.connect(self.on_game_state_changed)
                self.game_monitor_thread.start()
                print("Apex Legendsの監視を開始しました。")
        else:
            if self.game_monitor_thread is not None:
                self.game_monitor_thread.stop()
                self.game_monitor_thread.quit()
                self.game_monitor_thread.wait()
                self.game_monitor_thread = None
                print("Apex Legendsの監視を停止しました。")

    def animate_panel_show(self) -> None:
        if not hasattr(self, "panel"):
            return
        # Fade in
        fade = QtCore.QPropertyAnimation(self.panel, b"windowOpacity")
        fade.setDuration(300)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        # Slight slide for polish
        end_geo = self.panel.geometry()
        start_geo = QtCore.QRect(end_geo.x(), end_geo.y() - 20, end_geo.width(), end_geo.height())
        slide = QtCore.QPropertyAnimation(self.panel, b"geometry")
        slide.setDuration(350)
        slide.setStartValue(start_geo)
        slide.setEndValue(end_geo)
        slide.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        group = QtCore.QParallelAnimationGroup(self.panel)
        group.addAnimation(fade)
        group.addAnimation(slide)
        group.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        self._panel_animations.append(group)

    def _pulse_once(self, widget: QtWidgets.QWidget, color: QtGui.QColor) -> None:
        effect = QtWidgets.QGraphicsDropShadowEffect(widget)
        effect.setColor(color)
        effect.setOffset(0, 0)
        effect.setBlurRadius(0)
        widget.setGraphicsEffect(effect)

        up = QtCore.QPropertyAnimation(effect, b"blurRadius")
        up.setDuration(500)
        up.setStartValue(0)
        up.setEndValue(24)
        up.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        down = QtCore.QPropertyAnimation(effect, b"blurRadius")
        down.setDuration(500)
        down.setStartValue(24)
        down.setEndValue(0)
        down.setEasingCurve(QtCore.QEasingCurve.InCubic)

        seq = QtCore.QSequentialAnimationGroup(widget)
        seq.addAnimation(up)
        seq.addAnimation(down)
        seq.finished.connect(lambda: widget.setGraphicsEffect(None))
        seq.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        self._panel_animations.append(seq)

    def update_control_panel_ui(self):
        # 現在のインスタンス変数に基づいてコントロールパネルのUIを更新する

        # --- 値を設定する間、一時的にシグナルをブロック ---
        self.shape_box.blockSignals(True) # ★追加
        self.dot_slider.blockSignals(True)
        self.alpha_slider.blockSignals(True)
        self.dot_alpha_slider.blockSignals(True)
        self.fade_on_shoot_checkbox.blockSignals(True)
        # -------------------------------- תח

        self.crosshair_state.setText("ON" if self.crosshair_visible else "OFF")
        self.dot_state.setText("ON" if self.dot_visible else "OFF")
        
        self.shape_box.setCurrentText(self.crosshair_shape) # ★追加

        self.dot_slider.setValue(self.dot_radius * 2)
        self.dot_value.setText(str(self.dot_radius * 2))
        
        self.ch_color_square.setStyleSheet(f"background-color: {self.crosshair_color}; border: 1px solid #3C4048; border-radius: 4px;")
        self.dot_out_color_square.setStyleSheet(f"background-color: {self.dot_outer_color}; border: 1px solid #3C4048; border-radius: 4px;")
        self.dot_in_color_square.setStyleSheet(f"background-color: {self.dot_inner_color}; border: 1px solid #3C4048; border-radius: 4px;")
        
        self.alpha_slider.setValue(int(self.crosshair_alpha * 100))
        self.alpha_value.setText(str(self.crosshair_alpha))
        
        self.dot_alpha_slider.setValue(int(self.dot_alpha * 100))
        self.dot_alpha_value.setText(str(self.dot_alpha))

        self.fade_on_shoot_checkbox.setChecked(self.fade_on_shoot_enabled)
        
        self.disabled_keys_label.setText(", ".join(self.disabled_keys) if self.disabled_keys else "なし")

        # --- 値の設定が終わったら、シグナルのブロックを解除 ---
        self.shape_box.blockSignals(False) # ★追加
        self.dot_slider.blockSignals(False)
        self.alpha_slider.blockSignals(False)
        self.dot_alpha_slider.blockSignals(False)
        self.fade_on_shoot_checkbox.blockSignals(False)
        # ------------------------------------------------

    def toggle_crosshair_button(self): 
        self.crosshair_visible = not self.crosshair_visible
        self.crosshair_state.setText("ON" if self.crosshair_visible else "OFF")
        self.update()
        self._set_dirty_and_update_display()
    def update_crosshair_shape(self, shape_text):
        """クロスヘア形状の選択が変更されたときに呼ばれる"""
        self.crosshair_shape = shape_text
        self.update()
        self._set_dirty_and_update_display()
    def toggle_dot_button(self): self.dot_visible = not self.dot_visible; self.dot_state.setText("ON" if self.dot_visible else "OFF"); self.update(); self._set_dirty_and_update_display()
    def update_dot_size(self, val): self.dot_radius = val // 2; self.dot_value.setText(str(val)); self.update(); self._set_dirty_and_update_display()
    def update_alpha(self, val): alpha = round(val / 100, 2); self.crosshair_alpha = alpha; self.alpha_value.setText(str(alpha)); self.update(); self._set_dirty_and_update_display()
    def update_dot_alpha(self, val): alpha = round(val / 100, 2); self.dot_alpha = alpha; self.dot_alpha_value.setText(str(alpha)); self.update(); self._set_dirty_and_update_display()
    def toggle_fade_on_shoot(self, checked):
        """「射撃中はクロスヘアを薄くする」のON/OFFを切り替える"""
        self.fade_on_shoot_enabled = checked
        self.update() # 状態が変わったら即座に再描画
        self._set_dirty_and_update_display()
    def set_crosshair_color(self, val): self.crosshair_color = val
    def set_dot_outer_color(self, val): self.dot_outer_color = val
    def set_dot_inner_color(self, val): self.dot_inner_color = val

    def disable_key_gui(self):
        def on_key_selected(key): self.disable_key(key); self.disabled_keys_label.setText(", ".join(self.disabled_keys)); self.update(); self._set_dirty_and_update_display()
        dlg = self.KeyCaptureDialog(self.panel, message="無効化したいキーを押してください（Enterキーは無効化できません）", key_callback=on_key_selected)
        dlg.exec_()

    def enable_key_gui(self):
        if not self.disabled_keys:
            QtWidgets.QMessageBox.information(self.panel, "情報", "無効化されているキーはありません。")
            return
        
        def on_key_selected(key):
            self.enable_key(key); self.disabled_keys_label.setText(", ".join(self.disabled_keys) if self.disabled_keys else "なし"); self.update()
            # 他のキーを再度無効化
            for k in self.disabled_keys:
                if k != key: keyboard.block_key(k)
        
        for k in self.disabled_keys: # 一時的にすべて有効化
             try: keyboard.unblock_key(k)
             except: pass
        dlg = self.KeyCaptureDialog(self.panel, message="有効化したいキーを押してください（現在無効化中のキー: " + ", ".join(self.disabled_keys) + "）", key_callback=on_key_selected)
        dlg.exec_()

    def enable_all_keys_gui(self): 
        self.enable_all_keys()
        self.disabled_keys_label.setText("なし")
        self.update()
        self._set_dirty_and_update_display()

def gui_main():
    global overlay
    app = QtWidgets.QApplication(sys.argv)
    
    # この行を削除、またはTrueに設定します
    app.setQuitOnLastWindowClosed(True)

    # Apply sleek dark theme to the control panel and dialogs
    apply_dark_theme(app)
    
    overlay = CrosshairOverlay()
    overlay.show_control_panel()

    app.aboutToQuit.connect(lambda: [
        # 終了時に config (フォルダパスなど) を保存し、キーを全て有効化
        overlay.save_global_config(),
        overlay.enable_all_keys()
    ])
    overlay.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    gui_main()