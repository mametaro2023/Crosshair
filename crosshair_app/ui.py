import os
import json
import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
import keyboard

from . import utils
from . import config
from .dialogs import SettingsDialog, KeyCaptureDialog
from .ui_components import tab_general, tab_crosshair, tab_dot, tab_keys
from .editor.editor_dialog import EditorDialog


class ControlPanel(QtWidgets.QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.setWindowTitle("Crosshair Control Panel")
        self.setGeometry(100, 100, 450, 100)
        self._panel_animations = []

        self.setObjectName("controlPanel")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

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
        self._create_menu_bar(main_layout)

        # --- Master Toggle ---
        self.master_toggle_btn = QtWidgets.QPushButton("オーバーレイ無効化")
        self.master_toggle_btn.setObjectName("masterToggleButton")
        self.master_toggle_btn.setToolTip("クロスヘアとドットの表示をまとめてON/OFFします")
        self.master_toggle_btn.clicked.connect(self.toggle_master_visibility)
        main_layout.addWidget(self.master_toggle_btn)

        # --- Presets Group ---
        self._create_presets_group(main_layout)

        # --- Tab Widget for Settings ---
        self._create_tab_widget(main_layout)

        # --- Finalize ---
        self.reload_shapes() # 静的なリストの代わりに動的に読み込む
        self.update_control_panel_ui()
        self.load_presets() # プリセットのロードはUI更新の後に行う
        self.preset_box.currentIndexChanged.connect(self.load_selected_preset)
        
        if self.overlay.monitor_apex and utils.psutil:
            self.toggle_apex_monitoring(True)

        self.alpha_value_edit.editingFinished.connect(self._on_alpha_input_finished)
        self.dot_value_edit.editingFinished.connect(self._on_dot_size_input_finished)
        self.dot_alpha_value_edit.editingFinished.connect(self._on_dot_alpha_input_finished)

        # 最後にボタンの表示を更新して、ホットキー表示を確実に行う
        self.update_master_toggle_button_ui()

        self.setWindowOpacity(0.0)
        self.animate_panel_show()
        self._pulse_once(self.save_btn, QtGui.QColor("#0078d7"))

    def _create_menu_bar(self, parent_layout):
        menu_bar = QtWidgets.QMenuBar()
        settings_menu = menu_bar.addMenu("設定")
        settings_menu.addAction("保存先フォルダ...", self.open_settings)
        self.hotkey_action = settings_menu.addAction("ショートカットキー設定...")
        self.hotkey_action.triggered.connect(self.open_hotkey_settings)
        self.update_hotkey_menu_text()

        settings_menu.addSeparator()
        self.startup_action = settings_menu.addAction("PC起動時に自動実行する")
        self.startup_action.setCheckable(True)
        if utils.IS_WINDOWS:
            self.startup_action.setChecked(utils.is_in_startup(utils.APP_NAME))
            self.startup_action.triggered.connect(self.toggle_startup)
        else:
            self.startup_action.setEnabled(False)
        parent_layout.setMenuBar(menu_bar)

    def _create_presets_group(self, parent_layout):
        presets_group = QtWidgets.QGroupBox("プリセット")
        presets_layout = QtWidgets.QHBoxLayout(presets_group)
        self.preset_box = QtWidgets.QComboBox()
        self.save_btn = QtWidgets.QPushButton("保存")
        self.save_btn.setProperty("accent", True)
        self.save_btn.clicked.connect(self.save_preset)
        presets_layout.addWidget(self.preset_box, 1)
        presets_layout.addWidget(self.save_btn)
        parent_layout.addWidget(presets_group)

    def _create_tab_widget(self, parent_layout):
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.setObjectName("settingsTab")
        
        general_tab = tab_general.create_tab(self)
        ch_tab = tab_crosshair.create_tab(self)
        dot_tab = tab_dot.create_tab(self)
        keys_tab = tab_keys.create_tab(self)

        tab_widget.addTab(general_tab, "全般")
        tab_widget.addTab(ch_tab, "クロスヘア")
        tab_widget.addTab(dot_tab, "ドット")
        tab_widget.addTab(keys_tab, "キー無効化")

        parent_layout.addWidget(tab_widget)

    # --- Event Handlers & Slots ---

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

    def open_hotkey_settings(self):
        self.overlay.unregister_toggle_hotkey()
        def on_key_selected(key):
            self.overlay.set_toggle_hotkey(key)
            self.overlay.save_global_config()
            self.update_hotkey_menu_text()
            self.update_master_toggle_button_ui()
            QtWidgets.QMessageBox.information(self, "設定完了", f"表示切替ショートカットキーを '{key}' に設定しました。")
        dlg = KeyCaptureDialog(self,
                               message=f"新しいショートカットキーを押してください\n(現在の設定: {self.overlay.toggle_hotkey})",
                               key_callback=on_key_selected)
        result = dlg.exec_()
        if result == QtWidgets.QDialog.Rejected:
            self.overlay.register_toggle_hotkey()

    def reload_shapes(self):
        """利用可能なクロスヘア形状を動的に読み込む"""
        if not hasattr(self, 'shape_box'):
            return
            
        current_selection = self.shape_box.currentText()
        
        self.shape_box.blockSignals(True)
        self.shape_box.clear()

        # 基本形状
        shapes = ["十字", "十字 (ギャップなし)", "円", "矢印 (シェブロン)"]
        self.shape_box.addItems(shapes)

        # カスタム形状 (.crshr)
        try:
            custom_shapes = [os.path.splitext(f)[0] for f in os.listdir(self.overlay.shape_preset_folder) if f.endswith(".crshr")]
            if custom_shapes:
                self.shape_box.addItems(sorted(custom_shapes))
        except Exception as e:
            print(f"カスタム形状の読み込みに失敗: {e}")

        # 画像形状
        self.shape_box.addItems(["MAME", "カスタム画像"])
        
        # 作成
        self.shape_box.addItem("新しく作る")

        # 以前の選択を復元
        index = self.shape_box.findText(current_selection)
        if index != -1:
            self.shape_box.setCurrentIndex(index)

        self.shape_box.blockSignals(False)

    def update_hotkey_menu_text(self):
        current_hotkey = self.overlay.toggle_hotkey
        self.hotkey_action.setText(f"ショートカットキー設定... ({current_hotkey})")

    def make_color_button(self, label_text, getter, setter, update_callback):
        layout_ = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(label_text)
        color_button = QtWidgets.QPushButton()
        color_button.setFixedSize(90, 28)
        color_button.setToolTip("クリックして色を選択")
        def update_color(color_hex):
            color_button.setStyleSheet(f'''
                QPushButton {{
                    background-color: {color_hex};
                    border: 1px solid #4d4d4d;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border-color: #007acc;
                }}
            ''')
            color_button.setText(color_hex.upper())
            qcolor = QtGui.QColor(color_hex)
            if qcolor.lightness() > 127:
                color_button.setStyleSheet(color_button.styleSheet() + "QPushButton { color: #000000; font-weight: bold; }")
            else:
                color_button.setStyleSheet(color_button.styleSheet() + "QPushButton { color: #ffffff; font-weight: bold; }")
        color_button.update_color = update_color
        def pick_color():
            current_color = QtGui.QColor(getter())
            color = QtWidgets.QColorDialog.getColor(current_color, self, "色を選択")
            if color.isValid():
                color_name = color.name()
                setter(color_name)
                color_button.update_color(color_name)
                update_callback()
                self.schedule_overlay_update()
        color_button.clicked.connect(pick_color)
        color_button.update_color(getter()) # 初期色を設定
        layout_.addWidget(label)
        layout_.addStretch()
        layout_.addWidget(color_button)
        return layout_, color_button

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
        for file in os.listdir(self.overlay.overall_preset_folder):
            if file.endswith(config.PRESET_EXTENSION):
                name = os.path.splitext(file)[0]
                path = os.path.join(self.overlay.overall_preset_folder, file)
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
            self, "プリセットを保存", self.overlay.overall_preset_folder,
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
        dlg = SettingsDialog(self, self.overlay.overall_preset_folder, self.overlay.shape_preset_folder)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_overall_path, new_shape_path = dlg.get_selected_paths()
            
            if new_overall_path:
                self.overlay.overall_preset_folder = new_overall_path
                os.makedirs(self.overlay.overall_preset_folder, exist_ok=True)

            if new_shape_path:
                self.overlay.shape_preset_folder = new_shape_path
                os.makedirs(self.overlay.shape_preset_folder, exist_ok=True)

            self.overlay.save_global_config()
            self.load_presets()
            self.reload_shapes()

    def set_master_enabled(self, enabled, manual_toggle=False):
        if self.overlay.master_enabled == enabled and not manual_toggle:
            return
        self.overlay.master_enabled = enabled
        self.update_master_toggle_button_ui()
        self.overlay.update()

    def update_master_toggle_button_ui(self):
        if not hasattr(self, 'master_toggle_btn'):
            return
        hotkey_text = f"({self.overlay.toggle_hotkey})"
        if self.overlay.master_enabled:
            self.master_toggle_btn.setText(f"オーバーレイ無効化 {hotkey_text}")
            self.master_toggle_btn.setObjectName("masterToggleButton")
        else:
            self.master_toggle_btn.setText(f"オーバーレイ有効化 {hotkey_text}")
            self.master_toggle_btn.setObjectName("masterToggleButtonActive")
        if self.overlay.monitor_apex:
            self.master_toggle_btn.setToolTip("Apex監視が有効です。ゲームの起動/終了時に自動でON/OFFが切り替わります。")
        else:
            self.master_toggle_btn.setToolTip("クロスヘアとドットの表示をまとめてON/OFFします")
        self.master_toggle_btn.style().unpolish(self.master_toggle_btn)
        self.master_toggle_btn.style().polish(self.master_toggle_btn)

    def toggle_master_visibility(self):
        self.overlay.toggle_master_visibility()

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
            self.set_master_enabled(is_running)

    def toggle_apex_monitoring(self, checked):
        self.overlay.monitor_apex = checked
        self.overlay.save_global_config()
        self.master_toggle_btn.setEnabled(True)
        if checked:
            if not utils.psutil:
                QtWidgets.QMessageBox.warning(self, "ライブラリ不足", "この機能を利用するには 'psutil' が必要です。コマンドプロンプトで 'pip install psutil' を実行してください。 সন")
                if hasattr(self, 'apex_monitor_action'):
                    self.apex_monitor_action.setChecked(False)
                return
            is_game_running = any(p.name() in utils.GAME_PROCESS_NAMES for p in utils.psutil.process_iter(['name']))
            self.set_master_enabled(is_game_running)
            if self.overlay.game_monitor_thread is None:
                self.overlay.game_monitor_thread = utils.GameMonitorThread(utils.GAME_PROCESS_NAMES, self.overlay)
                self.overlay.game_monitor_thread.start()
                print("Apex Legendsの監視を開始しました。")
        else:
            if self.overlay.game_monitor_thread is not None:
                self.overlay.game_monitor_thread.stop()
                print("Apex Legendsの監視を停止しています...")
        self.update_master_toggle_button_ui()

    @QtCore.pyqtSlot()
    def on_monitor_thread_finished(self):
        print("Apex Legendsの監視を停止しました。 সন")
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
        shape = self.overlay.crosshair_shape
        self.shape_box.setCurrentText(shape)
        is_image_based = shape in ["MAME", "カスタム画像"]
        self.ch_color_widget.setVisible(not is_image_based)
        is_custom_image = self.overlay.crosshair_shape == "カスタム画像"
        self.custom_image_widget.setVisible(is_custom_image)
        if is_custom_image:
            path = self.overlay.crosshair_image_path
            if path and os.path.exists(path):
                self.custom_image_path_label.setText(os.path.basename(path))
            else:
                self.custom_image_path_label.setText("選択されていません")
        self.dot_slider.setValue(self.overlay.dot_radius * 2)
        self.dot_value_edit.setText(str(self.overlay.dot_radius * 2))
        self.ch_color_square.update_color(self.overlay.crosshair_color)
        self.dot_out_color_square.update_color(self.overlay.dot_outer_color)
        self.dot_in_color_square.update_color(self.overlay.dot_inner_color)
        self.alpha_slider.setValue(int(self.overlay.crosshair_alpha * 100))
        self.alpha_value_edit.setText(f"{self.overlay.crosshair_alpha:.2f}")
        self.dot_alpha_slider.setValue(int(self.overlay.dot_alpha * 100))
        self.dot_alpha_value_edit.setText(f"{self.overlay.dot_alpha:.2f}")
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
            restart_button = msg_box.addButton("今すぐ再起動", QtWidgets.QMessageBox.AcceptRole)
            msg_box.addButton("後で", QtWidgets.QMessageBox.RejectRole)
            msg_box.setStyleSheet("QLabel#qt_msgbox_label { min-width: 310px; }")
            msg_box.exec_()
            if msg_box.clickedButton() == restart_button:
                self.overlay.restart_application()

    def toggle_crosshair_button(self, checked): 
        self.overlay.crosshair_visible = checked
        self.schedule_overlay_update()

    @QtCore.pyqtSlot()
    def show_download_complete_message(self):
        QtWidgets.QMessageBox.information(self, "ダウンロード完了", "mame.png のダウンロードが完了しました。")
        self.schedule_overlay_update()

    @QtCore.pyqtSlot(str)
    def show_download_error_message(self, error_message):
        QtWidgets.QMessageBox.warning(self, "ダウンロード失敗", f"mame.png のダウンロードに失敗しました。\n{error_message}")

    def update_crosshair_shape(self, shape_text):
        if shape_text == "新しく作る":
            # 現在の形状を記憶しておく
            previous_shape = self.overlay.crosshair_shape
            
            editor = EditorDialog(self, shape_preset_folder=self.overlay.shape_preset_folder)
            if editor.exec_() == QtWidgets.QDialog.Accepted:
                self.reload_shapes()
                if editor.saved_path:
                    new_shape_name = os.path.splitext(os.path.basename(editor.saved_path))[0]
                    self.shape_box.setCurrentText(new_shape_name)
            else:
                # キャンセルされたら元の形状に戻す
                self.shape_box.setCurrentText(previous_shape)
            return

        self.overlay.crosshair_shape = shape_text
        is_image_based = shape_text in ["MAME", "カスタム画像"]
        self.ch_color_widget.setVisible(not is_image_based)
        self.custom_image_widget.setVisible(shape_text == "カスタム画像")
        if shape_text == "MAME":
            utils.download_mame_png_if_missing(self)
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

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(30, 30, 30))
        super().paintEvent(event)