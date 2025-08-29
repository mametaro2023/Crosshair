import os
import keyboard
from PyQt5 import QtWidgets
from .. import utils
from ..editor.editor_dialog import EditorDialog
from ..dialogs import KeyCaptureDialog

def _on_alpha_input_finished(self):
    original_value = self.overlay.crosshair_alpha
    text = self.alpha_value_edit.text()
    text = text.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
    try:
        value = float(text)
        value = int(value * 100) / 100.0
        if value > 1.0: value = 1.0
        if value < 0.0: value = 0.0
        self.alpha_slider.setValue(int(value * 100))
    except ValueError:
        self.alpha_value_edit.setText(f"{original_value:.2f}")

def _on_dot_size_input_finished(self):
    original_value = self.overlay.dot_radius * 2
    text = self.dot_value_edit.text()
    text = text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    try:
        value = int(text)
        if value > 100: value = 100
        if value < 0: value = 0
        self.dot_slider.setValue(value)
    except ValueError:
        self.dot_value_edit.setText(str(original_value))

def _on_dot_alpha_input_finished(self):
    original_value = self.overlay.dot_alpha
    text = self.dot_alpha_value_edit.text()
    text = text.translate(str.maketrans("０１２３４５６７８９．", "0123456789."))
    try:
        value = float(text)
        value = int(value * 100) / 100.0
        if value > 1.0: value = 1.0
        if value < 0.0: value = 0.0
        self.dot_alpha_slider.setValue(int(value * 100))
    except ValueError:
        self.dot_alpha_value_edit.setText(f"{original_value:.2f}")

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
    alpha = round(val / 100, 2)
    self.overlay.crosshair_alpha = alpha
    self.alpha_value_edit.setText(f"{alpha:.2f}")
    self.schedule_overlay_update()

def update_dot_alpha(self, val): 
    alpha = round(val / 100, 2)
    self.overlay.dot_alpha = alpha
    self.dot_alpha_value_edit.setText(f"{self.overlay.dot_alpha:.2f}")
    self.schedule_overlay_update()

def toggle_fade_on_shoot(self, checked):
    self.overlay.fade_on_shoot_enabled = checked
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