import os
import keyboard
from PyQt5 import QtWidgets
from .. import utils
from ..editor.editor_dialog import EditorDialog
from ..dialogs import KeyCaptureDialog

def _on_alpha_input_finished(panel_self):
    def handler():
        original_value = panel_self.overlay.crosshair_alpha
        text = panel_self.alpha_value_edit.text()
        text = text.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
        try:
            value = float(text)
            value = int(value * 1000) / 1000.0 # 小数点以下第3位で切り捨て
            if value > 1.0: value = 1.0
            if value < 0.0: value = 0.0
            panel_self.alpha_slider.setValue(int(value * 100))
        except ValueError:
            panel_self.alpha_value_edit.setText(f"{original_value:.3f}")
    return handler

def _on_dot_size_input_finished(panel_self):
    def handler():
        original_value = panel_self.overlay.dot_radius * 2
        text = panel_self.dot_value_edit.text()
        text = text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        try:
            value = int(text)
            if value > panel_self.dot_slider.maximum(): value = panel_self.dot_slider.maximum()
            if value < panel_self.dot_slider.minimum(): value = 0
            panel_self.dot_slider.setValue(value)
        except ValueError:
            panel_self.dot_value_edit.setText(str(original_value))
    return handler

def _on_dot_alpha_input_finished(panel_self):
    def handler():
        original_value = panel_self.overlay.dot_alpha
        text = panel_self.dot_alpha_value_edit.text()
        text = text.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
        try:
            value = float(text)
            value = int(value * 1000) / 1000.0 # 小数点以下第3位で切り捨て
            if value > 1.0: value = 1.0
            if value < 0.0: value = 0.0
            panel_self.dot_alpha_slider.setValue(int(value * 100))
        except ValueError:
            panel_self.dot_alpha_value_edit.setText(f"{original_value:.3f}")
    return handler

def _on_dot_offset_x_input_finished(panel_self):
    def handler():
        original_value = panel_self.overlay.dot_offset_x
        text = panel_self.dot_offset_x_edit.text()
        text = text.translate(str.maketrans("０１２３４５６７８９－", "0123456789-"))
        try:
            value = int(text)
            if value > panel_self.dot_offset_x_slider.maximum(): value = panel_self.dot_offset_x_slider.maximum()
            if value < panel_self.dot_offset_x_slider.minimum(): value = 0
            
            panel_self.dot_offset_x_slider.blockSignals(True)
            panel_self.dot_offset_x_slider.setValue(value)
            panel_self.dot_offset_x_slider.blockSignals(False)

            panel_self.overlay.dot_offset_x = value
            panel_self.schedule_overlay_update()
        except ValueError:
            panel_self.dot_offset_x_edit.setText(str(original_value))
    return handler

def _on_dot_offset_y_input_finished(panel_self):
    def handler():
        original_value = panel_self.overlay.dot_offset_y
        text = panel_self.dot_offset_y_edit.text()
        text = text.translate(str.maketrans("０１２３４５６７８９－", "0123456789-"))
        try:
            value = int(text)
            if value > panel_self.dot_offset_y_slider.maximum(): value = panel_self.dot_offset_y_slider.maximum()
            if value < panel_self.dot_offset_y_slider.minimum(): value = 0

            panel_self.dot_offset_y_slider.blockSignals(True)
            panel_self.dot_offset_y_slider.setValue(value)
            panel_self.dot_offset_y_slider.blockSignals(False)

            panel_self.overlay.dot_offset_y = value
            panel_self.schedule_overlay_update()
        except ValueError:
            panel_self.dot_offset_y_edit.setText(str(original_value))
    return handler

# --- Generic Handler Factory ---

def _create_line_edit_handler(panel_self, edit_widget, slider, overlay_attr, is_float=False):
    def handler():
        original_value = getattr(panel_self.overlay, overlay_attr)
        text = edit_widget.text()
        text = text.translate(str.maketrans("０１２３４５６７８９．－", "0123456789.- "))
        try:
            value = float(text) if is_float else int(text)
            if is_float:
                value = int(value * 1000) / 1000.0
                if value > 1.0: value = 1.0
                if value < 0.0: value = 0.0
                slider.setValue(int(value * 100))
            else:
                if value > slider.maximum(): value = slider.maximum()
                if value < slider.minimum(): value = 0
                slider.setValue(value)
        except ValueError:
            if is_float:
                edit_widget.setText(f"{original_value:.3f}")
            else:
                edit_widget.setText(str(original_value))
    return handler


