import os
import json
from PyQt5 import QtCore, QtWidgets
from pynput import mouse
import keyboard

from .. import config
from .. import ui
from .. import dialogs
from .. import utils

class CrosshairOverlayBase(QtWidgets.QWidget):
    # シグナルを定義
    update_check_done = QtCore.pyqtSignal(dict)
    # ダウンロード進捗シグナル
    download_progress = QtCore.pyqtSignal(int)
    # 表示切替シグナル（スレッドセーフなUI更新のため）
    master_visibility_changed = QtCore.pyqtSignal()

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
        self.toggle_hotkey = None

        # Explicitly initialize alpha values for robustness
        self.crosshair_alpha = 1.0
        self.crosshair_inner_alpha = 1.0
        self.dot_alpha = 1.0

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

        # ホットキーの設定 (will be moved to overlay_hotkeys.py)
        loaded_toggle_hotkey = loaded_config.get("toggle_hotkey", "ctrl+f1")
        # self.set_toggle_hotkey(loaded_toggle_hotkey) # This will be called from hotkeys mixin

        if self.monitor_apex:
            self.master_enabled = False
        else:
            self.master_enabled = True

        self.overall_preset_folder = loaded_config.get("overall_preset_folder", config.DEFAULT_OVERALL_PRESET_FOLDER)
        self.shape_preset_folder = loaded_config.get("shape_preset_folder", config.DEFAULT_SHAPE_PRESET_FOLDER)
        os.makedirs(self.overall_preset_folder, exist_ok=True)
        os.makedirs(self.shape_preset_folder, exist_ok=True)
        self.default_config = {
            "crosshair_visible": True,             "dot_visible": True, "dot_radius": 5,
            "dot_shape": "円",
            "crosshair_color": "#00FF66", "dot_outer_color": "#FFFFFF",
            "dot_inner_color": "#000000", "disabled_keys": [],
            "crosshair_alpha": 1.0, "crosshair_inner_alpha": 1.0, "dot_alpha": 1.0,
            "crosshair_shape": "十字",
            "crosshair_image_path": None,
            # 十字アドバンスド設定
            "crosshair_outline_enabled": True,
            "crosshair_outline_width": 1,
            "crosshair_outline_alpha": 1.0,
            "crosshair_vline_length": 10,
            "crosshair_hline_length": 10,
            "crosshair_thickness": 2,
            "crosshair_gap": 5,
            "drawing_order": loaded_config.get("drawing_order", "dot_on_top"),
            # 円アドバンスド設定
            "circle_outline_enabled": True,
            "circle_outline_width": 1,
            "circle_outline_alpha": 1.0,
            "circle_thickness": 2,
            "circle_diameter": 50,
            # 矢印 (シェブロン) アドバンスド設定
            "chevron_outline_enabled": True,
            "chevron_outline_width": 1,
            "chevron_outline_alpha": 1.0,
            "chevron_thickness": 2,
            "chevron_length": 10,
            # 画像系クロスヘアのリサイズ設定
            "image_crosshair_size": 40,
        }
        self.drawing_order = loaded_config.get("drawing_order", "dot_on_top")
        self.last_selected_preset = loaded_config.get("last_selected", "デフォルト設定")
        self.presets = {"デフォルト設定": self.default_config}

        self.apply_config(self.get_current_preset_config())

        self.disabled_keys = loaded_config.get("disabled_keys", []) # will be managed by overlay_utils.py
        # for k in self.disabled_keys: # This will be handled by overlay_utils.py
        #     try: keyboard.block_key(k)
        #     except Exception as e: print(f"キー {k} の無効化に失敗: {e}")
        
        # These signals will be connected in main.py or a dedicated setup method
        # self.update_check_done.connect(self.show_update_dialog)
        # self.download_progress.connect(self.update_progress_dialog)
        # self.master_visibility_changed.connect(self._update_ui_for_visibility_change)

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
                overall_folder = main_config.get("overall_preset_folder", config.DEFAULT_OVERALL_PRESET_FOLDER)
                
                if preset_name == "デフォルト設定":
                    default_with_shape = self.default_config.copy()
                    return default_with_shape

                preset_file = os.path.join(overall_folder, preset_name + config.PRESET_EXTENSION)
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
        self.dot_shape = config_data.get("dot_shape", "円")
        self.crosshair_color = config_data.get("crosshair_color", "#00FF66")
        self.dot_outer_color = config_data.get("dot_outer_color", "#FFFFFF")
        self.dot_inner_color = config_data.get("dot_inner_color", "#000000")
        self.crosshair_alpha = config_data.get("crosshair_alpha", 1.0)
        self.dot_alpha = config_data.get("dot_alpha", 1.0)
        self.fade_on_shoot_enabled = config_data.get("fade_on_shoot", False) 
        self.crosshair_shape = config_data.get("crosshair_shape", "十字")
        self.crosshair_image_path = config_data.get("crosshair_image_path", None)

        # 十字アドバンスド設定
        self.crosshair_outline_enabled = config_data.get("crosshair_outline_enabled", True)
        self.crosshair_outline_width = config_data.get("crosshair_outline_width", 1)
        self.crosshair_outline_alpha = config_data.get("crosshair_outline_alpha", 1.0)
        self.crosshair_vline_length = config_data.get("crosshair_vline_length", 10)
        self.crosshair_hline_length = config_data.get("crosshair_hline_length", 10)
        self.crosshair_thickness = config_data.get("crosshair_thickness", 2)
        self.crosshair_gap = config_data.get("crosshair_gap", 5)
        self.drawing_order = config_data.get("drawing_order", "dot_on_top")
        # 円アドバンスド設定
        self.circle_outline_enabled = config_data.get("circle_outline_enabled", True)
        self.circle_outline_width = config_data.get("circle_outline_width", 1)
        self.circle_outline_alpha = config_data.get("circle_outline_alpha", 1.0)
        self.circle_thickness = config_data.get("circle_thickness", 2)
        self.circle_diameter = config_data.get("circle_diameter", 50)

        # 矢印 (シェブロン) アドバンスド設定
        self.chevron_outline_enabled = config_data.get("chevron_outline_enabled", True)
        self.chevron_outline_width = config_data.get("chevron_outline_width", 1)
        self.chevron_outline_alpha = config_data.get("chevron_outline_alpha", 1.0)
        self.chevron_thickness = config_data.get("chevron_thickness", 2)
        self.chevron_length = config_data.get("chevron_length", 10)

        # 画像系クロスヘアのリサイズ設定
        self.image_crosshair_size = config_data.get("image_crosshair_size", 40)

        self.update()

    def get_config(self):
        return {
            "crosshair_visible": self.crosshair_visible,
            "dot_visible": self.dot_visible,
            "dot_radius": self.dot_radius,
            "dot_shape": self.dot_shape,
            "crosshair_color": self.crosshair_color,
            "dot_outer_color": self.dot_outer_color,
            "dot_inner_color": self.dot_inner_color,
            "disabled_keys": self.disabled_keys,
            "crosshair_alpha": self.crosshair_alpha,
            "dot_alpha": self.dot_alpha,
            "fade_on_shoot": self.fade_on_shoot_enabled,
            "crosshair_shape": self.crosshair_shape,
            "crosshair_image_path": self.crosshair_image_path,
            # 十字アドバンスド設定
            "crosshair_outline_enabled": self.crosshair_outline_enabled,
            "crosshair_outline_width": self.crosshair_outline_width,
            "crosshair_outline_alpha": self.crosshair_outline_alpha,
            "crosshair_vline_length": self.crosshair_vline_length,
            "crosshair_hline_length": self.crosshair_hline_length,
            "crosshair_thickness": self.crosshair_thickness,
            "crosshair_gap": self.crosshair_gap,
            "drawing_order": self.drawing_order,
            # 円アドバンスド設定
            "circle_outline_enabled": self.circle_outline_enabled,
            "circle_outline_width": self.circle_outline_width,
            "circle_outline_alpha": self.circle_outline_alpha,
            "circle_thickness": self.circle_thickness,
            "circle_diameter": self.circle_diameter,
            # 矢印 (シェブロン) アドバンスド設定
            "chevron_outline_enabled": self.chevron_outline_enabled,
            "chevron_outline_width": self.chevron_outline_width,
            "chevron_outline_alpha": self.chevron_outline_alpha,
            "chevron_thickness": self.chevron_thickness,
            "chevron_length": self.chevron_length,
            # 画像系クロスヘアのリサイズ設定
            "image_crosshair_size": self.image_crosshair_size,
        }

    def save_monitor_selection(self, index):
        self.selected_monitor_index = index
        self.save_global_config()

    def save_global_config(self):
        main_config = {
            "last_selected": self.last_selected_preset, 
            "overall_preset_folder": self.overall_preset_folder,
            "shape_preset_folder": self.shape_preset_folder,
            "monitor_apex": self.monitor_apex,
            "selected_monitor_index": self.selected_monitor_index,
            "toggle_hotkey": self.toggle_hotkey
        }
        config.save_global_config(main_config)

    def clean_up(self):
        self.mouse_listener.stop()
        # self.enable_all_keys() # This will be handled by overlay_utils.py
        # if self.toggle_hotkey: # This will be handled by overlay_hotkeys.py
        #     try:
        #         keyboard.remove_hotkey(self.toggle_hotkey)
        #     except (KeyError, AttributeError):
        #         pass
        self.save_global_config()
    #         pass
        self.save_global_config()
