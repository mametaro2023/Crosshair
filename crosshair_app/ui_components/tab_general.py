
from PyQt5 import QtWidgets

def create_tab(panel):
    """「全般」タブを生成する"""
    general_tab = QtWidgets.QWidget()
    general_layout = QtWidgets.QVBoxLayout(general_tab)
    general_layout.setContentsMargins(10, 15, 10, 10)
    general_layout.setSpacing(12)
    
    monitor_layout = QtWidgets.QHBoxLayout()
    monitor_label = QtWidgets.QLabel("表示モニター:")
    panel.monitor_selection_box = QtWidgets.QComboBox()
    panel.monitor_selection_box.currentIndexChanged.connect(panel.monitor_changed)
    monitor_layout.addWidget(monitor_label)
    monitor_layout.addWidget(panel.monitor_selection_box, 1)
    general_layout.addLayout(monitor_layout)

    panel.apex_monitor_action = QtWidgets.QCheckBox("Apex Legendsの起動を検出して自動ON/OFF")
    try:
        from .. import utils
        if utils.psutil:
            panel.apex_monitor_action.setChecked(panel.overlay.monitor_apex)
            panel.apex_monitor_action.toggled.connect(panel.toggle_apex_monitoring)
        else:
            raise ImportError
    except ImportError:
        panel.apex_monitor_action.setEnabled(False)
        panel.apex_monitor_action.setToolTip("この機能を利用するには 'psutil' ライブラリが必要です。(pip install psutil)")
    general_layout.addWidget(panel.apex_monitor_action)

    panel.fade_on_shoot_checkbox = QtWidgets.QCheckBox("射撃中はクロスヘアを薄くする")
    panel.fade_on_shoot_checkbox.toggled.connect(panel.toggle_fade_on_shoot)
    general_layout.addWidget(panel.fade_on_shoot_checkbox)
    general_layout.addStretch()
    
    return general_tab
