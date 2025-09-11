from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QComboBox, QLabel, QPushButton, QGroupBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import pyqtgraph as pg

class StatsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()

    def setupUi(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        # --- Settings Group ---
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout()

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["PC", "PS4", "X1"])
        
        self.player_name_input = QLineEdit()
        self.player_name_input.setPlaceholderText("Enter player name")

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API Key from mozambiquehe.re")
        self.api_key_input.setEchoMode(QLineEdit.Password)

        self.start_button = QPushButton("Start Tracking")
        self.stop_button = QPushButton("Stop Tracking")
        self.stop_button.setEnabled(False)

        settings_layout.addRow(QLabel("Platform:"), self.platform_combo)
        settings_layout.addRow(QLabel("Player Name:"), self.player_name_input)
        
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        settings_layout.addRow(button_layout)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # --- Stats Display Group ---
        stats_group = QGroupBox("Current Stats")
        stats_layout = QVBoxLayout()

        self.current_rank_label = QLabel("Rank: N/A")
        self.current_rank_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        
        self.score_layout = QHBoxLayout()
        self.current_score_label = QLabel("Score: N/A")
        self.current_score_label.setFont(QFont("Segoe UI", 12))
        self.score_diff_label = QLabel("")
        self.score_diff_label.setFont(QFont("Segoe UI", 12, QFont.Bold))

        self.score_layout.addWidget(self.current_score_label)
        self.score_layout.addSpacing(10)
        self.score_layout.addWidget(self.score_diff_label)
        self.score_layout.addStretch()

        stats_layout.addWidget(self.current_rank_label)
        stats_layout.addLayout(self.score_layout)
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)

        # --- Graph Group ---
        graph_group = QGroupBox("Rank Score History (Today)")
        graph_layout = QVBoxLayout()
        
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setLabel('left', 'Rank Score (RP)')
        self.graph_widget.setLabel('bottom', 'Time')
        self.graph_widget.showGrid(x=True, y=True)
        self.plot_data_item = self.graph_widget.plot(pen=pg.mkPen('b', width=2))

        graph_layout.addWidget(self.graph_widget)
        graph_group.setLayout(graph_layout)
        main_layout.addWidget(graph_group)
