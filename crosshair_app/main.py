import sys
import threading
import json
import os
import keyboard
import time
from pynput import mouse
from PyQt5 import QtCore, QtGui, QtWidgets

from . import ui
from . import theme
from . import dialogs
from . import config
from . import utils

class CrosshairOverlay(QtWidgets.QWidget):
    # シグナルを定義
    update_check_done = QtCore.pyqtSignal(dict)
    # ダウンロード進捗シグナル
    download_progress = QtCore.pyqtSignal(int)

    def __init__(self, screens):
        super().__init__()
        self.screens = screens
        self.UNSAVED_PRESET_TEXT = "--- 新しいプリセット ---"
        self.is_dirty = False
        self._panel_animations = []
        self.game_monitor_thread = None
        self.crosshair_image_path = None
        self.selected_monitor_index = 0
        self.center_x = 0
        self.center_y = 0

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.WindowTransparentForInput |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.fade_on_shoot_enabled = False
        self.is_shooting = False

        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.mouse_listener.start()
    
        self.size = 20

        loaded_config = config.load_config()
        self.monitor_apex = loaded_config.get("monitor_apex", False)
        self.selected_monitor_index = loaded_config.get("selected_monitor_index", 0)

        if self.monitor_apex:
            self.master_enabled = False
        else:
            self.master_enabled = True

        self.preset_folder = loaded_config.get("preset_folder", config.DEFAULT_PRESET_FOLDER)
        os.makedirs(self.preset_folder, exist_ok=True)
        self.default_config = {
            "crosshair_visible": True, "dot_visible": True, "dot_radius": 5,
            "crosshair_color": "#00FF66", "dot_outer_color": "#FFFFFF",
            "dot_inner_color": "#000000", "disabled_keys": [],
            "crosshair_alpha": 1.0, "dot_alpha": 1.0,
            "crosshair_shape": "十字",
            "crosshair_image_path": None,
            "selected_monitor_index": self.selected_monitor_index
        }
        self.last_selected_preset = loaded_config.get("last_selected", "デフォルト設定")
        self.presets = {"デフォルト設定": self.default_config}

        self.apply_config(self.get_current_preset_config())

        self.disabled_keys = loaded_config.get("disabled_keys", [])
        for k in self.disabled_keys:
            try: keyboard.block_key(k)
            except Exception as e: print(f"キー {k} の無効化に失敗: {e}")
        
        self.update_check_done.connect(self.show_update_dialog)
        self.download_progress.connect(self.update_progress_dialog)

    def _set_dirty_and_update_display(self):
        if not self.is_dirty:
            self.is_dirty = True
            self.panel.preset_box.setCurrentIndex(0)

    def _on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            self.is_shooting = pressed
            QtCore.QMetaObject.invokeMethod(self, "update", QtCore.Qt.QueuedConnection)

    def get_current_preset_config(self):
        if os.path.exists(config.CONFIG_FILE):
             try:
                with open(config.CONFIG_FILE, "r", encoding="utf-8") as f:
                    main_config = json.load(f)
                
                preset_name = main_config.get("last_selected", "デフォルト設定")
                preset_folder = main_config.get("preset_folder", config.DEFAULT_PRESET_FOLDER)
                
                if preset_name == "デフォルト設定":
                    default_with_shape = self.default_config.copy()
                    return default_with_shape

                preset_file = os.path.join(preset_folder, preset_name + config.PRESET_EXTENSION)
                if os.path.exists(preset_file):
                    with open(preset_file, "r", encoding="utf-8") as f:
                        return json.load(f)

             except Exception:
                pass
        return self.default_config

    def apply_config(self, config_data):
        self.crosshair_visible = config_data.get("crosshair_visible", True)
        self.dot_visible = config_data.get("dot_visible", True)
        self.dot_radius = config_data.get("dot_radius", 5)
        self.crosshair_color = config_data.get("crosshair_color", "#00FF66")
        self.dot_outer_color = config_data.get("dot_outer_color", "#FFFFFF")
        self.dot_inner_color = config_data.get("dot_inner_color", "#000000")
        self.crosshair_alpha = config_data.get("crosshair_alpha", 1.0)
        self.dot_alpha = config_data.get("dot_alpha", 1.0)
        self.fade_on_shoot_enabled = config_data.get("fade_on_shoot", False) 
        self.crosshair_shape = config_data.get("crosshair_shape", "十字")
        self.crosshair_image_path = config_data.get("crosshair_image_path", None)
        self.selected_monitor_index = config_data.get("selected_monitor_index", self.selected_monitor_index)
        self.update()

    def get_config(self):
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
            "crosshair_shape": self.crosshair_shape,
            "crosshair_image_path": self.crosshair_image_path,
            "selected_monitor_index": self.selected_monitor_index
        }

    def paintEvent(self, event):
        if not self.master_enabled:
            return
        
        self.center_x = self.width() // 2
        self.center_y = self.height() // 2
                
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        ch_alpha = self.crosshair_alpha
        dot_alpha = self.dot_alpha
        if self.fade_on_shoot_enabled and self.is_shooting:
            ch_alpha *= 0.3
            dot_alpha *= 0.3

        if self.crosshair_visible:
            painter.setOpacity(ch_alpha)
            shape = self.crosshair_shape
            
            image_path = None
            if shape == "MAME":
                image_path = "mame.png"
            elif shape == "カスタム画像":
                image_path = self.crosshair_image_path

            if image_path and os.path.exists(image_path):
                pixmap = QtGui.QPixmap(image_path)
                if not pixmap.isNull():
                    target_size = self.size * 2
                    target_rect = QtCore.QRect(self.center_x - self.size, self.center_y - self.size, target_size, target_size)
                    painter.drawPixmap(target_rect, pixmap)
            else:
                color = QtGui.QColor(self.crosshair_color)
                color.setAlphaF(ch_alpha)
                pen = QtGui.QPen(color, 2)
                painter.setPen(pen)
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
                    painter.setBrush(QtCore.Qt.NoBrush)
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
            painter.setOpacity(1.0) # Reset opacity for dot
            outer_color = QtGui.QColor(self.dot_outer_color)
            outer_color.setAlphaF(dot_alpha)
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
        self.panel = ui.ControlPanel(self)
        
        self.panel.monitor_selection_box.blockSignals(True)
        
        primary_screen_index = self.screens.index(QtWidgets.QApplication.primaryScreen())
        for i, screen in enumerate(self.screens):
            size = screen.size()
            item_text = f"モニター {i+1}: {size.width()}x{size.height()}"
            if i == primary_screen_index:
                item_text += " (プライマリ)"
            self.panel.monitor_selection_box.addItem(item_text)
        
        self.panel.monitor_selection_box.setCurrentIndex(self.selected_monitor_index)
        self.panel.monitor_selection_box.blockSignals(False)

        self.panel.show()

    @QtCore.pyqtSlot(dict)
    def show_update_dialog(self, update_info):
        if hasattr(self, 'panel'):
            dialog = dialogs.UpdateDialog(self.panel, update_info)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                self.start_update_process(update_info['download_url'])
        else:
            print("コントロールパネルが初期化されていません。")

    def start_update_process(self, download_url):
        self.progress_dialog = dialogs.ProgressDialog(self.panel)
        self.progress_dialog.show()

        self.download_thread = threading.Thread(target=self.download_worker, args=(download_url,), daemon=True)
        self.download_thread.start()

    @QtCore.pyqtSlot(int)
    def update_progress_dialog(self, value):
        if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():
            self.progress_dialog.update_progress(value)

    def download_worker(self, url):
        def progress_callback(progress):
            self.download_progress.emit(progress)

        downloaded_path = utils.download_asset_with_progress(url, progress_callback)
        
        if downloaded_path:
            # ダウンロード成功
            QtCore.QMetaObject.invokeMethod(self.progress_dialog, "update_progress", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(int, 100))
            QtCore.QMetaObject.invokeMethod(self.progress_dialog, "close", QtCore.Qt.QueuedConnection)
            
            # ZIPを展開し、新しい実行ファイルのパスを取得
            new_exe_in_temp_path = utils.extract_and_find_exe(downloaded_path)

            if new_exe_in_temp_path:
                current_exe_path = utils.get_executable_path()
                updater_script = utils.create_updater_script(downloaded_path, current_exe_path, new_exe_in_temp_path)
                
                if updater_script:
                    utils.run_updater_and_exit(updater_script)
                else:
                    print("アップデーターの作成に失敗しました。")
                    QtWidgets.QMessageBox.critical(self.panel, "アップデートエラー", "アップデーターの作成に失敗しました。")
            else:
                print("ZIPファイルから実行ファイルが見つかりませんでした。")
                QtWidgets.QMessageBox.critical(self.panel, "アップデートエラー", "ZIPファイルから実行ファイルが見つかりませんでした。")
        else:
            # ダウンロード失敗
            QtCore.QMetaObject.invokeMethod(self.progress_dialog, "close", QtCore.Qt.QueuedConnection)
            print("ダウンロードに失敗しました。")
            QtWidgets.QMessageBox.critical(self.panel, "アップデートエラー", "ダウンロードに失敗しました。")

    def save_monitor_selection(self, index):
        self.selected_monitor_index = index
        self.save_global_config()

    def save_global_config(self):
        main_config = {
            "last_selected": self.last_selected_preset, 
            "preset_folder": self.preset_folder,
            "monitor_apex": self.monitor_apex,
            "selected_monitor_index": self.selected_monitor_index
        }
        config.save_global_config(main_config)

    def clean_up(self):
        self.mouse_listener.stop()
        self.enable_all_keys()
        self.save_global_config()

def check_updates_thread(overlay):
    """バックグラウンドでアップデートを確認するスレッド"""
    time.sleep(2) 
    print("アップデートを確認しています...")
    update_info = utils.check_for_updates(config.APP_VERSION)
    if update_info:
        print(f"新しいバージョンが見つかりました: {update_info['latest_version']}")
        overlay.update_check_done.emit(update_info)
    else:
        print("新しいバージョンは見つかりませんでした。")

def gui_main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    theme.apply_dark_theme(app)
    
    screens = app.screens()
    overlay = CrosshairOverlay(screens)
    
    target_index = overlay.selected_monitor_index
    if 0 <= target_index < len(screens):
        target_screen = screens[target_index]
        overlay.setGeometry(target_screen.geometry())
        overlay.showFullScreen()
    else:
        overlay.showFullScreen()

    overlay.show_control_panel()

    update_thread = threading.Thread(target=check_updates_thread, args=(overlay,), daemon=True)
    update_thread.start()

    app.aboutToQuit.connect(overlay.clean_up)
    sys.exit(app.exec_())

if __name__ == "__main__":
    gui_main()