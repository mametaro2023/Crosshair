
from PyQt5 import QtWidgets, QtCore, QtGui
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from .. import config

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'TakaoPGothic', 'IPAPGothic', 'VL PGothic']
        plt.rcParams['axes.unicode_minus'] = False
        
        plt.style.use('dark_background')
        self.fig, self.axes = plt.subplots(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.apply_style()
        self.setStyleSheet("background-color: transparent;") # Make widget background transparent

    def apply_style(self):
        # Improved styling
        self.fig.patch.set_facecolor('#282c34')  # Darker, softer background
        self.axes.set_facecolor('#282c34')

        # Grid
        self.axes.grid(True, which='both', linestyle='--', linewidth=0.5, color='#474b52')

        # Spines
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['left'].set_color('#474b52') # Make left spine visible but subtle
        self.axes.spines['bottom'].set_color('#474b52') # Make bottom spine visible but subtle
        self.axes.spines['left'].set_linewidth(0.7)
        self.axes.spines['bottom'].set_linewidth(0.7)

        # Ticks
        self.axes.tick_params(axis='x', colors='#b0b0b0', direction='out', labelsize=9) # Lighter gray, smaller labels
        self.axes.tick_params(axis='y', colors='#b0b0b0', direction='out', labelsize=9) # Lighter gray, smaller labels
        self.axes.xaxis.label.set_color('#e0e0e0') # Slightly lighter label color
        self.axes.yaxis.label.set_color('#e0e0e0') # Slightly lighter label color
        self.axes.title.set_color('#ffffff') # Pure white title
        self.axes.title.set_fontsize(14) # Ensure title size is consistent
        self.axes.title.set_fontweight('bold')
        self.axes.set_xlabel('') # Keep these empty, _update_apex_graph will set them
        self.axes.set_ylabel('')

class ApexRankTab(QtWidgets.QWidget):
    def __init__(self, parent=None, overlay_obj=None):
        super().__init__(parent)
        self.overlay = overlay_obj
        self.setupUi()

    def setupUi(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Settings Group ---
        settings_group = QtWidgets.QGroupBox("設定")
        
        # Create a vertical layout for the settings group content
        settings_group_vlayout = QtWidgets.QVBoxLayout(settings_group)

        # Horizontal layout for platform and username
        platform_username_hlayout = QtWidgets.QHBoxLayout()
        
        platform_label = QtWidgets.QLabel("プラットフォーム:")
        self.platform_combo = QtWidgets.QComboBox()
        platforms = {"PC": "PC", "PS4/PS5": "PS4", "XBOX": "X1"}
        for display, value in platforms.items():
            self.platform_combo.addItem(display, userData=value)
        self.platform_combo.setFixedWidth(100)

        username_label = QtWidgets.QLabel("ユーザー名:")
        self.username_edit = QtWidgets.QLineEdit()
        self.username_edit.setPlaceholderText("Origin/PSN/Xbox Live ID")

        platform_username_hlayout.addWidget(platform_label)
        platform_username_hlayout.addWidget(self.platform_combo)
        platform_username_hlayout.addSpacing(15)
        platform_username_hlayout.addWidget(username_label)
        platform_username_hlayout.addWidget(self.username_edit, 1)

        # New: Auto-track checkbox
        self.auto_track_checkbox = QtWidgets.QCheckBox("Apex起動時に自動でトラッキングを開始")

        self.track_button = QtWidgets.QPushButton("トラッキング開始")
        self.track_button.setCheckable(True)
        self.track_button.setObjectName("accentButton")

        # Set initial values from overlay object
        saved_platform = self.overlay.apex_platform
        index = self.platform_combo.findData(saved_platform)
        if index != -1:
            self.platform_combo.setCurrentIndex(index)

        saved_username = self.overlay.apex_username
        self.username_edit.setText(saved_username)

        saved_auto_track = self.overlay.auto_track_apex
        print(f"[DEBUG] ApexRankTab: Initial auto_track_apex state from overlay: {saved_auto_track}")
        self.auto_track_checkbox.setChecked(saved_auto_track)

        # Connect signals to save changes
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
        self.username_edit.textChanged.connect(self._on_username_changed)
        self.auto_track_checkbox.toggled.connect(self._on_auto_track_toggled)

        # Add components to the main settings group vertical layout
        settings_group_vlayout.addLayout(platform_username_hlayout)
        settings_group_vlayout.addWidget(self.auto_track_checkbox)
        settings_group_vlayout.addWidget(self.track_button)

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

    def _on_platform_changed(self):
        selected_platform_data = self.platform_combo.currentData()
        self.overlay.apex_platform = selected_platform_data
        self.overlay.save_global_config()

    def _on_username_changed(self):
        username = self.username_edit.text()
        self.overlay.apex_username = username
        self.overlay.save_global_config()

    def _on_auto_track_toggled(self, checked):
        self.overlay.auto_track_apex = checked
        self.overlay.save_global_config()

def create_tab(parent_control_panel, overlay_obj):
    # This function is called by ui.py
    # It creates an instance of our tab widget
    tab = ApexRankTab(parent_control_panel, overlay_obj)
    return tab