def update_crosshair_shape(self, shape_text):
    if shape_text == "新しく作る":
        previous_shape = self.overlay.crosshair_shape
        
        editor = EditorDialog(self, shape_preset_folder=self.overlay.shape_preset_folder)
        if editor.exec_() == QtWidgets.QDialog.Accepted:
            self.reload_shapes()
            if editor.saved_path:
                new_shape_name = os.path.splitext(os.path.basename(editor.saved_path))[0]
                self.shape_box.setCurrentText(new_shape_name)
        else:
            self.shape_box.setCurrentText(previous_shape)
        return

    self.overlay.crosshair_shape = shape_text

    if shape_text == "MAME":
        utils.download_mame_png_if_missing(self)
    
    self.schedule_overlay_update()
    self.update_control_panel_ui()

def select_custom_image(self):
    path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "画像を選択", "", "画像ファイル (*.png *.jpg *.bmp *.gif)")
    if path:
        self.overlay.crosshair_image_path = path
        self.custom_image_path_label.setText(os.path.basename(path))
        self.schedule_overlay_update()

def toggle_crosshair_button(self, checked): 
    self.overlay.crosshair_visible = checked
    self.schedule_overlay_update()

def toggle_dot_button(self, checked): 
    self.overlay.dot_visible = checked
    self.schedule_overlay_update()

def update_dot_size(self, val): 
    self.overlay.dot_radius = val // 2
    self.dot_value_edit.setText(str(val))
    self.schedule_overlay_update()

def update_alpha(self, val): 
    alpha = round(val / 100, 3)
    self.overlay.crosshair_alpha = alpha
    self.alpha_value_edit.setText(f"{alpha:.3f}")
    self.schedule_overlay_update()

def update_dot_alpha(self, val): 
    alpha = round(val / 100, 3)
    self.overlay.dot_alpha = alpha
    self.dot_alpha_value_edit.setText(f"{self.overlay.dot_alpha:.3f}")
    self.schedule_overlay_update()

def toggle_fade_on_shoot(self, checked):
    self.overlay.fade_on_shoot_enabled = checked
    self.schedule_overlay_update()

def toggle_antialiasing(self, checked):
    self.overlay.antialiasing_enabled = checked
    self.schedule_overlay_update()

def set_crosshair_color(self, val): 
    self.overlay.crosshair_color = val

def set_dot_outer_color(self, val): 
    self.overlay.dot_outer_color = val

def set_dot_inner_color(self, val): 
    self.overlay.dot_inner_color = val

def schedule_overlay_update(self):
    self.overlay.is_dirty = True
    self._perform_deferred_update()

def _perform_deferred_update(self):
    self.overlay.update()
    if hasattr(self.overlay, '_set_dirty_and_update_display'):
        try:
            self.overlay._set_dirty_and_update_display()
        except Exception:
            pass

def monitor_changed(self, index):
    if index >= 0 and index != self.overlay.selected_monitor_index:
        self.overlay.save_monitor_selection(index)
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setText("モニター設定を保存しました。")
        msg_box.setInformativeText("アプリケーションを再起動すると、選択したモニターで表示されます。")
        msg_box.setWindowTitle("再起動が必要です")
        restart_button = msg_box.addButton("今すぐ再起動", QtWidgets.QMessageBox.AcceptRole)
        msg_box.addButton("後で", QtWidgets.QMessageBox.RejectRole)
        msg_box.setStyleSheet("QLabel#qt_msgbox_label { min-width: 310px; }")
        msg_box.exec_()
        if msg_box.clickedButton() == restart_button:
            self.overlay.restart_application()

def disable_key_gui(self):
    def on_key_selected(key): 
        self.overlay.disable_key(key)
        self.disabled_keys_label.setText(", ".join(self.overlay.disabled_keys))
        self.schedule_overlay_update()
    dlg = KeyCaptureDialog(self, message="無効化したいキーを押してください（Enterキーは無効化できません）", key_callback=on_key_selected)
    dlg.exec_()

def enable_key_gui(self):
    if not self.overlay.disabled_keys:
        QtWidgets.QMessageBox.information(self, "情報", "無効化されているキーはありません。")
        return
    def on_key_selected(key):
        self.overlay.enable_key(key)
        self.disabled_keys_label.setText(", ".join(self.overlay.disabled_keys) if self.overlay.disabled_keys else "なし")
        for k in self.overlay.disabled_keys:
            if k != key: keyboard.block_key(k)
        self.schedule_overlay_update()
    for k in self.overlay.disabled_keys:
            try: keyboard.unblock_key(k)
            except: pass
    dlg = KeyCaptureDialog(self, message="有効化したいキーを押してください（現在無効化中のキー: " + ", ".join(self.overlay.disabled_keys) + "）", key_callback=on_key_selected)
    dlg.exec_()

def enable_all_keys_gui(self):
    self.overlay.enable_all_keys()
    self.disabled_keys_label.setText("なし")
    self.schedule_overlay_update()

def update_chevron_outline_enabled(self, checked):
    self.overlay.chevron_outline_enabled = checked
    self.schedule_overlay_update()

def update_chevron_outline_width(self, val):
    self.overlay.chevron_outline_width = val
    self.chevron_outline_width_edit.setText(str(val))
    self.schedule_overlay_update()

