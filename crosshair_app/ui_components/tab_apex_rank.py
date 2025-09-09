
from PyQt5 import QtWidgets, QtCore, QtGui
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Set Japanese font and handle minus sign
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'TakaoPGothic', 'IPAPGothic', 'VL PGothic']
        plt.rcParams['axes.unicode_minus'] = False
        
        plt.style.use('dark_background')
        self.fig, self.axes = plt.subplots(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.fig.patch.set_facecolor('#222222')
        self.axes.set_facecolor('#222222')
        self.axes.tick_params(colors='white')
        self.axes.xaxis.label.set_color('white')
        self.axes.yaxis.label.set_color('white')
        self.axes.title.set_color('white')

class ApexRankTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()

    def setupUi(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Settings Group ---
        settings_group = QtWidgets.QGroupBox("設定")
        settings_layout = QtWidgets.QHBoxLayout(settings_group)
        
        platform_label = QtWidgets.QLabel("プラットフォーム:")
        self.platform_combo = QtWidgets.QComboBox()
        platforms = {"PC": "PC", "PS4/PS5": "PS4", "XBOX": "X1"}
        for display, value in platforms.items():
            self.platform_combo.addItem(display, userData=value)
        self.platform_combo.setFixedWidth(100)

        username_label = QtWidgets.QLabel("ユーザー名:")
        self.username_edit = QtWidgets.QLineEdit()
        self.username_edit.setPlaceholderText("Origin/PSN/Xbox Live ID")

        self.track_button = QtWidgets.QPushButton("トラッキング開始")
        self.track_button.setCheckable(True)
        self.track_button.setObjectName("accentButton")

        settings_layout.addWidget(platform_label)
        settings_layout.addWidget(self.platform_combo)
        settings_layout.addSpacing(15)
        settings_layout.addWidget(username_label)
        settings_layout.addWidget(self.username_edit, 1)
        settings_layout.addSpacing(15)
        settings_layout.addWidget(self.track_button)
        layout.addWidget(settings_group)

        # --- Status Group ---
        status_group = QtWidgets.QGroupBox("現在のランク")
        status_layout = QtWidgets.QHBoxLayout(status_group)
        status_layout.setSpacing(20)

        self.current_rank_label = QtWidgets.QLabel("N/A")
        self.current_rank_label.setObjectName("rankLabel")
        self.current_score_label = QtWidgets.QLabel("N/A")
        self.current_score_label.setObjectName("scoreLabel")
        self.score_change_label = QtWidgets.QLabel("")
        self.score_change_label.setObjectName("changeLabel")

        status_layout.addWidget(QtWidgets.QLabel("ランク:"))
        status_layout.addWidget(self.current_rank_label)
        status_layout.addStretch()
        status_layout.addWidget(QtWidgets.QLabel("スコア:"))
        status_layout.addWidget(self.current_score_label)
        status_layout.addWidget(self.score_change_label)
        status_layout.addStretch()
        layout.addWidget(status_group)

        # --- Graph Group ---
        graph_group = QtWidgets.QGroupBox("ランクスコア推移 (セッション)")
        graph_layout = QtWidgets.QVBoxLayout(graph_group)
        self.graph_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        graph_layout.addWidget(self.graph_canvas)
        layout.addWidget(graph_group, 1)

def create_tab(parent_control_panel):
    # This function is called by ui.py
    # It creates an instance of our tab widget
    tab = ApexRankTab(parent_control_panel)
    return tab
