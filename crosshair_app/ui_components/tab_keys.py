
from PyQt5 import QtWidgets

def create_tab(panel):
    """「キー無効化」タブを生成する"""
    keys_tab = QtWidgets.QWidget()
    keys_layout = QtWidgets.QVBoxLayout(keys_tab)
    keys_layout.setContentsMargins(10, 15, 10, 10)
    keys_layout.setSpacing(12)
    
    disabled_keys_group = QtWidgets.QGroupBox("現在無効化中のキー")
    disabled_keys_layout = QtWidgets.QVBoxLayout(disabled_keys_group)
    panel.disabled_keys_label = QtWidgets.QLabel("なし")
    panel.disabled_keys_label.setWordWrap(True)
    disabled_keys_layout.addWidget(panel.disabled_keys_label)
    keys_layout.addWidget(disabled_keys_group)

    keys_btn_layout = QtWidgets.QHBoxLayout()
    disable_btn = QtWidgets.QPushButton("無効化キーを追加")
    disable_btn.clicked.connect(panel.disable_key_gui)
    enable_btn = QtWidgets.QPushButton("無効化キーを削除")
    enable_btn.clicked.connect(panel.enable_key_gui)
    keys_btn_layout.addWidget(disable_btn)
    keys_btn_layout.addWidget(enable_btn)
    keys_layout.addLayout(keys_btn_layout)
    
    enable_all_btn = QtWidgets.QPushButton("すべてのキーを有効化")
    enable_all_btn.clicked.connect(panel.enable_all_keys_gui)
    keys_layout.addWidget(enable_all_btn)
    keys_layout.addStretch()

    return keys_tab
