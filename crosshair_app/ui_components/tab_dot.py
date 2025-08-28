
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
    dot_layout.addStretch()

    return dot_tab
