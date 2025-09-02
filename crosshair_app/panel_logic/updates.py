def update_control_panel_ui(self):
    # --- Block Signals ---
    self.monitor_selection_box.blockSignals(True)
    self.shape_box.blockSignals(True)
    self.dot_slider.blockSignals(True)
    self.alpha_slider.blockSignals(True)
    self.dot_alpha_slider.blockSignals(True)
    self.fade_on_shoot_checkbox.blockSignals(True)
    self.crosshair_btn.blockSignals(True)
    self.dot_btn.blockSignals(True)
    self.outline_btn.blockSignals(True)
    self.outline_width_slider.blockSignals(True)
    self.vline_length_slider.blockSignals(True)
    self.hline_length_slider.blockSignals(True)
    self.line_thickness_slider.blockSignals(True)
    self.gap_slider.blockSignals(True)
    self.circle_outline_btn.blockSignals(True)
    self.circle_outline_width_slider.blockSignals(True)
    self.circle_thickness_slider.blockSignals(True)
    self.circle_diameter_slider.blockSignals(True)
    self.chevron_outline_btn.blockSignals(True)
    self.chevron_outline_width_slider.blockSignals(True)
    self.chevron_thickness_slider.blockSignals(True)
    self.chevron_length_slider.blockSignals(True)
    self.image_crosshair_size_slider.blockSignals(True)
    self.crosshair_outline_alpha_slider.blockSignals(True)
    self.circle_outline_alpha_slider.blockSignals(True)
    self.chevron_outline_alpha_slider.blockSignals(True)
    self.dot_shape_box.blockSignals(True)
    if hasattr(self, 'outer_line_btn'):
        self.outer_line_btn.blockSignals(True)
        self.outer_vline_length_slider.blockSignals(True)
        self.outer_hline_length_slider.blockSignals(True)
        self.outer_line_alpha_slider.blockSignals(True)
        self.outer_line_thickness_slider.blockSignals(True)
        self.outer_gap_slider.blockSignals(True)
    if hasattr(self, 'dot_offset_x_slider'):
        self.dot_offset_x_slider.blockSignals(True)
        self.dot_offset_y_slider.blockSignals(True)
        self.dot_offset_x_edit.blockSignals(True)
        self.dot_offset_y_edit.blockSignals(True)

    # --- Update General and Non-Shape-Specific UI ---
    self.monitor_selection_box.setCurrentIndex(self.overlay.selected_monitor_index)
    self.crosshair_btn.setChecked(self.overlay.crosshair_visible)
    self.dot_btn.setChecked(self.overlay.dot_visible)
    self.dot_shape_box.setCurrentText(self.overlay.dot_shape)
    shape = self.overlay.crosshair_shape
    self.shape_box.setCurrentText(shape)

    if self.overlay.drawing_order == "dot_on_top":
        self.drawing_order_box.setCurrentIndex(0)
    else:
        self.drawing_order_box.setCurrentIndex(1)

    # --- Update Shape-Specific UI ---
    is_cross_shape = shape == "十字"
    is_circle_shape = shape == "円"
    is_chevron_shape = shape == "矢印 (シェブロン)"
    is_image_based = shape in ["MAME", "カスタム画像"]
    is_crshr_shape = hasattr(self, 'custom_crshr_shapes') and shape in self.custom_crshr_shapes
    is_image_crosshair_shape = is_image_based or is_crshr_shape
    is_advanced_shape = is_cross_shape or is_circle_shape or is_chevron_shape or is_image_crosshair_shape

    # Visibility of advanced settings sections
    self.cross_settings_widget.setVisible(is_cross_shape)
    self.circle_settings_widget.setVisible(is_circle_shape)
    self.chevron_settings_widget.setVisible(is_chevron_shape)
    self.image_settings_widget.setVisible(is_image_crosshair_shape)

    # Visibility of the main advanced settings toggle button
    if hasattr(self, 'advanced_settings_toggle_btn'):
        self.advanced_settings_toggle_btn.setVisible(is_advanced_shape)
        self.shape_box.setProperty("previous_shape", shape)

    # Visibility of other shape-related UI
    is_non_color_customizable = is_image_based or is_crshr_shape
    self.ch_color_widget.setVisible(not is_non_color_customizable)
    self.custom_image_widget.setVisible(shape == "カスタム画像")

    # --- Populate Values ---
    if shape == "カスタム画像":
        path = self.overlay.crosshair_image_path
        self.custom_image_path_label.setText(os.path.basename(path) if path and os.path.exists(path) else "選択されていません")

    # Dot settings
    self.dot_slider.setValue(self.overlay.dot_radius * 2)
    self.dot_value_edit.setText(str(self.overlay.dot_radius * 2))
    self.dot_out_color_square.update_color(self.overlay.dot_outer_color)
    self.dot_in_color_square.update_color(self.overlay.dot_inner_color)
    self.dot_alpha_slider.setValue(int(self.overlay.dot_alpha * 100))
    self.dot_alpha_value_edit.setText(f"{self.overlay.dot_alpha:.3f}")
    if hasattr(self, 'dot_offset_x_slider'):
        self.dot_offset_x_slider.setValue(self.overlay.dot_offset_x)
        self.dot_offset_y_slider.setValue(self.overlay.dot_offset_y)
        self.dot_offset_x_edit.setText(str(self.overlay.dot_offset_x))
        self.dot_offset_y_edit.setText(str(self.overlay.dot_offset_y))

    # Crosshair common settings
    self.ch_color_square.update_color(self.overlay.crosshair_color)
    self.alpha_slider.setValue(int(self.overlay.crosshair_alpha * 100))
    self.alpha_value_edit.setText(f"{self.overlay.crosshair_alpha:.3f}")
    self.fade_on_shoot_checkbox.setChecked(self.overlay.fade_on_shoot_enabled)

    # Cross advanced settings
    if is_cross_shape:
        self.outline_btn.setChecked(self.overlay.crosshair_outline_enabled)
        self.outline_width_slider.setValue(self.overlay.crosshair_outline_width)
        self.vline_length_slider.setValue(self.overlay.crosshair_vline_length)
        self.hline_length_slider.setValue(self.overlay.crosshair_hline_length)
        self.line_thickness_slider.setValue(self.overlay.crosshair_thickness)
        self.gap_slider.setValue(self.overlay.crosshair_gap)
        self.outline_width_edit.setText(str(self.overlay.crosshair_outline_width))
        self.vline_length_edit.setText(str(self.overlay.crosshair_vline_length))
        self.hline_length_edit.setText(str(self.overlay.crosshair_hline_length))
        self.line_thickness_edit.setText(str(self.overlay.crosshair_thickness))
        self.gap_edit.setText(str(self.overlay.crosshair_gap))
        self.crosshair_outline_alpha_slider.setValue(int(self.overlay.crosshair_outline_alpha * 100))
        self.crosshair_outline_alpha_edit.setText(f"{self.overlay.crosshair_outline_alpha:.3f}")
        self.crosshair_inner_alpha_slider.setValue(int(self.overlay.crosshair_inner_alpha * 100))
        self.crosshair_inner_alpha_edit.setText(f"{self.overlay.crosshair_inner_alpha:.3f}")
        # --- Outer Crosshair ---
        self.outer_line_btn.setChecked(self.overlay.outer_line_enabled)
        self.outer_vline_length_slider.setValue(self.overlay.outer_vline_length)
        self.outer_hline_length_slider.setValue(self.overlay.outer_hline_length)
        self.outer_line_alpha_slider.setValue(int(self.overlay.outer_line_alpha * 100))
        self.outer_line_thickness_slider.setValue(self.overlay.outer_line_thickness)
        self.outer_gap_slider.setValue(self.overlay.outer_gap)
        self.outer_vline_length_edit.setText(str(self.overlay.outer_vline_length))
        self.outer_hline_length_edit.setText(str(self.overlay.outer_hline_length))
        self.outer_line_alpha_edit.setText(f"{self.overlay.outer_line_alpha:.3f}")
        self.outer_line_thickness_edit.setText(str(self.overlay.outer_line_thickness))
        self.outer_gap_edit.setText(str(self.overlay.outer_gap))

    # Circle advanced settings
    if is_circle_shape:
        self.circle_outline_btn.setChecked(self.overlay.circle_outline_enabled)
        self.circle_outline_width_slider.setValue(self.overlay.circle_outline_width)
        self.circle_thickness_slider.setValue(self.overlay.circle_thickness)
        self.circle_diameter_slider.setValue(self.overlay.circle_diameter)
        self.circle_outline_width_edit.setText(str(self.overlay.circle_outline_width))
        self.circle_thickness_edit.setText(str(self.overlay.circle_thickness))
        self.circle_diameter_edit.setText(str(self.overlay.circle_diameter))
        self.circle_outline_alpha_slider.setValue(int(self.overlay.circle_outline_alpha * 100))
        self.circle_outline_alpha_edit.setText(f"{self.overlay.circle_outline_alpha:.3f}")

    # Chevron advanced settings
    if is_chevron_shape:
        self.chevron_outline_btn.setChecked(self.overlay.chevron_outline_enabled)
        self.chevron_outline_width_slider.setValue(self.overlay.chevron_outline_width)
        self.chevron_thickness_slider.setValue(self.overlay.chevron_thickness)
        self.chevron_length_slider.setValue(self.overlay.chevron_length)
        self.chevron_outline_width_edit.setText(str(self.overlay.chevron_outline_width))
        self.chevron_thickness_edit.setText(str(self.overlay.chevron_thickness))
        self.chevron_length_edit.setText(str(self.overlay.chevron_length))
        self.chevron_outline_alpha_slider.setValue(int(self.overlay.chevron_outline_alpha * 100))
        self.chevron_outline_alpha_edit.setText(f"{self.overlay.chevron_outline_alpha:.3f}")

    # Image crosshair settings
    if is_image_crosshair_shape:
        self.image_crosshair_size_slider.setValue(self.overlay.image_crosshair_size)
        self.image_crosshair_size_edit.setText(str(self.overlay.image_crosshair_size))

    # Keys settings
    self.disabled_keys_label.setText(", ".join(self.overlay.disabled_keys) if self.overlay.disabled_keys else "なし")

    # --- Unblock Signals ---
    self.monitor_selection_box.blockSignals(False)
    self.shape_box.blockSignals(False)
    self.dot_slider.blockSignals(False)
    self.alpha_slider.blockSignals(False)
    self.dot_alpha_slider.blockSignals(False)
    self.fade_on_shoot_checkbox.blockSignals(False)
    self.crosshair_btn.blockSignals(False)
    self.dot_btn.blockSignals(False)
    self.outline_btn.blockSignals(False)
    self.outline_width_slider.blockSignals(False)
    self.vline_length_slider.blockSignals(False)
    self.hline_length_slider.blockSignals(False)
    self.line_thickness_slider.blockSignals(False)
    self.gap_slider.blockSignals(False)
    self.circle_outline_btn.blockSignals(False)
    self.circle_outline_width_slider.blockSignals(False)
    self.circle_thickness_slider.blockSignals(False)
    self.circle_diameter_slider.blockSignals(False)
    self.chevron_outline_btn.blockSignals(False)
    self.chevron_outline_width_slider.blockSignals(False)
    self.chevron_thickness_slider.blockSignals(False)
    self.chevron_length_slider.blockSignals(False)
    self.image_crosshair_size_slider.blockSignals(False)
    self.crosshair_outline_alpha_slider.blockSignals(False)
    self.circle_outline_alpha_slider.blockSignals(False)
    self.chevron_outline_alpha_slider.blockSignals(False)
    self.dot_shape_box.blockSignals(False)
    if hasattr(self, 'outer_line_btn'):
        self.outer_line_btn.blockSignals(False)
        self.outer_vline_length_slider.blockSignals(False)
        self.outer_hline_length_slider.blockSignals(False)
        self.outer_line_alpha_slider.blockSignals(False)
        self.outer_line_thickness_slider.blockSignals(False)
        self.outer_gap_slider.blockSignals(False)
    if hasattr(self, 'dot_offset_x_slider'):
        self.dot_offset_x_slider.blockSignals(False)
        self.dot_offset_y_slider.blockSignals(False)
        self.dot_offset_x_edit.blockSignals(False)
        self.dot_offset_y_edit.blockSignals(False)

    self._initial_load_complete = True


