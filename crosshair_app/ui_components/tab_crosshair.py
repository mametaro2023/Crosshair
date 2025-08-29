
from PyQt5 import QtCore, QtWidgets

def create_tab(panel):
    """「クロスヘア」タブを生成する"""
    ch_tab = QtWidgets.QWidget()
    ch_layout = QtWidgets.QVBoxLayout(ch_tab)
    ch_layout.setContentsMargins(10, 15, 10, 10)
    ch_layout.setSpacing(12)

    panel.crosshair_btn = QtWidgets.QCheckBox("クロスヘアを表示")
    panel.crosshair_btn.toggled.connect(panel.toggle_crosshair_button)
    ch_layout.addWidget(panel.crosshair_btn)

    shape_layout = QtWidgets.QHBoxLayout()
    panel.shape_box = QtWidgets.QComboBox()
    # アイテムの追加は ui.py の reload_shapes で行うので、ここでは削除
    panel.shape_box.currentTextChanged.connect(panel.update_crosshair_shape)
    shape_layout.addWidget(QtWidgets.QLabel("形状:"))
    shape_layout.addWidget(panel.shape_box, 1)
    ch_layout.addLayout(shape_layout)

    # アドバンスド設定
    panel.advanced_settings_group = QtWidgets.QGroupBox("アドバンスド設定")
    advanced_layout = QtWidgets.QFormLayout(panel.advanced_settings_group)
    advanced_layout.setSpacing(10)

    panel.outline_btn = QtWidgets.QCheckBox("輪郭")
    panel.outline_btn.toggled.connect(panel.update_outline_enabled)
    advanced_layout.addRow(panel.outline_btn)

    panel.outline_width_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    panel.outline_width_slider.setRange(1, 6)
    panel.outline_width_slider.valueChanged.connect(panel.update_outline_width)
    panel.outline_width_label = QtWidgets.QLabel()
    outline_width_layout = QtWidgets.QHBoxLayout()
    outline_width_layout.addWidget(panel.outline_width_slider)
    outline_width_layout.addWidget(panel.outline_width_label)
    advanced_layout.addRow("輪郭の太さ:", outline_width_layout)

    panel.vline_length_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    panel.vline_length_slider.setRange(0, 20)
    panel.vline_length_slider.valueChanged.connect(panel.update_vline_length)
    panel.vline_length_label = QtWidgets.QLabel()
    vline_length_layout = QtWidgets.QHBoxLayout()
    vline_length_layout.addWidget(panel.vline_length_slider)
    vline_length_layout.addWidget(panel.vline_length_label)
    advanced_layout.addRow("縦線の長さ:", vline_length_layout)

    panel.hline_length_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    panel.hline_length_slider.setRange(0, 20)
    panel.hline_length_slider.valueChanged.connect(panel.update_hline_length)
    panel.hline_length_label = QtWidgets.QLabel()
    hline_length_layout = QtWidgets.QHBoxLayout()
    hline_length_layout.addWidget(panel.hline_length_slider)
    hline_length_layout.addWidget(panel.hline_length_label)
    advanced_layout.addRow("横線の長さ:", hline_length_layout)

    panel.line_thickness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    panel.line_thickness_slider.setRange(0, 10)
    panel.line_thickness_slider.valueChanged.connect(panel.update_line_thickness)
    panel.line_thickness_label = QtWidgets.QLabel()
    line_thickness_layout = QtWidgets.QHBoxLayout()
    line_thickness_layout.addWidget(panel.line_thickness_slider)
    line_thickness_layout.addWidget(panel.line_thickness_label)
    advanced_layout.addRow("線の太さ:", line_thickness_layout)

    panel.gap_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    panel.gap_slider.setRange(0, 20)
    panel.gap_slider.valueChanged.connect(panel.update_gap)
    panel.gap_label = QtWidgets.QLabel()
    gap_layout = QtWidgets.QHBoxLayout()
    gap_layout.addWidget(panel.gap_slider)
    gap_layout.addWidget(panel.gap_label)
    advanced_layout.addRow("ギャップ:", gap_layout)

    ch_layout.addWidget(panel.advanced_settings_group)

    panel.custom_image_widget = QtWidgets.QWidget()
    custom_image_layout = QtWidgets.QHBoxLayout(panel.custom_image_widget)
    custom_image_layout.setContentsMargins(0, 5, 0, 0)
    select_image_btn = QtWidgets.QPushButton("画像を選択...")
    select_image_btn.clicked.connect(panel.select_custom_image)
    panel.custom_image_path_label = QtWidgets.QLabel("選択されていません")
    panel.custom_image_path_label.setWordWrap(True)
    custom_image_layout.addWidget(select_image_btn)
    custom_image_layout.addWidget(panel.custom_image_path_label, 1)
    ch_layout.addWidget(panel.custom_image_widget)

    # 色設定UIをコンテナウィジェットに格納
    panel.ch_color_widget = QtWidgets.QWidget()
    ch_color_layout, panel.ch_color_square = panel.make_color_button("色:", lambda: panel.overlay.crosshair_color, panel.set_crosshair_color, lambda: panel.overlay.update())
    ch_color_layout.setContentsMargins(0, 0, 0, 0)
    panel.ch_color_widget.setLayout(ch_color_layout)
    ch_layout.addWidget(panel.ch_color_widget)

    alpha_layout = QtWidgets.QHBoxLayout()
    panel.alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    panel.alpha_slider.setRange(0, 100)
    panel.alpha_value_edit = QtWidgets.QLineEdit()
    panel.alpha_value_edit.setFixedWidth(45)
    panel.alpha_slider.valueChanged.connect(panel.update_alpha)
    alpha_layout.addWidget(QtWidgets.QLabel("透明度:"))
    alpha_layout.addWidget(panel.alpha_slider)
    alpha_layout.addWidget(panel.alpha_value_edit)
    ch_layout.addLayout(alpha_layout)
    ch_layout.addStretch()

    return ch_tab
