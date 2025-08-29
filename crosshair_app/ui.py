
import os
import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
import keyboard

from . import utils
from . import config
from .dialogs import SettingsDialog, KeyCaptureDialog
from .ui_components import tab_general, tab_crosshair, tab_dot, tab_keys

# Import logic from the new sub-package
from .panel_logic import presets, updates, handlers

class ControlPanel(QtWidgets.QWidget):
    def __init__(self, overlay):
        super().__init__()
        self._initial_load_complete = False
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

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self._create_menu_bar(main_layout)
        self._create_master_toggle(main_layout)
        self._create_presets_group(main_layout)
        self._create_tab_widget(main_layout)

        self._connect_signals()

        self.reload_shapes()
        self.update_control_panel_ui()
        self.load_presets()
        
        if self.overlay.monitor_apex and utils.psutil:
            self.toggle_apex_monitoring(True)

        self.update_master_toggle_button_ui()
        self.setWindowOpacity(0.0)
        self.animate_panel_show()
        self._pulse_once(self.save_btn, QtGui.QColor("#0078d7"))

    # --- UI Creation ---
    def _create_menu_bar(self, parent_layout):
        menu_bar = QtWidgets.QMenuBar()
        settings_menu = menu_bar.addMenu("設定")
        settings_menu.addAction("保存先フォルダ...", self.open_settings)
        self.hotkey_action = settings_menu.addAction("ショートカットキー設定...")
        self.update_hotkey_menu_text()

        settings_menu.addSeparator()
        self.startup_action = settings_menu.addAction("PC起動時に自動実行する")
        self.startup_action.setCheckable(True)
        if utils.IS_WINDOWS:
            self.startup_action.setChecked(utils.is_in_startup(utils.APP_NAME))
        else:
            self.startup_action.setEnabled(False)
        parent_layout.setMenuBar(menu_bar)

    def _create_master_toggle(self, parent_layout):
        self.master_toggle_btn = QtWidgets.QPushButton("オーバーレイ無効化")
        self.master_toggle_btn.setObjectName("masterToggleButton")
        self.master_toggle_btn.setToolTip("クロスヘアとドットの表示をまとめてON/OFFします")
        parent_layout.addWidget(self.master_toggle_btn)

    def _create_presets_group(self, parent_layout):
        presets_group = QtWidgets.QGroupBox("プリセット")
        presets_layout = QtWidgets.QHBoxLayout(presets_group)
        self.preset_box = QtWidgets.QComboBox()
        self.save_btn = QtWidgets.QPushButton("保存")
        self.save_btn.setProperty("accent", True)
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

    def _connect_signals(self):
        self.master_toggle_btn.clicked.connect(self.toggle_master_visibility)
        self.preset_box.currentIndexChanged.connect(self.load_selected_preset)
        self.save_btn.clicked.connect(self.save_preset)
        self.hotkey_action.triggered.connect(self.open_hotkey_settings)
        if utils.IS_WINDOWS:
            self.startup_action.triggered.connect(self.toggle_startup)

        self.alpha_value_edit.editingFinished.connect(self._on_alpha_input_finished)
        self.dot_value_edit.editingFinished.connect(self._on_dot_size_input_finished)
        self.dot_alpha_value_edit.editingFinished.connect(self._on_dot_alpha_input_finished)

    # --- Method Assignments from Imported Logic ---
    # Presets
    load_presets = presets.load_presets
    save_preset = presets.save_preset
    load_selected_preset = presets.load_selected_preset

    # UI Updates
    update_control_panel_ui = updates.update_control_panel_ui
    update_outline_enabled = updates.update_outline_enabled
    update_outline_width = updates.update_outline_width
    update_vline_length = updates.update_vline_length
    update_hline_length = updates.update_hline_length
    update_line_thickness = updates.update_line_thickness
    update_gap = updates.update_gap
    update_circle_outline_enabled = updates.update_circle_outline_enabled
    update_circle_outline_width = updates.update_circle_outline_width
    update_circle_thickness = updates.update_circle_thickness
    update_circle_diameter = updates.update_circle_diameter
    update_drawing_order = updates.update_drawing_order

    # --- Event Handlers ---
        # Event Handlers
    _on_alpha_input_finished = handlers._on_alpha_input_finished
    _on_dot_size_input_finished = handlers._on_dot_size_input_finished
    _on_dot_alpha_input_finished = handlers._on_dot_alpha_input_finished
    update_crosshair_shape = handlers.update_crosshair_shape
    select_custom_image = handlers.select_custom_image
    toggle_crosshair_button = handlers.toggle_crosshair_button
    toggle_dot_button = handlers.toggle_dot_button
    update_dot_size = handlers.update_dot_size
    update_alpha = handlers.update_alpha
    update_dot_alpha = handlers.update_dot_alpha
    toggle_fade_on_shoot = handlers.toggle_fade_on_shoot
    set_crosshair_color = handlers.set_crosshair_color
    set_dot_outer_color = handlers.set_dot_outer_color
    set_dot_inner_color = handlers.set_dot_inner_color
    schedule_overlay_update = handlers.schedule_overlay_update
    _perform_deferred_update = handlers._perform_deferred_update
    monitor_changed = handlers.monitor_changed
    disable_key_gui = handlers.disable_key_gui
    enable_key_gui = handlers.enable_key_gui
    enable_all_keys_gui = handlers.enable_all_keys_gui

    # --- Remaining Logic Specific to ControlPanel ---
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
        if not hasattr(self, 'shape_box'): return
        current_selection = self.shape_box.currentText()
        self.shape_box.blockSignals(True)
        self.shape_box.clear()
        shapes = ["十字", "円", "矢印 (シェブロン)"]
        self.shape_box.addItems(shapes)
        self.custom_crshr_shapes = []
        try:
            for f in os.listdir(self.overlay.shape_preset_folder):
                if f.endswith(".crshr"):
                    self.custom_crshr_shapes.append(os.path.splitext(f)[0])
            if self.custom_crshr_shapes:
                self.shape_box.addItems(sorted(self.custom_crshr_shapes))
        except Exception as e:
            print(f"カスタム形状の読み込みに失敗: {e}")
        self.shape_box.addItems(["MAME", "カスタム画像", "新しく作る"])
        index = self.shape_box.findText(current_selection)
        if index != -1: self.shape_box.setCurrentIndex(index)
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
                QPushButton {{ background-color: {color_hex}; border: 1px solid #4d4d4d; border-radius: 4px; }}
                QPushButton:hover {{ border-color: #007acc; }}
            ''')
            color_button.setText(color_hex.upper())
            qcolor = QtGui.QColor(color_hex)
            color_button.setStyleSheet(color_button.styleSheet() + f"QPushButton {{ color: {'#000000' if qcolor.lightness() > 127 else '#ffffff'}; font-weight: bold; }}")
        color_button.update_color = update_color
        def pick_color():
            color = QtWidgets.QColorDialog.getColor(QtGui.QColor(getter()), self, "色を選択")
            if color.isValid():
                setter(color.name())
                color_button.update_color(color.name())
                update_callback()
                self.schedule_overlay_update()
        color_button.clicked.connect(pick_color)
        color_button.update_color(getter())
        layout_.addWidget(label)
        layout_.addStretch()
        layout_.addWidget(color_button)
        return layout_, color_button

    def set_master_enabled(self, enabled, manual_toggle=False):
        self.overlay.set_master_enabled(enabled, manual_toggle)

    def update_master_toggle_button_ui(self):
        if not hasattr(self, 'master_toggle_btn'): return
        hotkey_text = f"({self.overlay.toggle_hotkey})"
        if self.overlay.master_enabled:
            self.master_toggle_btn.setText(f"オーバーレイ無効化 {hotkey_text}")
            self.master_toggle_btn.setObjectName("masterToggleButton")
        else:
            self.master_toggle_btn.setText(f"オーバーレイ有効化 {hotkey_text}")
            self.master_toggle_btn.setObjectName("masterToggleButtonActive")
        self.master_toggle_btn.setToolTip("Apex監視が有効です。" if self.overlay.monitor_apex else "クロスヘアとドットの表示をまとめてON/OFFします")
        self.master_toggle_btn.style().unpolish(self.master_toggle_btn)
        self.master_toggle_btn.style().polish(self.master_toggle_btn)

    def toggle_master_visibility(self):
        self.overlay.toggle_master_visibility()

    def toggle_startup(self, checked):
        path = utils.get_executable_path()
        if checked:
            if not utils.add_to_startup(utils.APP_NAME, path):
                QtWidgets.QMessageBox.warning(self, "設定失敗", "スタートアップへの登録に失敗しました。\n管理者として実行すると解決する場合があります。")
                self.startup_action.setChecked(False)
        else:
            if not utils.remove_from_startup(utils.APP_NAME):
                QtWidgets.QMessageBox.warning(self, "設定失敗", "スタートアップからの登録解除に失敗しました。")
                self.startup_action.setChecked(True)

    @QtCore.pyqtSlot(bool)
    def on_game_state_changed(self, is_running):
        if self.overlay.monitor_apex:
            self.set_master_enabled(is_running)

    def toggle_apex_monitoring(self, checked):
        self.overlay.monitor_apex = checked
        self.overlay.save_global_config()
        self.master_toggle_btn.setEnabled(True)
        if checked:
            if not utils.psutil:
                QtWidgets.QMessageBox.warning(self, "ライブラリ不足", "この機能を利用するには 'psutil' が必要です。'pip install psutil' を実行してください。")
                if hasattr(self, 'apex_monitor_action'): self.apex_monitor_action.setChecked(False)
                return
            is_game_running = any(p.name() in utils.GAME_PROCESS_NAMES for p in utils.psutil.process_iter(['name']))
            self.set_master_enabled(is_game_running)
            if self.overlay.game_monitor_thread is None:
                self.overlay.game_monitor_thread = utils.GameMonitorThread(utils.GAME_PROCESS_NAMES, self.overlay)
                self.overlay.game_monitor_thread.start()
        else:
            if self.overlay.game_monitor_thread is not None:
                self.overlay.game_monitor_thread.stop()
        self.update_master_toggle_button_ui()

    @QtCore.pyqtSlot()
    def on_monitor_thread_finished(self):
        self.overlay.game_monitor_thread = None

    def animate_panel_show(self):
        fade = QtCore.QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(300)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        slide = QtCore.QPropertyAnimation(self, b"geometry")
        slide.setDuration(350)
        slide.setStartValue(QtCore.QRect(self.x(), self.y() - 20, self.width(), self.height()))
        slide.setEndValue(self.geometry())
        group = QtCore.QParallelAnimationGroup(self)
        group.addAnimation(fade)
        group.addAnimation(slide)
        group.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        self._panel_animations.append(group)

    def _pulse_once(self, widget, color):
        effect = QtWidgets.QGraphicsDropShadowEffect(widget)
        effect.setColor(color)
        effect.setOffset(0, 0)
        effect.setBlurRadius(0)
        widget.setGraphicsEffect(effect)
        anim = QtCore.QPropertyAnimation(effect, b"blurRadius")
        anim.setDuration(1000)
        anim.setStartValue(0)
        anim.setKeyValueAt(0.5, 24)
        anim.setEndValue(0)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        self._panel_animations.append(anim)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(30, 30, 30))
        super().paintEvent(event)