def update_outline_enabled(self, checked):
    self.overlay.crosshair_outline_enabled = checked
    self.schedule_overlay_update()

def update_outline_width(self, val):
    self.overlay.crosshair_outline_width = val
    self.outline_width_edit.setText(str(val))
    self.schedule_overlay_update()

def update_vline_length(self, val):
    self.overlay.crosshair_vline_length = val
    self.vline_length_edit.setText(str(val))
    self.schedule_overlay_update()

def update_hline_length(self, val):
    self.overlay.crosshair_hline_length = val
    self.hline_length_edit.setText(str(val))
    self.schedule_overlay_update()

def update_line_thickness(self, val):
    self.overlay.crosshair_thickness = val
    self.line_thickness_edit.setText(str(val))
    self.schedule_overlay_update()

def update_gap(self, val):
    self.overlay.crosshair_gap = val
    self.gap_edit.setText(str(val))
    self.schedule_overlay_update()

def update_circle_outline_enabled(self, checked):
    self.overlay.circle_outline_enabled = checked
    self.schedule_overlay_update()

def update_circle_outline_width(self, val):
    self.overlay.circle_outline_width = val
    self.circle_outline_width_edit.setText(str(val))
    self.schedule_overlay_update()

def update_circle_thickness(self, val):
    self.overlay.circle_thickness = val
    self.circle_thickness_edit.setText(str(val))
    self.schedule_overlay_update()

