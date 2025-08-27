import os
import json
from PyQt5 import QtCore, QtGui, QtWidgets
import keyboard

from . import utils
from . import config

# This function was already here
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

        QPushButton { background-color: #40454c; border: 1px solid #50555c; padding: 8px 12px; border-radius: 6px; color: #E0E0E0; }
        QPushButton:hover { background-color: #4a4f57; }
        QPushButton:pressed { background-color: #2a2e36; }
        QPushButton[accent="true"] { background-color: #0078d7; border: 1px solid #0088f7; color: #ffffff; font-weight: bold; }
        QPushButton[accent="true"]:hover { background-color: #0088f7; }
        QPushButton[accent="true"]:pressed { background-color: #0068c7; }

        QPushButton#masterToggleButton {
            background-color: #c0392b;
            border: 1px solid #e74c3c;
            font-weight: bold;
            padding: 10px 12px;
        }
        QPushButton#masterToggleButton:hover { background-color: #e74c3c; }

        QPushButton#masterToggleButtonActive {
            background-color: #27ae60;
            border: 1px solid #2ecc71;
            font-weight: bold;
            padding: 10px 12px;
        }
        QPushButton#masterToggleButtonActive:hover { background-color: #2ecc71; }

        QComboBox { background-color: #40454c; border: 1px solid #50555c; border-radius: 6px; padding: 6px 10px; }
        QComboBox QAbstractItemView { background-color: #2c3136; border: 1px solid #3c4048; selection-background-color: #0078d7; }

        QLabel { color: #E0E0E0; }

        QSlider::groove:horizontal { height: 6px; background: #3C4048; border-radius: 3px; }
        QSlider::handle:horizontal { background: #00aaff; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }

        QCheckBox { spacing: 8px; }
        QCheckBox::indicator { width: 18px; height: 18px; }
        QCheckBox::indicator:unchecked { border: 1px solid #3C4048; background: #2D2F36; border-radius: 4px; }
        QCheckBox::indicator:checked { border: 1px solid #00cc55; background: #00FF66; border-radius: 4px; }

        QFrame#SeparatorLine { background-color: #3C4048; max-height: 1px; min-height: 1px; }

        QToolTip { background-color: #2D2F36; color: #E0E0E0; border: 1px solid #3C4048; }
        """)

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
        cancel_button.clicked.connect(self.reject)
        self.layout().addWidget(cancel_button)
        self.resize(300, 100)

    def _on_key_press(self, event):
        key = event.name
        
        if key == "enter":
            QtCore.QMetaObject.invokeMethod(self, "_show_enter_error", QtCore.Qt.QueuedConnection)
            return

        self.captured_key = key
        QtCore.QMetaObject.invokeMethod(self, "accept", QtCore.Qt.QueuedConnection)
        return True

    @QtCore.pyqtSlot()
    def _show_enter_error(self):
        QtWidgets.QMessageBox.information(self, "無効化不可", "Enterキーは無効化できません。 সন")

    def exec_(self):
        self.hook = keyboard.on_press(self._on_key_press, suppress=True)
        result = super().exec_()
        keyboard.unhook(self.hook)
        if result == QtWidgets.QDialog.Accepted and self.key_callback and self.captured_key:
            self.key_callback(self.captured_key)
        return result

class ControlPanel(QtWidgets.QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.setWindowTitle("Crosshair Control Panel")
        self.setGeometry(100, 100, 400, 100)
        self._panel_animations = []

        self.setObjectName("controlPanel")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet("#controlPanel { background-color: #181A1B; border: 1px solid #2C2F33; }")

        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        shadow.setOffset(0, 12)
        self.setGraphicsEffect(shadow)

        layout = QtWidgets.QVBoxLayout()

        menu_bar = QtWidgets.QMenuBar()
        settings_menu = menu_bar.addMenu("環境設定")
        settings_menu.addAction("保存先フォルダを変更", self.open_settings)

        settings_menu.addSeparator()

        self.startup_action = QtWidgets.QAction("PC起動時に自動実行する", self, checkable=True)
        if utils.IS_WINDOWS:
            self.startup_action.setChecked(utils.is_in_startup(utils.APP_NAME))
            self.startup_action.triggered.connect(self.toggle_startup)
        else:
            self.startup_action.setEnabled(False)
            self.startup_action.setToolTip("この機能はWindowsでのみ利用可能です。")
        settings_menu.addAction(self.startup_action)

        settings_menu.addSeparator()

        self.apex_monitor_action = QtWidgets.QAction("Apex Legendsを監視して自動切替", self, checkable=True)
        self.apex_monitor_action.setToolTip("Apex Legendsの起動・終了に合わせてオーバーレイのON/OFFを自動で切り替えます。")

        if utils.psutil:
            self.apex_monitor_action.setChecked(self.overlay.monitor_apex)
            self.apex_monitor_action.triggered.connect(self.toggle_apex_monitoring)
        else:
            self.apex_monitor_action.setEnabled(False)
            self.apex_monitor_action.setToolTip("この機能を利用するには 'psutil' ライブラリが必要です。(pip install psutil)")
        settings_menu.addAction(self.apex_monitor_action)

        layout.setMenuBar(menu_bar)

        self.master_toggle_btn = QtWidgets.QPushButton("オーバーレイを無効化")
        self.master_toggle_btn.setObjectName("masterToggleButton")
        self.master_toggle_btn.setToolTip("クロスヘアとドットの表示をまとめてON/OFFします")
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton)
        self.master_toggle_btn.setIcon(icon)
        self.master_toggle_btn.clicked.connect(self.toggle_master_visibility)
        layout.addWidget(self.master_toggle_btn)

        if self.apex_monitor_action.isChecked():
            self.master_toggle_btn.setEnabled(False)
            self.master_toggle_btn.setToolTip("Apex監視が有効なため、手動でのON/OFFはできません。")

        line_master = QtWidgets.QFrame()
        line_master.setObjectName("SeparatorLine")
        line_master.setFrameShape(QtWidgets.QFrame.HLine)
        line_master.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line_master)

        self.detail_controls = []

        monitor_layout = QtWidgets.QHBoxLayout()
        monitor_label = QtWidgets.QLabel("表示モニター")
        self.monitor_selection_box = QtWidgets.QComboBox()
        self.monitor_selection_box.currentIndexChanged.connect(self.monitor_changed)
        monitor_layout.addWidget(monitor_label)
        monitor_layout.addWidget(self.monitor_selection_box)
        layout.addLayout(monitor_layout)
        self.detail_controls.extend([monitor_label, self.monitor_selection_box])

        preset_layout = QtWidgets.QHBoxLayout()
        self.preset_box = QtWidgets.QComboBox()
        self.save_btn = QtWidgets.QPushButton("現在の設定を保存")
        self.save_btn.setProperty("accent", True)
        self.save_btn.clicked.connect(self.save_preset)
        preset_layout.addWidget(self.preset_box)
        preset_layout.addWidget(self.save_btn)
        layout.addLayout(preset_layout)
        self.detail_controls.extend([self.preset_box, self.save_btn])

        line = QtWidgets.QFrame()
        line.setObjectName("SeparatorLine")
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)
        self.detail_controls.append(line)

        self.crosshair_btn = QtWidgets.QPushButton("クロスヘア表示/非表示"); self.crosshair_state = QtWidgets.QLabel()
        self.crosshair_btn.clicked.connect(self.toggle_crosshair_button)
        h1 = QtWidgets.QHBoxLayout(); h1.addWidget(self.crosshair_btn); h1.addWidget(self.crosshair_state); layout.addLayout(h1)
        self.detail_controls.extend([self.crosshair_btn, self.crosshair_state])

        shape_layout = QtWidgets.QHBoxLayout()
        shape_label = QtWidgets.QLabel("クロスヘア形状")
        self.shape_box = QtWidgets.QComboBox()
        self.shape_box.addItems(["十字", "十字 (ギャップなし)", "円", "矢印 (シェブロン)", "MAME", "カスタム画像"])
        self.shape_box.currentTextChanged.connect(self.update_crosshair_shape)
        shape_layout.addWidget(shape_label)
        shape_layout.addWidget(self.shape_box)
        layout.addLayout(shape_layout)
        self.detail_controls.extend([shape_label, self.shape_box])

        # Custom image selection widget (initially hidden)
        self.custom_image_widget = QtWidgets.QWidget()
        custom_image_layout = QtWidgets.QHBoxLayout()
        self.custom_image_widget.setLayout(custom_image_layout)
        custom_image_layout.setContentsMargins(0, 5, 0, 0)
        select_image_btn = QtWidgets.QPushButton("画像を選択...")
        select_image_btn.clicked.connect(self.select_custom_image)
        self.custom_image_path_label = QtWidgets.QLabel("選択されていません")
        self.custom_image_path_label.setWordWrap(True)
        custom_image_layout.addWidget(select_image_btn)
        custom_image_layout.addWidget(self.custom_image_path_label, 1)
        layout.addWidget(self.custom_image_widget)
        self.detail_controls.extend([self.custom_image_widget, select_image_btn, self.custom_image_path_label])

        self.dot_btn = QtWidgets.QPushButton("ドット表示/非表示"); self.dot_state = QtWidgets.QLabel()
        self.dot_btn.clicked.connect(self.toggle_dot_button)
        h2 = QtWidgets.QHBoxLayout(); h2.addWidget(self.dot_btn); h2.addWidget(self.dot_state); layout.addLayout(h2)
        self.detail_controls.extend([self.dot_btn, self.dot_state])

        dotsize_layout = QtWidgets.QHBoxLayout(); dotsize_label = QtWidgets.QLabel("ドットサイズ")
        self.dot_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.dot_slider.setMinimum(0); self.dot_slider.setMaximum(100)
        self.dot_value = QtWidgets.QLabel(); self.dot_slider.valueChanged.connect(self.update_dot_size)
        dotsize_layout.addWidget(dotsize_label); dotsize_layout.addWidget(self.dot_slider); dotsize_layout.addWidget(self.dot_value); layout.addLayout(dotsize_layout)
        self.detail_controls.extend([dotsize_label, self.dot_slider, self.dot_value])

        def make_color_button(label_text, getter, setter, update_callback):
            layout_ = QtWidgets.QHBoxLayout(); button = QtWidgets.QPushButton(label_text)
            square = QtWidgets.QLabel(); square.setFixedSize(20, 20)
            def pick_color():
                color = QtWidgets.QColorDialog.getColor(QtGui.QColor(getter()))
                if color.isValid(): 
                    setter(color.name())
                    square.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #3C4048; border-radius: 4px;")
                    update_callback()
                    self.overlay._set_dirty_and_update_display()
            button.clicked.connect(pick_color)
            layout_.addWidget(button); layout_.addWidget(square); return layout_, square
        
        color_update_cb = lambda: self.overlay.update()
        ch_color_layout, self.ch_color_square = make_color_button("クロスヘア色", lambda: self.overlay.crosshair_color, self.set_crosshair_color, color_update_cb)
        dot_out_color_layout, self.dot_out_color_square = make_color_button("ドット外枠色", lambda: self.overlay.dot_outer_color, self.set_dot_outer_color, color_update_cb)
        dot_in_color_layout, self.dot_in_color_square = make_color_button("ドット内側色", lambda: self.overlay.dot_inner_color, self.set_dot_inner_color, color_update_cb)
        layout.addLayout(ch_color_layout); layout.addLayout(dot_out_color_layout); layout.addLayout(dot_in_color_layout)
        for i in range(ch_color_layout.count()): self.detail_controls.append(ch_color_layout.itemAt(i).widget())
        for i in range(dot_out_color_layout.count()): self.detail_controls.append(dot_out_color_layout.itemAt(i).widget())
        for i in range(dot_in_color_layout.count()): self.detail_controls.append(dot_in_color_layout.itemAt(i).widget())

        alpha_layout = QtWidgets.QHBoxLayout(); alpha_label = QtWidgets.QLabel("クロスヘア透明度")
        self.alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.alpha_slider.setMinimum(0); self.alpha_slider.setMaximum(100)
        self.alpha_value = QtWidgets.QLabel(); self.alpha_slider.valueChanged.connect(self.update_alpha)
        alpha_layout.addWidget(alpha_label); alpha_layout.addWidget(self.alpha_slider); alpha_layout.addWidget(self.alpha_value); layout.addLayout(alpha_layout)
        self.detail_controls.extend([alpha_label, self.alpha_slider, self.alpha_value])

        dot_alpha_layout = QtWidgets.QHBoxLayout(); dot_alpha_label = QtWidgets.QLabel("ドット透明度")
        self.dot_alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.dot_alpha_slider.setMinimum(0); self.dot_alpha_slider.setMaximum(100)
        self.dot_alpha_value = QtWidgets.QLabel(); self.dot_alpha_slider.valueChanged.connect(self.update_dot_alpha)
        dot_alpha_layout.addWidget(dot_alpha_label); dot_alpha_layout.addWidget(self.dot_alpha_slider); dot_alpha_layout.addWidget(self.dot_alpha_value); layout.addLayout(dot_alpha_layout)
        self.detail_controls.extend([dot_alpha_label, self.dot_alpha_slider, self.dot_alpha_value])

        self.fade_on_shoot_checkbox = QtWidgets.QCheckBox("射撃中はクロスヘアを薄くする")
        self.fade_on_shoot_checkbox.toggled.connect(self.toggle_fade_on_shoot)
        layout.addWidget(self.fade_on_shoot_checkbox)
        self.detail_controls.append(self.fade_on_shoot_checkbox)

        disable_layout = QtWidgets.QHBoxLayout(); disable_btn = QtWidgets.QPushButton("キーを無効化")
        self.disabled_keys_label = QtWidgets.QLabel(", ".join(self.overlay.disabled_keys) if self.overlay.disabled_keys else "なし"); self.disabled_keys_label.setWordWrap(True)
        disable_btn.clicked.connect(self.disable_key_gui); disable_layout.addWidget(disable_btn); disable_layout.addWidget(self.disabled_keys_label); layout.addLayout(disable_layout)
        self.detail_controls.extend([disable_btn, self.disabled_keys_label])

        enable_btn = QtWidgets.QPushButton("キーを有効化"); enable_btn.clicked.connect(self.enable_key_gui); layout.addWidget(enable_btn)
        enable_all_btn = QtWidgets.QPushButton("すべてのキーを有効化"); enable_all_btn.clicked.connect(self.enable_all_keys_gui); layout.addWidget(enable_all_btn)
        self.detail_controls.extend([enable_btn, enable_all_btn])

        self.setLayout(layout)
        
        self.update_control_panel_ui()
        
        self.load_presets()
        self.preset_box.currentIndexChanged.connect(self.load_selected_preset)
        
        if self.overlay.monitor_apex and utils.psutil:
            self.toggle_apex_monitoring(True)

        self.setWindowOpacity(0.0)
        self.animate_panel_show()
        self._pulse_once(self.save_btn, QtGui.QColor("#00FF66"))

    def closeEvent(self, event):
        if self.overlay.is_dirty:
            reply = QtWidgets.QMessageBox.question(
                self, "保存されていません",
                "現在の設定はプリセットとして保存されていません。保存しますか？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel
            )
            if reply == QtWidgets.QMessageBox.Yes:
                if not self.save_preset(): 
                    event.ignore()
                    return
            elif reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                return
        event.accept()
        self.overlay.close()

    def load_presets(self):
        self.preset_box.blockSignals(True)
        self.preset_box.clear()
        
        self.preset_box.addItem(self.overlay.UNSAVED_PRESET_TEXT)
        self.preset_box.addItem("デフォルト設定")
        self.overlay.presets = {"デフォルト設定": self.overlay.default_config}

        for file in os.listdir(self.overlay.preset_folder):
            if file.endswith(config.PRESET_EXTENSION):
                name = os.path.splitext(file)[0]
                path = os.path.join(self.overlay.preset_folder, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.overlay.presets[name] = data
                    self.preset_box.addItem(name)
                except Exception as e:
                    print(f"プリセット読み込み失敗: {file}: {e}")

        if self.overlay.is_dirty:
            self.preset_box.setCurrentIndex(0)
        elif self.overlay.last_selected_preset in self.overlay.presets:
            index = self.preset_box.findText(self.overlay.last_selected_preset)
            self.preset_box.setCurrentIndex(index)
        else:
            self.preset_box.setCurrentIndex(0)

        self.preset_box.blockSignals(False)

    def save_preset(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "プリセットを保存", os.path.join(self.overlay.preset_folder, "preset" + config.PRESET_EXTENSION),
            f"プリセットファイル (*{config.PRESET_EXTENSION})")
        if path:
            if not path.endswith(config.PRESET_EXTENSION):
                path += config.PRESET_EXTENSION
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.overlay.get_config(), f, indent=4)
                
                self.overlay.last_selected_preset = os.path.splitext(os.path.basename(path))[0]
                self.overlay.save_global_config()
                self.load_presets()
                self.overlay.is_dirty = False
                return True
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "保存失敗", str(e))
        return False

    def load_selected_preset(self):
        name = self.preset_box.currentText()
        if name == self.overlay.UNSAVED_PRESET_TEXT:
            return
        
        config_to_load = self.overlay.presets.get(name, self.overlay.default_config)
        self.overlay.apply_config(config_to_load)
        
        self.overlay.last_selected_preset = name
        self.overlay.save_global_config()
        print(f"プリセット {name} を読み込みました")
        
        self.update_control_panel_ui()
        self.overlay.update()
        self.overlay.is_dirty = False

    def open_settings(self):
        dlg = SettingsDialog(self, self.overlay.preset_folder)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_path = dlg.get_selected_path()
            if new_path:
                self.overlay.preset_folder = new_path
                os.makedirs(self.overlay.preset_folder, exist_ok=True)
                self.overlay.save_global_config()
                self.load_presets()

    def set_master_enabled(self, enabled, manual_toggle=False):
        if self.overlay.master_enabled == enabled:
            return

        self.overlay.master_enabled = enabled

        if manual_toggle and hasattr(self, 'detail_controls'):
            for widget in self.detail_controls:
                widget.setEnabled(self.overlay.master_enabled)

        if hasattr(self, 'master_toggle_btn'):
            if self.overlay.master_enabled:
                self.master_toggle_btn.setText("オーバーレイを無効化")
                icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton)
                self.master_toggle_btn.setIcon(icon)
                self.master_toggle_btn.setObjectName("masterToggleButton")
            else:
                self.master_toggle_btn.setText("オーバーレイ有効化")
                icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton)
                self.master_toggle_btn.setIcon(icon)
                self.master_toggle_btn.setObjectName("masterToggleButtonActive")
            
            self.master_toggle_btn.style().unpolish(self.master_toggle_btn)
            self.master_toggle_btn.style().polish(self.master_toggle_btn)

        self.overlay.update()

    def toggle_master_visibility(self):
        self.set_master_enabled(not self.overlay.master_enabled, manual_toggle=True)

    def toggle_startup(self, checked):
        path = utils.get_executable_path()
        if checked:
            if utils.add_to_startup(utils.APP_NAME, path):
                QtWidgets.QMessageBox.information(self, "設定完了", "PC起動時に自動実行するよう設定しました。")
            else:
                QtWidgets.QMessageBox.warning(self, "設定失敗", "スタートアップへの登録に失敗しました。\n管理者として実行すると解決する場合があります。")
                self.startup_action.setChecked(False)
        else:
            if utils.remove_from_startup(utils.APP_NAME):
                QtWidgets.QMessageBox.information(self, "設定完了", "スタートアップ設定を解除しました。")
            else:
                QtWidgets.QMessageBox.warning(self, "設定失敗", "スタートアップからの登録解除に失敗しました。")
                self.startup_action.setChecked(True)

    @QtCore.pyqtSlot(bool)
    def on_game_state_changed(self, is_running):
        print(f"ゲーム状態の変更を検知: {{'実行中' if is_running else '終了'}}")
        if self.overlay.monitor_apex:
            self.set_master_enabled(is_running, manual_toggle=False)

    def toggle_apex_monitoring(self, checked):
        self.overlay.monitor_apex = checked
        self.overlay.save_global_config()

        self.master_toggle_btn.setEnabled(not checked)
        if checked:
            self.master_toggle_btn.setToolTip("Apex監視が有効なため、手動でのON/OFFはできません。")
            if not utils.psutil:
                QtWidgets.QMessageBox.warning(self, "ライブラリ不足", "この機能を利用するには 'psutil' が必要です。コマンドプロンプトで 'pip install psutil' を実行してください。 সন")
                if hasattr(self, 'apex_monitor_action'):
                    self.apex_monitor_action.setChecked(False)
                return

            if self.overlay.game_monitor_thread is None:
                self.overlay.game_monitor_thread = utils.GameMonitorThread(utils.GAME_PROCESS_NAME, self.overlay)
                self.overlay.game_monitor_thread.gameRunning.connect(self.on_game_state_changed)
                self.overlay.game_monitor_thread.finished.connect(self.on_monitor_thread_finished)
                self.overlay.game_monitor_thread.start()
                print("Apex Legendsの監視を開始しました。")
        else:
            self.master_toggle_btn.setToolTip("クロスヘアとドットの表示をまとめてON/OFFします")
            if self.overlay.game_monitor_thread is not None:
                self.overlay.game_monitor_thread.stop()
                self.overlay.game_monitor_thread.quit()
                print("Apex Legendsの監視を停止しています...")

    @QtCore.pyqtSlot()
    def on_monitor_thread_finished(self):
        print("Apex Legendsの監視を停止しました。")
        self.overlay.game_monitor_thread = None

    def animate_panel_show(self) -> None:
        fade = QtCore.QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(300)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        end_geo = self.geometry()
        start_geo = QtCore.QRect(end_geo.x(), end_geo.y() - 20, end_geo.width(), end_geo.height())
        slide = QtCore.QPropertyAnimation(self, b"geometry")
        slide.setDuration(350)
        slide.setStartValue(start_geo)
        slide.setEndValue(end_geo)
        slide.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        group = QtCore.QParallelAnimationGroup(self)
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
        self.monitor_selection_box.blockSignals(True)
        self.shape_box.blockSignals(True)
        self.dot_slider.blockSignals(True)
        self.alpha_slider.blockSignals(True)
        self.dot_alpha_slider.blockSignals(True)
        self.fade_on_shoot_checkbox.blockSignals(True)
        self.crosshair_btn.blockSignals(True)
        self.dot_btn.blockSignals(True)

        self.monitor_selection_box.setCurrentIndex(self.overlay.selected_monitor_index)
        self.crosshair_btn.setChecked(self.overlay.crosshair_visible)
        self.dot_btn.setChecked(self.overlay.dot_visible)
        self.shape_box.setCurrentText(self.overlay.crosshair_shape)
        
        is_custom_image = self.overlay.crosshair_shape == "カスタム画像"
        self.custom_image_widget.setVisible(is_custom_image)
        if is_custom_image:
            path = self.overlay.crosshair_image_path
            if path and os.path.exists(path):
                self.custom_image_path_label.setText(os.path.basename(path))
            else:
                self.custom_image_path_label.setText("選択されていません")

        self.dot_slider.setValue(self.overlay.dot_radius * 2)
        self.dot_value.setText(str(self.overlay.dot_radius * 2))
        self.ch_color_square.setStyleSheet(f"background-color: {self.overlay.crosshair_color}; border: 1px solid #50555c; border-radius: 4px;")
        self.dot_out_color_square.setStyleSheet(f"background-color: {self.overlay.dot_outer_color}; border: 1px solid #50555c; border-radius: 4px;")
        self.dot_in_color_square.setStyleSheet(f"background-color: {self.overlay.dot_inner_color}; border: 1px solid #50555c; border-radius: 4px;")
        self.alpha_slider.setValue(int(self.overlay.crosshair_alpha * 100))
        self.alpha_value.setText(f"{self.overlay.crosshair_alpha:.2f}")
        self.dot_alpha_slider.setValue(int(self.overlay.dot_alpha * 100))
        self.dot_alpha_value.setText(f"{self.overlay.dot_alpha:.2f}")
        self.fade_on_shoot_checkbox.setChecked(self.overlay.fade_on_shoot_enabled)
        self.disabled_keys_label.setText(", ".join(self.overlay.disabled_keys) if self.overlay.disabled_keys else "なし")

        self.monitor_selection_box.blockSignals(False)
        self.shape_box.blockSignals(False)
        self.dot_slider.blockSignals(False)
        self.alpha_slider.blockSignals(False)
        self.dot_alpha_slider.blockSignals(False)
        self.fade_on_shoot_checkbox.blockSignals(False)
        self.crosshair_btn.blockSignals(False)
        self.dot_btn.blockSignals(False)

    def monitor_changed(self, index):
        if index >= 0 and index != self.overlay.selected_monitor_index:
            self.overlay.save_monitor_selection(index)
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setText("モニター設定を保存しました。")
            msg_box.setInformativeText("アプリケーションを再起動すると、選択したモニターで表示されます。")
            msg_box.setWindowTitle("再起動が必要です")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()

    def toggle_crosshair_button(self, checked): 
        self.overlay.crosshair_visible = checked
        self.overlay.update()
        self.overlay._set_dirty_and_update_display()

    def update_crosshair_shape(self, shape_text):
        self.overlay.crosshair_shape = shape_text
        self.custom_image_widget.setVisible(shape_text == "カスタム画像")
        self.overlay.update()
        self.overlay._set_dirty_and_update_display()

    def select_custom_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "画像を選択", "", "画像ファイル (*.png *.jpg *.bmp *.gif)")
        if path:
            self.overlay.crosshair_image_path = path
            self.custom_image_path_label.setText(os.path.basename(path))
            self.overlay.update()
            self.overlay._set_dirty_and_update_display()

    def toggle_dot_button(self, checked): 
        self.overlay.dot_visible = checked
        self.overlay.update()
        self.overlay._set_dirty_and_update_display()

    def update_dot_size(self, val): 
        self.overlay.dot_radius = val // 2
        self.dot_value.setText(str(val))
        self.overlay.update()
        self.overlay._set_dirty_and_update_display()

    def update_alpha(self, val): 
        alpha = round(val / 100, 2)
        self.overlay.crosshair_alpha = alpha
        self.alpha_value.setText(f"{alpha:.2f}")
        self.overlay.update()
        self.overlay._set_dirty_and_update_display()

    def update_dot_alpha(self, val): 
        alpha = round(val / 100, 2)
        self.overlay.dot_alpha = alpha
        self.dot_alpha_value.setText(f"{alpha:.2f}")
        self.overlay.update()
        self.overlay._set_dirty_and_update_display()

    def toggle_fade_on_shoot(self, checked):
        self.overlay.fade_on_shoot_enabled = checked
        self.overlay.update()
        self.overlay._set_dirty_and_update_display()

    def set_crosshair_color(self, val): 
        self.overlay.crosshair_color = val

    def set_dot_outer_color(self, val): 
        self.overlay.dot_outer_color = val

    def set_dot_inner_color(self, val): 
        self.overlay.dot_inner_color = val

    def disable_key_gui(self):
        def on_key_selected(key): 
            self.overlay.disable_key(key)
            self.disabled_keys_label.setText(", ".join(self.overlay.disabled_keys))
            self.overlay.update()
            self.overlay._set_dirty_and_update_display()
        dlg = KeyCaptureDialog(self, message="無効化したいキーを押してください（Enterキーは無効化できません）", key_callback=on_key_selected)
        dlg.exec_()

    def enable_key_gui(self):
        if not self.overlay.disabled_keys:
            QtWidgets.QMessageBox.information(self, "情報", "無効化されているキーはありません。")
            return
        
        def on_key_selected(key):
            self.overlay.enable_key(key)
            self.disabled_keys_label.setText(", ".join(self.overlay.disabled_keys) if self.overlay.disabled_keys else "なし")
            self.overlay.update()
            for k in self.overlay.disabled_keys:
                if k != key: keyboard.block_key(k)
        
        for k in self.overlay.disabled_keys:
             try: keyboard.unblock_key(k)
             except: pass
        dlg = KeyCaptureDialog(self, message="有効化したいキーを押してください（現在無効化中のキー: " + ", ".join(self.overlay.disabled_keys) + "）", key_callback=on_key_selected)
        dlg.exec_()

    def enable_all_keys_gui(self):
        self.overlay.enable_all_keys()
        self.disabled_keys_label.setText("なし")
        self.overlay.update()
        self.overlay._set_dirty_and_update_display()