import os
import time
from PyQt5 import QtCore, QtGui, QtWidgets

from . import utils
from .dialogs import SettingsDialog, KeyCaptureDialog
from .ui_components import tab_general, tab_crosshair, tab_dot, tab_keys, tab_apex_rank

# Import logic from the new sub-package
from .panel_logic import presets, updates, handlers, apex_tracker

class ControlPanel(QtWidgets.QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.setWindowTitle("Crosshair Control Panel")
        self.setWindowIcon(QtGui.QIcon("mame.png"))
        self.setGeometry(100, 100, 810, 900)
        self.apex_rank_history = []
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
        self._create_main_view(main_layout)
        self._create_tray_icon()
        self._setup_apex_tracker()

        self._assign_handlers()
        self._connect_signals()
        self._connect_overlay_signals()

        self.reload_shapes()
        self.update_control_panel_ui()
        self.load_presets()
        
        if self.overlay.monitor_apex and utils.psutil:
            self.toggle_apex_monitoring(True)

        self.update_master_toggle_button_ui()

        # Start hidden if both Apex monitoring and startup are enabled
        start_hidden = False
        if self.overlay.monitor_apex and utils.IS_WINDOWS and utils.is_in_startup(utils.APP_NAME):
            start_hidden = True

        if not start_hidden:
            self.setWindowOpacity(0.0)
            self.animate_panel_show()
            self._pulse_once(self.save_btn, QtGui.QColor("#0078d7"))

        # Install wheel event filter on all sliders to prevent scroll hijacking
        self.wheel_filter = utils.WheelEventFilter(self)
        sliders = self.findChildren(QtWidgets.QSlider)
        for slider in sliders:
            slider.installEventFilter(self.wheel_filter)

    def _create_tray_icon(self):
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon("mame.png"))

        tray_menu = QtWidgets.QMenu()
        show_action = tray_menu.addAction("表示")
        show_action.triggered.connect(self.show)
        
        quit_action = tray_menu.addAction("終了")
        quit_action.triggered.connect(self._quit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        self.tray_icon.show()

    def _on_tray_icon_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.show()
            self.activateWindow()

    def _quit_app(self):
        self.apex_tracker.stop_tracking()
        self.overlay.clean_up()
        QtWidgets.QApplication.instance().quit()

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
        self.save_btn = QtWidgets.QPushButton("プリセットを保存")
        self.save_btn.setProperty("accent", True)
        presets_layout.addWidget(self.preset_box, 1)
        presets_layout.addWidget(self.save_btn)
        parent_layout.addWidget(presets_group)

    def _create_main_view(self, parent_layout):
        main_view_layout = QtWidgets.QHBoxLayout()
        main_view_layout.setSpacing(0)
        main_view_layout.setContentsMargins(0, 10, 0, 0)

        # --- Navigation ---
        self.nav_list = QtWidgets.QListWidget()
        self.nav_list.setObjectName("navigationList")
        self.nav_list.setFixedWidth(120)
        main_view_layout.addWidget(self.nav_list)

        # --- Separator ---
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setObjectName("navigationSeparator")
        main_view_layout.addWidget(separator)

        # --- Pages ---
        self.pages_widget = QtWidgets.QStackedWidget()
        self.pages_widget.setObjectName("pagesWidget")
        main_view_layout.addWidget(self.pages_widget, 1)

        # --- Create and add pages with ScrollArea ---
        general_tab = tab_general.create_tab(self)
        ch_tab = tab_crosshair.create_tab(self)
        dot_tab = tab_dot.create_tab(self)
        keys_tab = tab_keys.create_tab(self)
        self.apex_tab = tab_apex_rank.create_tab(self, self.overlay)

        # Set initial values for Apex Rank tab from loaded config
        platform_index = self.apex_tab.platform_combo.findData(self.overlay.apex_platform)
        if platform_index != -1:
            self.apex_tab.platform_combo.setCurrentIndex(platform_index)
        self.apex_tab.username_edit.setText(self.overlay.apex_username)

        tabs_to_add = [general_tab, ch_tab, dot_tab, keys_tab, self.apex_tab]
        for tab_content in tabs_to_add:
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setWidget(tab_content)
            scroll_area.setWidgetResizable(True)
            scroll_area.setObjectName("pageScrollArea")
            scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.pages_widget.addWidget(scroll_area)

        # --- Add items to navigation ---
        self.nav_list.addItem(QtWidgets.QListWidgetItem(" 全般"))
        self.nav_list.addItem(QtWidgets.QListWidgetItem(" クロスヘア"))
        self.nav_list.addItem(QtWidgets.QListWidgetItem(" ドット"))
        self.nav_list.addItem(QtWidgets.QListWidgetItem(" キー無効化"))
        self.nav_list.addItem(QtWidgets.QListWidgetItem(" Apexランク"))
        
        # --- Connect navigation ---
        self.nav_list.currentRowChanged.connect(self.pages_widget.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        parent_layout.addLayout(main_view_layout)

    def _assign_handlers(self):
        # --- Event Handlers ---
        self._on_alpha_input_finished = handlers._on_alpha_input_finished(self)
        self._on_dot_size_input_finished = handlers._on_dot_size_input_finished(self)
        self._on_dot_alpha_input_finished = handlers._on_dot_alpha_input_finished(self)
        self._on_dot_offset_x_input_finished = handlers._on_dot_offset_x_input_finished(self)
        self._on_dot_offset_y_input_finished = handlers._on_dot_offset_y_input_finished(self)

        # --- New Handlers ---
        self._on_outline_width_input_finished = handlers._create_line_edit_handler(self, self.outline_width_edit, self.outline_width_slider, 'crosshair_outline_width')
        self._on_crosshair_outline_alpha_input_finished = handlers._create_line_edit_handler(self, self.crosshair_outline_alpha_edit, self.crosshair_outline_alpha_slider, 'crosshair_outline_alpha', is_float=True)
        self._on_vline_length_input_finished = handlers._create_line_edit_handler(self, self.vline_length_edit, self.vline_length_slider, 'crosshair_vline_length')
        self._on_hline_length_input_finished = handlers._create_line_edit_handler(self, self.hline_length_edit, self.hline_length_slider, 'crosshair_hline_length')
        self._on_line_thickness_input_finished = handlers._create_line_edit_handler(self, self.line_thickness_edit, self.line_thickness_slider, 'crosshair_thickness')
        self._on_crosshair_inner_alpha_input_finished = handlers._create_line_edit_handler(self, self.crosshair_inner_alpha_edit, self.crosshair_inner_alpha_slider, 'crosshair_inner_alpha', is_float=True)
        self._on_gap_input_finished = handlers._create_line_edit_handler(self, self.gap_edit, self.gap_slider, 'crosshair_gap')
        self._on_outer_vline_length_input_finished = handlers._create_line_edit_handler(self, self.outer_vline_length_edit, self.outer_vline_length_slider, 'outer_vline_length')
        self._on_outer_hline_length_input_finished = handlers._create_line_edit_handler(self, self.outer_hline_length_edit, self.outer_hline_length_slider, 'outer_hline_length')
        self._on_outer_line_alpha_input_finished = handlers._create_line_edit_handler(self, self.outer_line_alpha_edit, self.outer_line_alpha_slider, 'outer_line_alpha', is_float=True)
        self._on_outer_line_thickness_input_finished = handlers._create_line_edit_handler(self, self.outer_line_thickness_edit, self.outer_line_thickness_slider, 'outer_line_thickness')
        self._on_outer_gap_input_finished = handlers._create_line_edit_handler(self, self.outer_gap_edit, self.outer_gap_slider, 'outer_gap')
        self._on_circle_outline_width_input_finished = handlers._create_line_edit_handler(self, self.circle_outline_width_edit, self.circle_outline_width_slider, 'circle_outline_width')
        self._on_circle_outline_alpha_input_finished = handlers._create_line_edit_handler(self, self.circle_outline_alpha_edit, self.circle_outline_alpha_slider, 'circle_outline_alpha', is_float=True)
        self._on_circle_thickness_input_finished = handlers._create_line_edit_handler(self, self.circle_thickness_edit, self.circle_thickness_slider, 'circle_thickness')
        self._on_circle_diameter_input_finished = handlers._create_line_edit_handler(self, self.circle_diameter_edit, self.circle_diameter_slider, 'circle_diameter')
        self._on_chevron_outline_width_input_finished = handlers._create_line_edit_handler(self, self.chevron_outline_width_edit, self.chevron_outline_width_slider, 'chevron_outline_width')
        self._on_chevron_outline_alpha_input_finished = handlers._create_line_edit_handler(self, self.chevron_outline_alpha_edit, self.chevron_outline_alpha_slider, 'chevron_outline_alpha', is_float=True)
        self._on_chevron_thickness_input_finished = handlers._create_line_edit_handler(self, self.chevron_thickness_edit, self.chevron_thickness_slider, 'chevron_thickness')
        self._on_chevron_length_input_finished = handlers._create_line_edit_handler(self, self.chevron_length_edit, self.chevron_length_slider, 'chevron_length')
        self._on_image_crosshair_size_input_finished = handlers._create_line_edit_handler(self, self.image_crosshair_size_edit, self.image_crosshair_size_slider, 'image_crosshair_size')
        self._on_fade_multiplier_input_finished = handlers._create_line_edit_handler(self, self.fade_multiplier_edit, self.fade_multiplier_slider, 'fade_on_shoot_multiplier', is_float=True)

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
        self.dot_offset_x_edit.editingFinished.connect(self._on_dot_offset_x_input_finished)
        self.dot_offset_y_edit.editingFinished.connect(self._on_dot_offset_y_input_finished)

        # Connect new QLineEdit signals
        self.outline_width_edit.editingFinished.connect(self._on_outline_width_input_finished)
        self.crosshair_outline_alpha_edit.editingFinished.connect(self._on_crosshair_outline_alpha_input_finished)
        self.vline_length_edit.editingFinished.connect(self._on_vline_length_input_finished)
        self.hline_length_edit.editingFinished.connect(self._on_hline_length_input_finished)
        self.line_thickness_edit.editingFinished.connect(self._on_line_thickness_input_finished)
        self.crosshair_inner_alpha_edit.editingFinished.connect(self._on_crosshair_inner_alpha_input_finished)
        self.gap_edit.editingFinished.connect(self._on_gap_input_finished)
        self.outer_vline_length_edit.editingFinished.connect(self._on_outer_vline_length_input_finished)
        self.outer_hline_length_edit.editingFinished.connect(self._on_outer_hline_length_input_finished)
        self.outer_line_alpha_edit.editingFinished.connect(self._on_outer_line_alpha_input_finished)
        self.outer_line_thickness_edit.editingFinished.connect(self._on_outer_line_thickness_input_finished)
        self.outer_gap_edit.editingFinished.connect(self._on_outer_gap_input_finished)
        self.circle_outline_width_edit.editingFinished.connect(self._on_circle_outline_width_input_finished)
        self.circle_outline_alpha_edit.editingFinished.connect(self._on_circle_outline_alpha_input_finished)
        self.circle_thickness_edit.editingFinished.connect(self._on_circle_thickness_input_finished)
        self.circle_diameter_edit.editingFinished.connect(self._on_circle_diameter_input_finished)
        self.chevron_outline_width_edit.editingFinished.connect(self._on_chevron_outline_width_input_finished)
        self.chevron_outline_alpha_edit.editingFinished.connect(self._on_chevron_outline_alpha_input_finished)
        self.chevron_thickness_edit.editingFinished.connect(self._on_chevron_thickness_input_finished)
        self.chevron_length_edit.editingFinished.connect(self._on_chevron_length_input_finished)
        self.image_crosshair_size_edit.editingFinished.connect(self._on_image_crosshair_size_input_finished)
        self.fade_multiplier_slider.valueChanged.connect(self.update_fade_multiplier)
        self.fade_multiplier_edit.editingFinished.connect(self._on_fade_multiplier_input_finished)

        self._connect_apex_signals()

    def _connect_overlay_signals(self):
        self.overlay.panel_activation_requested.connect(self.activateWindow)


    # --- Apex Legends Rank Tracker Methods ---
    def _setup_apex_tracker(self):
        self.apex_tracker = apex_tracker.ApexTracker(self)
        self.apex_tracker.data_updated.connect(self._on_apex_data_updated)
        self.apex_tracker.error_occurred.connect(self._on_apex_tracker_error)
        self.apex_tracker.tracking_status_changed.connect(self._on_apex_tracker_status_changed)

    def _connect_apex_signals(self):
        self.apex_tab.track_button.toggled.connect(self._on_apex_track_button_toggled)
        self.apex_tab.username_edit.editingFinished.connect(self._update_apex_credentials)
        self.apex_tab.platform_combo.currentIndexChanged.connect(self._update_apex_credentials)

    def _on_apex_track_button_toggled(self, checked):
        if checked:
            self._update_apex_credentials()
            self.apex_tracker.start_tracking()
            self.apex_rank_history = [] # Reset history on new tracking session
            self._update_apex_graph()
        else:
            self.apex_tracker.stop_tracking()

    def _update_apex_credentials(self):
        platform = self.apex_tab.platform_combo.currentData()
        username = self.apex_tab.username_edit.text()
        self.apex_tracker.set_credentials(platform, username)
        # Save the updated credentials to overlay and then to config
        self.overlay.apex_platform = platform
        self.overlay.apex_username = username
        self.overlay.save_global_config() # Save immediately

    @QtCore.pyqtSlot(dict)
    def _on_apex_data_updated(self, data):
        # Extract data
        current_score = data["current_score"]
        last_score = data["last_score"]
        rank_name = data["rank_name"]
        rank_div = data["rank_div"]
        al_stop_int = data.get("al_stop_int") # Get ALStopInt

        # Format rank string
        if rank_name in ["Master", "Predator"]:
            rank_str = rank_name
        else:
            rank_str = f"{rank_name} {rank_div}"
        
        self.apex_tab.current_rank_label.setText(rank_str)
        self.apex_tab.current_score_label.setText(f"{current_score:,} RP")
        if al_stop_int is not None:
            self.apex_tab.current_position_label.setText(f"{al_stop_int:,}") # Update position label
        else:
            self.apex_tab.current_position_label.setText("N/A")

        # Update score change
        if last_score is not None:
            change = current_score - last_score
            if change > 0:
                self.apex_tab.score_change_label.setText(f"+{change}")
                self.apex_tab.score_change_label.setStyleSheet("color: #4CAF50;") # Green
            elif change < 0:
                self.apex_tab.score_change_label.setText(f"{change}")
                self.apex_tab.score_change_label.setStyleSheet("color: #F44336;") # Red
            else:
                self.apex_tab.score_change_label.setText("+0")
                self.apex_tab.score_change_label.setStyleSheet("color: white;")
        else:
            # First data point
            self.apex_tab.score_change_label.setText("+0")
            self.apex_tab.score_change_label.setStyleSheet("color: white;")

        # Add to history and update graph
        self.apex_rank_history.append((time.time(), current_score))
        self._update_apex_graph()

    def _update_apex_graph(self):
        from matplotlib.ticker import MaxNLocator
        canvas = self.apex_tab.graph_canvas
        ax = canvas.axes
        ax.clear()
        canvas.apply_style()  # Re-apply the custom style

        DEFAULT_VISIBLE_RANGE = 300 # A good range to show typical +/-75 RP fluctuations

        # Set labels and title (do this once)
        ax.set_xlabel("試合数", fontsize=12, color='#e0e0e0')
        ax.set_ylabel("ランクスコア (RP)", fontsize=12, color='#e0e0e0')
        ax.set_title("ランクスコア推移", fontsize=16, color='#ffffff', pad=20)

        if self.apex_rank_history and len(self.apex_rank_history) > 1:
            timestamps, scores = zip(*self.apex_rank_history)
            match_numbers = range(1, len(scores) + 1)

            # Stylish plot
            line_color = '#00BFFF'  # Vibrant blue
            fill_color = '#00BFFF'
            ax.plot(match_numbers, scores, marker='o', linestyle='-', color=line_color, linewidth=2.5, markersize=7, markeredgecolor='#282c34', markeredgewidth=1.5)
            ax.fill_between(match_numbers, scores, color=fill_color, alpha=0.15, interpolate=True)

            # Add data point labels with subtle background
            for i, score in enumerate(scores):
                ax.text(match_numbers[i], score + (max(scores)*0.02), str(score), ha='center', va='bottom', color='#ffffff', fontsize=10, weight='bold', 
                        bbox=dict(facecolor='#282c34', edgecolor='none', boxstyle='round,pad=0.3', alpha=0.7))

            # Ensure x-axis ticks are integers and set limits
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax.margins(x=0.02)  # Small horizontal padding

            # Improved Y-axis scaling with more padding
            min_score, max_score = min(scores), max(scores)
            score_range = max_score - min_score
            DEFAULT_VISIBLE_RANGE = 300 # A good range to show typical +/-75 RP fluctuations

            if score_range < DEFAULT_VISIBLE_RANGE:
                mid_point = (min_score + max_score) / 2
                ax.set_ylim(mid_point - (DEFAULT_VISIBLE_RANGE / 2), mid_point + (DEFAULT_VISIBLE_RANGE / 2))
            else:
                # Add more padding if the range is large
                padding = score_range * 0.15 # Increased padding
                ax.set_ylim(min_score - padding, max_score + padding)

            # Set x-axis ticks to show all match numbers if few, or a reasonable subset
            if len(match_numbers) <= 10:
                ax.set_xticks(match_numbers)
            else:
                ax.set_xticks(MaxNLocator(nbins=5).tick_values(1, len(match_numbers)))

        elif self.apex_rank_history:  # Exactly one data point
            score = self.apex_rank_history[0][1]
            ax.plot([1], [score], marker='o', linestyle='-', color='#00BFFF', markersize=7, markeredgecolor='#282c34', markeredgewidth=1.5)
            ax.text(1, score + (score*0.02), str(score), ha='center', va='bottom', color='#ffffff', fontsize=10, weight='bold',
                    bbox=dict(facecolor='#282c34', edgecolor='none', boxstyle='round,pad=0.3', alpha=0.7))
            ax.set_xlim(0.5, 1.5)
            ax.set_ylim(score - (DEFAULT_VISIBLE_RANGE / 2), score + (DEFAULT_VISIBLE_RANGE / 2)) # Use default visible range for single point
            ax.set_xticks([1]) # Ensure only '1' is shown for single point

        else:  # No data
            ax.text(0.5, 0.5, "トラッキングを開始してデータを表示", ha='center', va='center', transform=ax.transAxes, color='#b0b0b0', fontsize=14) # Slightly larger and lighter gray
            # Hide ticks and labels for empty state
            ax.set_xticks([])
            ax.set_yticks([])

        canvas.figure.tight_layout(pad=3.5) # Increased padding for overall layout
        canvas.draw()

    @QtCore.pyqtSlot(str)
    def _on_apex_tracker_error(self, message):
        QtWidgets.QMessageBox.warning(self, "トラッカーエラー", message)
        if self.apex_tab.track_button.isChecked():
            self.apex_tab.track_button.setChecked(False)

    @QtCore.pyqtSlot(bool)
    def _on_apex_tracker_status_changed(self, is_tracking):
        print(f"[DEBUG] ControlPanel: _on_apex_tracker_status_changed received signal with is_tracking={is_tracking}")
        # Ensure the button's checked state matches the actual tracking status
        if self.apex_tab.track_button.isChecked() != is_tracking:
            self.apex_tab.track_button.setChecked(is_tracking)
        
        # Update button text based on tracking status
        if is_tracking:
            self.apex_tab.track_button.setText("トラッキング停止")
            self.apex_tab.platform_combo.setEnabled(False)
            self.apex_tab.username_edit.setEnabled(False)
        else:
            self.apex_tab.track_button.setText("トラッキング開始")
            self.apex_tab.platform_combo.setEnabled(True)
            self.apex_tab.username_edit.setEnabled(True)

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
    update_fade_multiplier_ui = updates.update_fade_multiplier_ui

    # --- ここから外枠 ---
    update_outer_line_enabled = updates.update_outer_line_enabled
    update_outer_vline_length = updates.update_outer_vline_length
    update_outer_hline_length = updates.update_outer_hline_length
    update_outer_line_alpha = updates.update_outer_line_alpha
    update_outer_line_thickness = updates.update_outer_line_thickness
    update_outer_gap = updates.update_outer_gap

    # --- ここからドットオフセット ---
    update_dot_offset_x = updates.update_dot_offset_x
    update_dot_offset_y = updates.update_dot_offset_y

    # --- Event Handlers ---
    update_crosshair_shape = handlers.update_crosshair_shape
    select_custom_image = handlers.select_custom_image
    toggle_crosshair_button = handlers.toggle_crosshair_button
    toggle_dot_button = handlers.toggle_dot_button
    update_dot_size = handlers.update_dot_size
    update_alpha = handlers.update_alpha
    update_dot_alpha = handlers.update_dot_alpha
    update_dot_shape = handlers.update_dot_shape
    toggle_fade_on_shoot = handlers.toggle_fade_on_shoot
    update_fade_multiplier = handlers.update_fade_multiplier
    set_crosshair_color = handlers.set_crosshair_color
    set_dot_outer_color = handlers.set_dot_outer_color
    set_dot_inner_color = handlers.set_dot_inner_color
    schedule_overlay_update = handlers.schedule_overlay_update
    _perform_deferred_update = handlers._perform_deferred_update
    monitor_changed = handlers.monitor_changed
    disable_key_gui = handlers.disable_key_gui
    enable_key_gui = handlers.enable_key_gui
    enable_all_keys_gui = handlers.enable_all_keys_gui

    update_chevron_outline_enabled = handlers.update_chevron_outline_enabled
    update_chevron_outline_width = handlers.update_chevron_outline_width
    update_chevron_thickness = handlers.update_chevron_thickness
    update_chevron_length = handlers.update_chevron_length

    update_image_crosshair_size = handlers.update_image_crosshair_size

    update_crosshair_outline_alpha = handlers.update_crosshair_outline_alpha
    update_crosshair_inner_alpha = handlers.update_crosshair_inner_alpha
    update_circle_outline_alpha = handlers.update_circle_outline_alpha
    update_chevron_outline_alpha = handlers.update_chevron_outline_alpha
    toggle_antialiasing = handlers.toggle_antialiasing

    import_valorant_crosshair = handlers.import_valorant_crosshair

    # --- Remaining Logic Specific to ControlPanel ---
    def closeEvent(self, event):
        if self.overlay.is_dirty:
            reply = QtWidgets.QMessageBox.question(
                self, "保存されていません",
                "現在の設定はプリセットとして保存されていません。終了する前に保存しますか？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel
            )
            if reply == QtWidgets.QMessageBox.Yes:
                if not self.save_preset():
                    event.ignore()
                    return
            elif reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                return
        
        self.hide()
        event.ignore()

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

    def make_color_button(self, label_text, getter, setter, update_callback, parent=None):
        container = QtWidgets.QWidget(parent)
        layout_ = QtWidgets.QHBoxLayout(container)
        layout_.setContentsMargins(0, 0, 0, 0)

        label = QtWidgets.QLabel(label_text, container)
        color_button = QtWidgets.QPushButton(container)
        color_button.setFixedSize(90, 28)
        color_button.setToolTip("クリックして色を選択")
        
        def update_color(color_hex):
            color_button.setStyleSheet(f'''
                QPushButton {{ background-color: {color_hex}; border: 1px solid #4d4d4d; border-radius: 4px; }}
                QPushButton:hover {{ border-color: #007acc; }}
            ''')
            color_button.setText(color_hex.upper())
            qcolor = QtGui.QColor(color_hex)
            color_button.setStyleSheet(color_button.styleSheet() + f"QPushButton {{ color: {{'#000000' if qcolor.lightness() > 127 else '#ffffff'}}; font-weight: bold; }}")
        
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
        
        return container, color_button

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
            if is_running:
                self.show()
                self.activateWindow()
                # New: Automatically start tracking if auto_track_apex is enabled
                if self.overlay.auto_track_apex:
                    # Ensure credentials are set before attempting to start tracking
                    self.apex_tracker.set_credentials(self.overlay.apex_platform, self.overlay.apex_username)
                    
                    # Only set if not already checked to ensure toggled signal is emitted
                    if not self.apex_tab.track_button.isChecked():
                        self.apex_tab.track_button.setChecked(True)
            else:
                # If auto-tracking is enabled and Apex is not running, stop tracking
                if self.overlay.auto_track_apex:
                    self.apex_tracker.stop_tracking()
                    # Ensure the track button is unchecked if tracking was auto-started and Apex exited
                    if self.apex_tab.track_button.isChecked():
                        self.apex_tab.track_button.setChecked(False)
        else:
            pass

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
                # Connect the signal here
                self.overlay.game_monitor_thread.apex_status_changed.connect(self.on_game_state_changed)
                self.overlay.game_monitor_thread.start()
        else:
            if self.overlay.game_monitor_thread is not None:
                self.overlay.game_monitor_thread.stop()
        self.update_master_toggle_button_ui()

    

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