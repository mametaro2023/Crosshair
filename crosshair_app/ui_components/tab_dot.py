
from PyQt5 import QtCore, QtWidgets

def create_tab(panel):
    """「ドット」タブを生成する"""
    dot_tab = QtWidgets.QWidget()
    dot_layout = QtWidgets.QVBoxLayout(dot_tab)
    dot_layout.setContentsMargins(10, 15, 10, 10)
    dot_layout.setSpacing(12)

    panel.dot_btn = QtWidgets.QCheckBox("ドットを表示")
    panel.dot_btn.toggled.connect(panel.toggle_dot_button)
    dot_layout.addWidget(panel.dot_btn)

    # Dot Shape Selection
    dot_shape_layout = QtWidgets.QHBoxLayout()
    dot_shape_label = QtWidgets.QLabel("形状:")
    panel.dot_shape_box = QtWidgets.QComboBox()
    panel.dot_shape_box.addItem("円")
    panel.dot_shape_box.addItem("正方形")
    panel.dot_shape_box.addItem("正三角形上向き")
    panel.dot_shape_box.currentTextChanged.connect(panel.update_dot_shape)
    dot_shape_layout.addWidget(dot_shape_label)
    dot_shape_layout.addWidget(panel.dot_shape_box, 1)
    dot_layout.addLayout(dot_shape_layout)

    dotsize_layout = QtWidgets.QHBoxLayout()
    panel.dot_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    panel.dot_slider.setRange(0, 100)
    panel.dot_value_edit = QtWidgets.QLineEdit()
    panel.dot_value_edit.setFixedWidth(45)
    panel.dot_slider.valueChanged.connect(panel.update_dot_size)
    dotsize_layout.addWidget(QtWidgets.QLabel("サイズ:"))
    dotsize_layout.addWidget(panel.dot_slider)
    dotsize_layout.addWidget(panel.dot_value_edit)
    dot_layout.addLayout(dotsize_layout)

    dot_out_color_layout, panel.dot_out_color_square = panel.make_color_button("外枠の色:", lambda: panel.overlay.dot_outer_color, panel.set_dot_outer_color, lambda: panel.overlay.update())
    dot_in_color_layout, panel.dot_in_color_square = panel.make_color_button("内側の色:", lambda: panel.overlay.dot_inner_color, panel.set_dot_inner_color, lambda: panel.overlay.update())
    dot_layout.addLayout(dot_out_color_layout)
    dot_layout.addLayout(dot_in_color_layout)

    dot_alpha_layout = QtWidgets.QHBoxLayout()
    panel.dot_alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    panel.dot_alpha_slider.setRange(0, 100)
    panel.dot_alpha_value_edit = QtWidgets.QLineEdit()
    panel.dot_alpha_value_edit.setFixedWidth(45)
    panel.dot_alpha_slider.valueChanged.connect(panel.update_dot_alpha)
    dot_alpha_layout.addWidget(QtWidgets.QLabel("透明度:"))
    dot_alpha_layout.addWidget(panel.dot_alpha_slider)
    dot_alpha_layout.addWidget(panel.dot_alpha_value_edit)
    dot_layout.addLayout(dot_alpha_layout)

    # X Offset
    offset_x_layout = QtWidgets.QHBoxLayout()
    panel.dot_offset_x_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    panel.dot_offset_x_slider.setRange(-100, 100)
    panel.dot_offset_x_slider.setValue(0)
    panel.dot_offset_x_edit = QtWidgets.QLineEdit("0")
    panel.dot_offset_x_edit.setFixedWidth(45)
    panel.dot_offset_x_slider.valueChanged.connect(panel.update_dot_offset_x)
    offset_x_layout.addWidget(QtWidgets.QLabel("X オフセット:"))
    offset_x_layout.addWidget(panel.dot_offset_x_slider)
    offset_x_layout.addWidget(panel.dot_offset_x_edit)
    dot_layout.addLayout(offset_x_layout)

    # Y Offset
    offset_y_layout = QtWidgets.QHBoxLayout()
    panel.dot_offset_y_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    panel.dot_offset_y_slider.setRange(-100, 100)
    panel.dot_offset_y_slider.setValue(0)
    panel.dot_offset_y_edit = QtWidgets.QLineEdit("0")
    panel.dot_offset_y_edit.setFixedWidth(45)
    panel.dot_offset_y_slider.valueChanged.connect(panel.update_dot_offset_y)
    offset_y_layout.addWidget(QtWidgets.QLabel("Y オフセット:"))
    offset_y_layout.addWidget(panel.dot_offset_y_slider)
    offset_y_layout.addWidget(panel.dot_offset_y_edit)
    dot_layout.addLayout(offset_y_layout)

    dot_layout.addStretch()

    return dot_tab