def update_circle_diameter(self, val):
    self.overlay.circle_diameter = val
    self.circle_diameter_edit.setText(str(val))
    self.schedule_overlay_update()

def update_drawing_order(self, index):
    if index == 0: # "ドットを上に描画"
        self.overlay.drawing_order = "dot_on_top"
    else: # "クロスヘアを上に描画"
        self.overlay.drawing_order = "crosshair_on_top"
    self.overlay.save_global_config() # Save the new drawing order
    self.schedule_overlay_update() # Request overlay redraw

def update_outer_line_enabled(self, checked):
    self.overlay.outer_line_enabled = checked
    self.schedule_overlay_update()

def update_outer_vline_length(self, val):
    self.overlay.outer_vline_length = val
    self.outer_vline_length_edit.setText(str(val))
    self.schedule_overlay_update()

def update_outer_hline_length(self, val):
    self.overlay.outer_hline_length = val
    self.outer_hline_length_edit.setText(str(val))
    self.schedule_overlay_update()

def update_outer_line_alpha(self, val):
    alpha = val / 100.0
    self.overlay.outer_line_alpha = alpha
    self.outer_line_alpha_edit.setText(f"{alpha:.3f}")
    self.schedule_overlay_update()

def update_outer_line_thickness(self, val):
    self.overlay.outer_line_thickness = val
    self.outer_line_thickness_edit.setText(str(val))
    self.schedule_overlay_update()

def update_outer_gap(self, val):
    self.overlay.outer_gap = val
    self.outer_gap_edit.setText(str(val))
    self.schedule_overlay_update()

def update_dot_offset_x(self, val):
    self.overlay.dot_offset_x = val
    self.dot_offset_x_edit.setText(str(val))
    self.schedule_overlay_update()

def update_dot_offset_y(self, val):
    self.overlay.dot_offset_y = val
    self.dot_offset_y_edit.setText(str(val))
    self.schedule_overlay_update()