def update_chevron_thickness(self, val):
    self.overlay.chevron_thickness = val
    self.chevron_thickness_edit.setText(str(val))
    self.schedule_overlay_update()

def update_chevron_length(self, val):
    self.overlay.chevron_length = val
    self.chevron_length_edit.setText(str(val))
    self.schedule_overlay_update()

def update_image_crosshair_size(self, val):
    self.overlay.image_crosshair_size = val
    self.image_crosshair_size_edit.setText(str(val))
    self.schedule_overlay_update()

def update_crosshair_outline_alpha(self, val):
    alpha = round(val / 100, 3)
    self.overlay.crosshair_outline_alpha = alpha
    self.crosshair_outline_alpha_edit.setText(f"{alpha:.3f}")
    self.schedule_overlay_update()

def update_crosshair_inner_alpha(self, val):
    alpha = round(val / 100, 3)
    self.overlay.crosshair_inner_alpha = alpha
    self.crosshair_inner_alpha_edit.setText(f"{alpha:.3f}")
    self.schedule_overlay_update()

def update_circle_outline_alpha(self, val):
    alpha = round(val / 100, 3)
    self.overlay.circle_outline_alpha = alpha
    self.circle_outline_alpha_edit.setText(f"{alpha:.3f}")
    self.schedule_overlay_update()

def update_chevron_outline_alpha(self, val):
    alpha = round(val / 100, 3)
    self.overlay.chevron_outline_alpha = alpha
    self.chevron_outline_alpha_edit.setText(f"{alpha:.3f}")
    self.schedule_overlay_update()

def import_valorant_crosshair(self):
    code, ok = QtWidgets.QInputDialog.getText(self, "Valorantクロスヘアをインポート(ベータ版)", "Valorantクロスヘアコードを入力してください:")
    if ok and code:
        try:
            parsed_settings = utils.parse_valorant_crosshair_code(code)

            # Apply settings to overlay
            # Dot shape to "正方形"
            self.overlay.dot_shape = "正方形"
            self.dot_shape_box.setCurrentText("正方形") # Update UI

            # Crosshair shape to "十字"
            self.overlay.crosshair_shape = "十字"
            self.shape_box.setCurrentText("十字") # Update UI

            # Dot outer color to black
            self.overlay.dot_outer_color = "#000000"

            # Apply parsed settings
            settings_to_apply = {
                "crosshair_visible": "crosshair_visible", # Add this line
                "crosshair_outline_enabled": "crosshair_outline_enabled",
                "crosshair_outline_alpha": "crosshair_outline_alpha",
                "crosshair_outline_width": "crosshair_outline_width",
                "crosshair_inner_alpha": "crosshair_inner_alpha", # Add this line
                "dot_alpha": "dot_alpha", # Now correctly mapped from 'a' in utils.py
                "dot_radius": "dot_radius", # Mapped from 'z' in utils.py
                "crosshair_alpha": "crosshair_alpha",
                "crosshair_hline_length": "crosshair_hline_length",
                "crosshair_vline_length": "crosshair_vline_length",
                "crosshair_gap": "crosshair_gap",
                "crosshair_thickness": "crosshair_thickness",
                "crosshair_color": "crosshair_color",
                "dot_visible": "dot_visible", # Mapped from 'd' in utils.py
                # --- ここから外枠 ---
                "outer_line_enabled": "outer_line_enabled",
                "outer_line_alpha": "outer_line_alpha",
                "outer_hline_length": "outer_hline_length",
                "outer_vline_length": "outer_vline_length",
                "outer_gap": "outer_gap",
                "outer_line_thickness": "outer_line_thickness",
            }

            for parsed_key, overlay_attr in settings_to_apply.items():
                if parsed_key in parsed_settings:
                    setattr(self.overlay, overlay_attr, parsed_settings[parsed_key])

            # Automatically disable anti-aliasing for Valorant crosshairs
            self.overlay.antialiasing_enabled = False
            self.antialiasing_checkbox.setChecked(False) # Update UI

            # Special handling for crosshair_color as it also updates a UI element directly
            if "crosshair_color" in parsed_settings:
                self.ch_color_square.update_color(parsed_settings["crosshair_color"])
                # Dot inner color to crosshair color
                self.overlay.dot_inner_color = parsed_settings["crosshair_color"]
                self.dot_in_color_square.update_color(parsed_settings["crosshair_color"]) # Update UI

            self.schedule_overlay_update()
            self.update_control_panel_ui() # Update all UI elements

            QtWidgets.QMessageBox.information(self, "インポート成功", "Valorantクロスヘア設定をインポートしました。" )

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "インポート失敗", f"Valorantクロスヘアコードの解析に失敗しました:\n{e}")

def update_dot_shape(self, shape_text):
    self.overlay.dot_shape = shape_text
    self.schedule_overlay_update()
