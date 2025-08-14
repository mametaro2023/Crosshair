import sys
import threading
import queue
import json
import os
import math
import keyboard
from pynput import mouse
from PyQt5 import QtCore, QtGui, QtWidgets

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".crosshair_config.json")
DEFAULT_PRESET_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "CrosshairPresets")
PRESET_EXTENSION = ".mametaro"

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
        "preset_folder": DEFAULT_PRESET_FOLDER
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


def build_modern_stylesheet():
    """Return a modern dark stylesheet that targets the control panel and common inputs.
    Note: Avoid setting a global QWidget background to keep the overlay transparent.
    """
    return """
    /* Global font and smoothing */
    * {
        font-family: 'Noto Sans JP', 'Segoe UI', 'Meiryo', sans-serif;
        letter-spacing: 0.2px;
    }

    /* Panel container */
    #ControlPanel {
        background-color: rgba(15, 17, 26, 230);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 8px;
    }

    /* Menu bar */
    QMenuBar { background: transparent; border: none; }
    QMenuBar::item { background: transparent; padding: 6px 10px; color: #e6e6e6; }
    QMenuBar::item:selected { background: rgba(255,255,255,0.06); border-radius: 6px; }
    QMenu { background-color: #0f111a; border: 1px solid #2c313c; }
    QMenu::item { padding: 6px 10px; }
    QMenu::item:selected { background-color: #2a2f3a; }

    /* Buttons */
    QPushButton {
        background-color: #1e222a;
        color: #e6e6e6;
        border: 1px solid #2c313c;
        border-radius: 8px;
        padding: 6px 10px;
    }
    QPushButton:hover { background-color: #2a2f3a; border-color: #3a3f4b; }
    QPushButton:pressed { background-color: #141821; }
    QPushButton:disabled { color: rgba(230,230,230,0.4); border-color: rgba(44,49,60,0.6); }

    /* ComboBox */
    QComboBox {
        background-color: #141821;
        color: #e6e6e6;
        border: 1px solid #2c313c;
        border-radius: 8px;
        padding: 6px 10px;
    }
    QComboBox QAbstractItemView { background-color: #0f111a; color: #e6e6e6; selection-background-color: #2a2f3a; }

    /* Labels */
    QLabel { color: #e6e6e6; }

    /* Checkboxes */
    QCheckBox { color: #e6e6e6; spacing: 8px; }
    QCheckBox::indicator { width: 18px; height: 18px; }

    /* Sliders */
    QSlider::groove:horizontal { background: #2c313c; height: 6px; border-radius: 3px; }
    QSlider::sub-page:horizontal { background: #4fad8a; height: 6px; border-radius: 3px; }
    QSlider::handle:horizontal {
        background: #5bd3a6; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; border: 2px solid #0f111a;
    }

    /* Color preview squares */
    QLabel[colorSquare="true"] {
        border: 1px solid #3a3f4b;
        border-radius: 6px;
    }

    /* Separators */
    QFrame[frameShape="4"] { /* HLine */ color: #2c313c; background-color: #2c313c; height: 1px; }
    """

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, preset_folder_path=""):
        super().__init__(parent)
        self.setWindowTitle("環境設定")
        self.setLayout(QtWidgets.QVBoxLayout())

        path_layout = QtWidgets.QHBoxLayout()
        self.path_label = QtWidgets.QLabel(preset_folder_path)
        self.browse_btn = QtWidgets.QPushButton("参照")
        self.browse_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
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
            self.setGeometry(100, 100, 520, 100) # 少し幅を広げる

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

        # --- プリセット関連のプロパティを初期化 ---
        self.preset_folder = config.get("preset_folder", DEFAULT_PRESET_FOLDER)
        os.makedirs(self.preset_folder, exist_ok=True)
        self.default_config = {
            "crosshair_visible": True, "dot_visible": True, "dot_radius": 5,
            "crosshair_color": "#00FF66", "dot_outer_color": "#FFFFFF",
            "dot_inner_color": "#000000", "disabled_keys": [],
            "crosshair_alpha": 1.0, "dot_alpha": 1.0,
        }
        self.last_selected_preset = config.get("last_selected", "デフォルト設定")
        self.presets = {"デフォルト設定": self.default_config}

        # 設定値を適用
        self.apply_config(self.get_current_preset_config())

        self.disabled_keys = config["disabled_keys"]
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
                    return self.default_config

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
                self.save_last_selected_preset()
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
        self.save_last_selected_preset()
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
                self.save_last_selected_preset() # フォルダの変更も保存
                self.load_presets()

    def save_last_selected_preset(self):
        config = {"last_selected": self.last_selected_preset, "preset_folder": self.preset_folder}
        # 他の設定はメインのconfigファイルには保存しない
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except:
            pass
    
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
        }

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # 射撃状態に応じて一時的な透明度を決定
        ch_alpha = self.crosshair_alpha
        dot_alpha = self.dot_alpha
        if self.fade_on_shoot_enabled and self.is_shooting:
            ch_alpha *= 0.1
            dot_alpha *= 0.1

        if self.crosshair_visible:
            base = QtGui.QColor(self.crosshair_color)
            base.setAlphaF(ch_alpha)
            gap = 10
            # Glow pass
            glow = QtGui.QColor(base)
            glow.setAlphaF(max(0.0, ch_alpha * 0.25))
            painter.setPen(QtGui.QPen(glow, 8))
            painter.drawLine(self.center_x - self.size, self.center_y, self.center_x - gap, self.center_y)
            painter.drawLine(self.center_x + gap, self.center_y, self.center_x + self.size, self.center_y)
            painter.drawLine(self.center_x, self.center_y - self.size, self.center_x, self.center_y - gap)
            painter.drawLine(self.center_x, self.center_y + gap, self.center_x, self.center_y + self.size)
            # Crisp pass
            pen = QtGui.QPen(base, 2)
            painter.setPen(pen)
            painter.drawLine(self.center_x - self.size, self.center_y, self.center_x - gap, self.center_y)
            painter.drawLine(self.center_x + gap, self.center_y, self.center_x + self.size, self.center_y)
            painter.drawLine(self.center_x, self.center_y - self.size, self.center_x, self.center_y - gap)
            painter.drawLine(self.center_x, self.center_y + gap, self.center_x, self.center_y + self.size)
        if self.dot_visible and self.dot_radius > 0:
            outer_color = QtGui.QColor(self.dot_outer_color)
            outer_color.setAlphaF(dot_alpha)
            # Glow around dot
            grad = QtGui.QRadialGradient(self.center_x, self.center_y, self.dot_radius * 3)
            c0 = QtGui.QColor(outer_color)
            c0.setAlphaF(min(1.0, dot_alpha * 0.35))
            c1 = QtGui.QColor(outer_color)
            c1.setAlphaF(0.0)
            grad.setColorAt(0.0, c0)
            grad.setColorAt(1.0, c1)
            painter.setBrush(QtGui.QBrush(grad))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(QtCore.QRect(self.center_x - self.dot_radius * 3, self.center_y - self.dot_radius * 3, self.dot_radius * 6, self.dot_radius * 6))
            # Main dot
            painter.setBrush(QtGui.QBrush(outer_color))
            painter.setPen(QtGui.QPen(outer_color))
            painter.drawEllipse(QtCore.QRect(self.center_x - self.dot_radius, self.center_y - self.dot_radius, self.dot_radius * 2, self.dot_radius * 2))
            if self.dot_radius > 1:
                inner_r = self.dot_radius - 1
                inner_color = QtGui.QColor(self.dot_inner_color)
                inner_color.setAlphaF(dot_alpha)
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
        self.panel.setObjectName("ControlPanel")
        layout = QtWidgets.QVBoxLayout()

        # --- 環境設定メニュー ---
        menu_bar = QtWidgets.QMenuBar()
        settings_menu = menu_bar.addMenu("環境設定")
        settings_menu.addAction("保存先フォルダを変更", self.open_settings)
        layout.setMenuBar(menu_bar)

        # --- プリセット機能 ---
        preset_layout = QtWidgets.QHBoxLayout()
        self.preset_box = QtWidgets.QComboBox()
        self.save_btn = QtWidgets.QPushButton("現在の設定を保存")
        self.save_btn.setIcon(self.panel.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton))
        self.save_btn.clicked.connect(self.save_preset)
        preset_layout.addWidget(self.preset_box)
        preset_layout.addWidget(self.save_btn)
        layout.addLayout(preset_layout)

        # 水平線を追加
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)

        # --- 既存のコントロール ---
        self.crosshair_btn = QtWidgets.QPushButton("クロスヘア表示/非表示"); self.crosshair_state = QtWidgets.QLabel()
        self.crosshair_btn.clicked.connect(self.toggle_crosshair_button)
        h1 = QtWidgets.QHBoxLayout(); h1.addWidget(self.crosshair_btn); h1.addWidget(self.crosshair_state); layout.addLayout(h1)

        self.dot_btn = QtWidgets.QPushButton("ドット表示/非表示"); self.dot_state = QtWidgets.QLabel()
        self.dot_btn.clicked.connect(self.toggle_dot_button)
        h2 = QtWidgets.QHBoxLayout(); h2.addWidget(self.dot_btn); h2.addWidget(self.dot_state); layout.addLayout(h2)

        dotsize_layout = QtWidgets.QHBoxLayout(); dotsize_label = QtWidgets.QLabel("ドットサイズ")
        self.dot_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.dot_slider.setMinimum(0); self.dot_slider.setMaximum(100)
        self.dot_value = QtWidgets.QLabel(); self.dot_slider.valueChanged.connect(self.update_dot_size)
        dotsize_layout.addWidget(dotsize_label); dotsize_layout.addWidget(self.dot_slider); dotsize_layout.addWidget(self.dot_value); layout.addLayout(dotsize_layout)

        def make_color_button(label_text, getter, setter, update_callback):
            layout_ = QtWidgets.QHBoxLayout(); button = QtWidgets.QPushButton(label_text)
            square = QtWidgets.QLabel(); square.setFixedSize(20, 20); square.setProperty("colorSquare", True)
            def pick_color():
                color = QtWidgets.QColorDialog.getColor(QtGui.QColor(getter()))
                if color.isValid(): 
                    setter(color.name())
                    square.setStyleSheet(f"background-color: {color.name()};")
                    update_callback()
                    self._set_dirty_and_update_display()
            button.clicked.connect(pick_color)
            layout_.addWidget(button); layout_.addWidget(square); return layout_, square
        
        color_update_cb = lambda: self.update()
        ch_color_layout, self.ch_color_square = make_color_button("クロスヘア色", lambda: self.crosshair_color, self.set_crosshair_color, color_update_cb)
        dot_out_color_layout, self.dot_out_color_square = make_color_button("ドット外枠色", lambda: self.dot_outer_color, self.set_dot_outer_color, color_update_cb)
        dot_in_color_layout, self.dot_in_color_square = make_color_button("ドット内側色", lambda: self.dot_inner_color, self.set_dot_inner_color, color_update_cb)
        layout.addLayout(ch_color_layout); layout.addLayout(dot_out_color_layout); layout.addLayout(dot_in_color_layout)

        alpha_layout = QtWidgets.QHBoxLayout(); alpha_label = QtWidgets.QLabel("クロスヘア透明度")
        self.alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.alpha_slider.setMinimum(0); self.alpha_slider.setMaximum(100)
        self.alpha_value = QtWidgets.QLabel(); self.alpha_slider.valueChanged.connect(self.update_alpha)
        alpha_layout.addWidget(alpha_label); alpha_layout.addWidget(self.alpha_slider); alpha_layout.addWidget(self.alpha_value); layout.addLayout(alpha_layout)

        dot_alpha_layout = QtWidgets.QHBoxLayout(); dot_alpha_label = QtWidgets.QLabel("ドット透明度")
        self.dot_alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.dot_alpha_slider.setMinimum(0); self.dot_alpha_slider.setMaximum(100)
        self.dot_alpha_value = QtWidgets.QLabel(); self.dot_alpha_slider.valueChanged.connect(self.update_dot_alpha)
        dot_alpha_layout.addWidget(dot_alpha_label); dot_alpha_layout.addWidget(self.dot_alpha_slider); dot_alpha_layout.addWidget(self.dot_alpha_value); layout.addLayout(dot_alpha_layout)

        # 射撃時フェード機能のチェックボックス
        self.fade_on_shoot_checkbox = QtWidgets.QCheckBox("射撃中はクロスヘアを薄くする")
        self.fade_on_shoot_checkbox.toggled.connect(self.toggle_fade_on_shoot)
        layout.addWidget(self.fade_on_shoot_checkbox)

        disable_layout = QtWidgets.QHBoxLayout(); disable_btn = QtWidgets.QPushButton("キーを無効化")
        disable_btn.setIcon(self.panel.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning))
        self.disabled_keys_label = QtWidgets.QLabel(", ".join(self.disabled_keys) if self.disabled_keys else "なし"); self.disabled_keys_label.setWordWrap(True)
        disable_btn.clicked.connect(self.disable_key_gui); disable_layout.addWidget(disable_btn); disable_layout.addWidget(self.disabled_keys_label); layout.addLayout(disable_layout)

        enable_btn = QtWidgets.QPushButton("キーを有効化"); enable_btn.setIcon(self.panel.style().standardIcon(QtWidgets.QStyle.SP_DialogYesButton)); enable_btn.clicked.connect(self.enable_key_gui); layout.addWidget(enable_btn)
        enable_all_btn = QtWidgets.QPushButton("すべてのキーを有効化"); enable_all_btn.setIcon(self.panel.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload)); enable_all_btn.clicked.connect(self.enable_all_keys_gui); layout.addWidget(enable_all_btn)

        # Apply shadow to panel
        shadow = QtWidgets.QGraphicsDropShadowEffect(self.panel)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        self.panel.setGraphicsEffect(shadow)

        self.panel.setLayout(layout)
        
        # UIの初期状態を設定
        self.update_control_panel_ui()
        
        # プリセットの読み込みと接続
        self.load_presets()
        self.preset_box.currentIndexChanged.connect(self.load_selected_preset)
        
        # Show with fade-in animation
        self.panel.setWindowOpacity(0.0)
        self.panel.show()
        fade_anim = QtCore.QPropertyAnimation(self.panel, b"windowOpacity", self.panel)
        fade_anim.setDuration(220)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        fade_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def update_control_panel_ui(self):
        # 現在のインスタンス変数に基づいてコントロールパネルのUIを更新する

        # --- 値を設定する間、一時的にシグナルをブロック ---
        self.dot_slider.blockSignals(True)
        self.alpha_slider.blockSignals(True)
        self.dot_alpha_slider.blockSignals(True)
        self.fade_on_shoot_checkbox.blockSignals(True)
        # -----------------------------------------------

        self.crosshair_state.setText("ON" if self.crosshair_visible else "OFF")
        self.dot_state.setText("ON" if self.dot_visible else "OFF")
        
        self.dot_slider.setValue(self.dot_radius * 2)
        self.dot_value.setText(str(self.dot_radius * 2))
        
        self.ch_color_square.setStyleSheet(f"background-color: {self.crosshair_color};")
        self.dot_out_color_square.setStyleSheet(f"background-color: {self.dot_outer_color};")
        self.dot_in_color_square.setStyleSheet(f"background-color: {self.dot_inner_color};")
        
        self.alpha_slider.setValue(int(self.crosshair_alpha * 100))
        self.alpha_value.setText(str(self.crosshair_alpha))
        
        self.dot_alpha_slider.setValue(int(self.dot_alpha * 100))
        self.dot_alpha_value.setText(str(self.dot_alpha))

        self.fade_on_shoot_checkbox.setChecked(self.fade_on_shoot_enabled)
        
        self.disabled_keys_label.setText(", ".join(self.disabled_keys) if self.disabled_keys else "なし")

        # --- 値の設定が終わったら、シグナルのブロックを解除 ---
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
    
    # Apply modern style (Fusion + custom QSS)
    try:
        app.setStyle("Fusion")
    except Exception:
        pass
    app.setStyleSheet(build_modern_stylesheet())
    
    overlay = CrosshairOverlay()
    overlay.show_control_panel()

    app.aboutToQuit.connect(lambda: [
        # 終了時に config (フォルダパスなど) を保存し、キーを全て有効化
        overlay.save_last_selected_preset(),
        overlay.enable_all_keys()
    ])
    overlay.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    gui_main()