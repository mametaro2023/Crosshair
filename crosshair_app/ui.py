import os
import json
import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
import keyboard

from . import utils
from . import config
from .dialogs import SettingsDialog, KeyCaptureDialog, UpdateDialog, show_update_dialog


class ControlPanel(QtWidgets.QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.setWindowTitle("Crosshair Control Panel")
        self.setGeometry(100, 100, 450, 100)
        self._panel_animations = []

        self.setObjectName("controlPanel")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)
        # Opaque 描画でゴースト抑制
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent, True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, False) # この行を追加

        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        # --- Main Layout ---
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Menu Bar ---
        menu_bar = QtWidgets.QMenuBar()
        settings_menu = menu_bar.addMenu("設定")
        settings_menu.addAction("保存先フォルダ...", self.open_settings)
        settings_menu.addSeparator()
        self.startup_action = settings_menu.addAction("PC起動時に自動実行する")
        self.startup_action.setCheckable(True)
        if utils.IS_WINDOWS:
            self.startup_action.setChecked(utils.is_in_startup(utils.APP_NAME))
            self.startup_action.triggered.connect(self.toggle_startup)
        else:
            self.startup_action.setEnabled(False)
        main_layout.setMenuBar(menu_bar)

        # --- Master Toggle ---
        self.master_toggle_btn = QtWidgets.QPushButton("オーバーレイ無効化")
        self.master_toggle_btn.setObjectName("masterToggleButton")
        self.master_toggle_btn.setToolTip("クロスヘアとドットの表示をまとめてON/OFFします")
        self.master_toggle_btn.clicked.connect(self.toggle_master_visibility)
        main_layout.addWidget(self.master_toggle_btn)

        # --- Presets Group ---
        presets_group = QtWidgets.QGroupBox("プリセット")
        presets_layout = QtWidgets.QHBoxLayout(presets_group)
        self.preset_box = QtWidgets.QComboBox()
        self.save_btn = QtWidgets.QPushButton("保存")
        self.save_btn.setProperty("accent", True)
        self.save_btn.clicked.connect(self.save_preset)
        presets_layout.addWidget(self.preset_box, 1)
        presets_layout.addWidget(self.save_btn)
        main_layout.addWidget(presets_group)

        # --- General Settings Group ---
        general_group = QtWidgets.QGroupBox("全般設定")
        general_layout = QtWidgets.QVBoxLayout(general_group)
        
        monitor_layout = QtWidgets.QHBoxLayout()
        monitor_label = QtWidgets.QLabel("表示モニター:")
        self.monitor_selection_box = QtWidgets.QComboBox()
        self.monitor_selection_box.currentIndexChanged.connect(self.monitor_changed)
        monitor_layout.addWidget(monitor_label)
        monitor_layout.addWidget(self.monitor_selection_box, 1)
        general_layout.addLayout(monitor_layout)

        self.apex_monitor_action = QtWidgets.QCheckBox("Apex Legendsを監視して自動ON/OFF")
        if utils.psutil:
            self.apex_monitor_action.setChecked(self.overlay.monitor_apex)
            self.apex_monitor_action.toggled.connect(self.toggle_apex_monitoring)
        else:
            self.apex_monitor_action.setEnabled(False)
            self.apex_monitor_action.setToolTip("この機能を利用するには 'psutil' ライブラリが必要です。(pip install psutil)")
        general_layout.addWidget(self.apex_monitor_action)

        self.fade_on_shoot_checkbox = QtWidgets.QCheckBox("射撃中はクロスヘアを薄くする")
        self.fade_on_shoot_checkbox.toggled.connect(self.toggle_fade_on_shoot)
        general_layout.addWidget(self.fade_on_shoot_checkbox)
        main_layout.addWidget(general_group)

        # --- Crosshair Group ---
        ch_group = QtWidgets.QGroupBox("クロスヘア")
        ch_layout = QtWidgets.QVBoxLayout(ch_group)

        self.crosshair_btn = QtWidgets.QCheckBox("クロスヘアを表示")
        self.crosshair_btn.toggled.connect(self.toggle_crosshair_button)
        ch_layout.addWidget(self.crosshair_btn)

        shape_layout = QtWidgets.QHBoxLayout()
        self.shape_box = QtWidgets.QComboBox()
        self.shape_box.addItems(["十字", "十字 (ギャップなし)", "円", "矢印 (シェブロン)", "MAME", "カスタム画像"])
        self.shape_box.currentTextChanged.connect(self.update_crosshair_shape)
        shape_layout.addWidget(QtWidgets.QLabel("形状:"))
        shape_layout.addWidget(self.shape_box, 1)
        ch_layout.addLayout(shape_layout)

        self.custom_image_widget = QtWidgets.QWidget()
        custom_image_layout = QtWidgets.QHBoxLayout(self.custom_image_widget)
        custom_image_layout.setContentsMargins(0, 5, 0, 0)
        select_image_btn = QtWidgets.QPushButton("画像を選択...")
        select_image_btn.clicked.connect(self.select_custom_image)
        self.custom_image_path_label = QtWidgets.QLabel("選択されていません")
        self.custom_image_path_label.setWordWrap(True)
        custom_image_layout.addWidget(select_image_btn)
        custom_image_layout.addWidget(self.custom_image_path_label, 1)
        ch_layout.addWidget(self.custom_image_widget)

        ch_color_layout, self.ch_color_square = self.make_color_button("色:", lambda: self.overlay.crosshair_color, self.set_crosshair_color, lambda: self.overlay.update())
        ch_layout.addLayout(ch_color_layout)

        alpha_layout = QtWidgets.QHBoxLayout()
        self.alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_value = QtWidgets.QLabel()
        self.alpha_slider.valueChanged.connect(self.update_alpha)
        alpha_layout.addWidget(QtWidgets.QLabel("透明度:"))
        alpha_layout.addWidget(self.alpha_slider)
        alpha_layout.addWidget(self.alpha_value)
        ch_layout.addLayout(alpha_layout)
        main_layout.addWidget(ch_group)

        # --- Dot Group ---
        dot_group = QtWidgets.QGroupBox("ドット")
        dot_layout = QtWidgets.QVBoxLayout(dot_group)

        self.dot_btn = QtWidgets.QCheckBox("ドットを表示")
        self.dot_btn.toggled.connect(self.toggle_dot_button)
        dot_layout.addWidget(self.dot_btn)

        dotsize_layout = QtWidgets.QHBoxLayout()
        self.dot_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.dot_slider.setRange(0, 100)
        self.dot_value = QtWidgets.QLabel()
        self.dot_slider.valueChanged.connect(self.update_dot_size)
        dotsize_layout.addWidget(QtWidgets.QLabel("サイズ:"))
        dotsize_layout.addWidget(self.dot_slider)
        dotsize_layout.addWidget(self.dot_value)
        dot_layout.addLayout(dotsize_layout)

        dot_out_color_layout, self.dot_out_color_square = self.make_color_button("外枠の色:", lambda: self.overlay.dot_outer_color, self.set_dot_outer_color, lambda: self.overlay.update())
        dot_in_color_layout, self.dot_in_color_square = self.make_color_button("内側の色:", lambda: self.overlay.dot_inner_color, self.set_dot_inner_color, lambda: self.overlay.update())
        dot_layout.addLayout(dot_out_color_layout)
        dot_layout.addLayout(dot_in_color_layout)

        dot_alpha_layout = QtWidgets.QHBoxLayout()
        self.dot_alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.dot_alpha_slider.setRange(0, 100)
        self.dot_alpha_value = QtWidgets.QLabel()
        self.dot_alpha_slider.valueChanged.connect(self.update_dot_alpha)
        dot_alpha_layout.addWidget(QtWidgets.QLabel("透明度:"))
        dot_alpha_layout.addWidget(self.dot_alpha_slider)
        dot_alpha_layout.addWidget(self.dot_alpha_value)
        dot_layout.addLayout(dot_alpha_layout)
        main_layout.addWidget(dot_group)

        # --- Keys Group ---
        keys_group = QtWidgets.QGroupBox("キー無効化")
        keys_layout = QtWidgets.QVBoxLayout(keys_group)
        self.disabled_keys_label = QtWidgets.QLabel("なし")
        self.disabled_keys_label.setWordWrap(True)
        keys_layout.addWidget(self.disabled_keys_label, 1)
        keys_btn_layout = QtWidgets.QHBoxLayout()
        disable_btn = QtWidgets.QPushButton("無効化キーを追加")
        disable_btn.clicked.connect(self.disable_key_gui)
        enable_btn = QtWidgets.QPushButton("無効化キーを削除")
        enable_btn.clicked.connect(self.enable_key_gui)
        keys_btn_layout.addWidget(disable_btn)
        keys_btn_layout.addWidget(enable_btn)
        keys_layout.addLayout(keys_btn_layout)
        enable_all_btn = QtWidgets.QPushButton("すべてのキーを有効化")
        enable_all_btn.clicked.connect(self.enable_all_keys_gui)
        keys_layout.addWidget(enable_all_btn)
        main_layout.addWidget(keys_group)

        main_layout.addStretch()

        # GroupBox の背景再描画を確実にし、半透明時の残像を抑える
        for _gb in (presets_group, general_group, ch_group, dot_group, keys_group):
            _gb.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            _gb.setAutoFillBackground(True)

        # --- Finalize ---
        self.update_control_panel_ui()
        self.load_presets()
        self.preset_box.currentIndexChanged.connect(self.load_selected_preset)
        
        if self.overlay.monitor_apex and utils.psutil:
            self.toggle_apex_monitoring(True)

        self.setWindowOpacity(0.0)
        self.animate_panel_show()
        self._pulse_once(self.save_btn, QtGui.QColor("#0078d7"))

    def make_color_button(self, label_text, getter, setter, update_callback):
        layout_ = QtWidgets.QHBoxLayout()
        button = QtWidgets.QPushButton(label_text)
        square = QtWidgets.QLabel()
        square.setFixedSize(24, 24)
        square.setStyleSheet(f"background-color: {getter()}; border: 1px solid #50555c; border-radius: 4px;")
        def pick_color():
            color = QtWidgets.QColorDialog.getColor(QtGui.QColor(getter()), self, "色を選択")
            if color.isValid(): 
                setter(color.name())
                square.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #50555c; border-radius: 4px;")
                update_callback()
                self.schedule_overlay_update()
        button.clicked.connect(pick_color)
        layout_.addWidget(button)
        layout_.addStretch()
        layout_.addWidget(square)
        return layout_, square

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

        # Apex監視が有効な場合は、ボタンの見た目を変更しない
        if hasattr(self, 'master_toggle_btn') and not self.overlay.monitor_apex:
            if self.overlay.master_enabled:
                self.master_toggle_btn.setText("オーバーレイ無効化")
                self.master_toggle_btn.setObjectName("masterToggleButton")
            else:
                self.master_toggle_btn.setText("オーバーレイ有効化")
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
                QtWidgets.QMessageBox.warning(self, "設定失敗", "スタートアップへの登録に失敗しました。\n管理者として実行すると解決する場合があります。 সন")
                self.startup_action.setChecked(False)
        else:
            if utils.remove_from_startup(utils.APP_NAME):
                QtWidgets.QMessageBox.information(self, "設定完了", "スタートアップ設定を解除しました。")
            else:
                QtWidgets.QMessageBox.warning(self, "設定失敗", "スタートアップからの登録解除に失敗しました。 سন")
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
            self.master_toggle_btn.setText("オーバーレイ自動制御中")
            self.master_toggle_btn.setObjectName("masterToggleButtonMonitoring")
            self.master_toggle_btn.setToolTip("Apex監視が有効なため、手動でのON/OFFはできません。")
            
            if not utils.psutil:
                QtWidgets.QMessageBox.warning(self, "ライブラリ不足", "この機能を利用するには 'psutil' が必要です。コマンドプロンプトで 'pip install psutil' を実行してください。")
                if hasattr(self, 'apex_monitor_action'):
                    self.apex_monitor_action.setChecked(False)
                return

            # 現在のゲームの状態を確認して即座に反映
            is_game_running = any(p.name() in utils.GAME_PROCESS_NAMES for p in utils.psutil.process_iter(['name']))
            self.set_master_enabled(is_game_running, manual_toggle=False)

            if self.overlay.game_monitor_thread is None:
                self.overlay.game_monitor_thread = utils.GameMonitorThread(utils.GAME_PROCESS_NAMES, self.overlay)
                self.overlay.game_monitor_thread.start()
                print("Apex Legendsの監視を開始しました。")
        else:
            # ボタンの表示を現在のオーバーレイ状態に基づいて元に戻す
            if self.overlay.master_enabled:
                self.master_toggle_btn.setText("オーバーレイ無効化")
                self.master_toggle_btn.setObjectName("masterToggleButton")
            else:
                self.master_toggle_btn.setText("オーバーレイ有効化")
                self.master_toggle_btn.setObjectName("masterToggleButtonActive")

            self.master_toggle_btn.setToolTip("クロスヘアとドットの表示をまとめてON/OFFします")
            if self.overlay.game_monitor_thread is not None:
                self.overlay.game_monitor_thread.stop()
                print("Apex Legendsの監視を停止しています...")
        
        self.master_toggle_btn.style().unpolish(self.master_toggle_btn)
        self.master_toggle_btn.style().polish(self.master_toggle_btn)

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
        self.schedule_overlay_update()

    def update_crosshair_shape(self, shape_text):
        self.overlay.crosshair_shape = shape_text
        self.custom_image_widget.setVisible(shape_text == "カスタム画像")
        self.schedule_overlay_update()

    def select_custom_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "画像を選択", "", "画像ファイル (*.png *.jpg *.bmp *.gif)")
        if path:
            self.overlay.crosshair_image_path = path
            self.custom_image_path_label.setText(os.path.basename(path))
            self.schedule_overlay_update()

    def toggle_dot_button(self, checked): 
        self.overlay.dot_visible = checked
        self.schedule_overlay_update()

    def update_dot_size(self, val): 
        self.overlay.dot_radius = val // 2
        self.dot_value.setText(str(val))
        self.schedule_overlay_update()

    def update_alpha(self, val): 
        alpha = round(val / 100, 2)
        self.overlay.crosshair_alpha = alpha
        self.alpha_value.setText(f"{alpha:.2f}")
        self.schedule_overlay_update()

    def update_dot_alpha(self, val): 
        alpha = round(val / 100, 2)
        self.overlay.dot_alpha = alpha
        self.dot_alpha_value.setText(f"{self.overlay.dot_alpha:.2f}")
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
            # 他の無効化キーを再ブロック後まとめて更新
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

    # --- 更新スロットリング関連 ---
    def schedule_overlay_update(self):
        # 更新を即座に実行
        self.overlay.is_dirty = True
        self._perform_deferred_update()

    def _perform_deferred_update(self):
        # 実際の update() と表示再構築
        self.overlay.update()
        if hasattr(self.overlay, '_set_dirty_and_update_display'):
            try:
                self.overlay._set_dirty_and_update_display()
            except Exception:
                pass

    # 背景を毎回明示的に塗りつぶして残像を防止
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(37, 41, 45))  # Window と同色でクリア
        super().paintEvent(event)

