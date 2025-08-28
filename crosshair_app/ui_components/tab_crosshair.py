
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
    panel.shape_box.addItems(["十字", "十字 (ギャップなし)", "円", "矢印 (シェブロン)", "MAME", "カスタム画像"])
    panel.shape_box.currentTextChanged.connect(panel.update_crosshair_shape)
    shape_layout.addWidget(QtWidgets.QLabel("形状:"))
    shape_layout.addWidget(panel.shape_box, 1)
    ch_layout.addLayout(shape_layout)

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
