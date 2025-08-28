from PyQt5 import QtGui, QtWidgets

def apply_dark_theme(app: QtWidgets.QApplication) -> None:
    app.setStyle("Fusion")

    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(37, 41, 45))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(224, 224, 224))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(28, 31, 34))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(44, 47, 51))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(45, 47, 54))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(224, 224, 224))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(224, 224, 224))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(45, 47, 54))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(224, 224, 224))
    palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 0, 0))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 120, 215))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor(0, 170, 255))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QWidget {
            color: #e0e0e0;
            font-family: 'Noto Sans JP', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            font-size: 10pt;
        }
        QDialog, QMenuBar, QMenu {
            background-color: #25292d;
        }
        QMenuBar {
            border-bottom: 1px solid #3c4048;
        }
        QMenu::item:selected {
            background-color: #0078d7;
        }

        /* QGroupBox: 透過背景が頻繁な再描画時にゴースト(重なり)を生むので不透明色に変更 */
        QGroupBox {
            background-color: #2c3135; /* 以前: rgba(44, 49, 53, 0.7) */
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            margin-top: 10px;
            padding: 10px 5px 5px 5px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 10px;
            left: 10px;
            color: #00aaff;
            font-weight: bold;
        }

        QPushButton {
            background-color: #40454c;
            border: 1px solid #50555c;
            padding: 8px 12px;
            border-radius: 4px;
            color: #e0e0e0;
        }
        QPushButton:hover {
            background-color: #4a4f57;
            border-color: #5a5f67;
        }
        QPushButton:pressed {
            background-color: #2a2e36;
        }
        QPushButton[accent="true"] {
            background-color: #0078d7;
            border: 1px solid #0088f7;
            color: #ffffff;
            font-weight: bold;
        }
        QPushButton[accent="true"]:hover { background-color: #0088f7; }
        QPushButton[accent="true"]:pressed { background-color: #0068c7; }

        QPushButton#masterToggleButton {
            background-color: #c0392b;
            border: 1px solid #e74c3c;
            font-weight: bold;
            padding: 10px 12px;
        }
        QPushButton#masterToggleButton:hover { background-color: #e74c3c; }

        QPushButton#masterToggleButtonActive {
            background-color: #27ae60;
            border: 1px solid #2ecc71;
            font-weight: bold;
            padding: 10px 12px;
        }
        QPushButton#masterToggleButtonActive:hover { background-color: #2ecc71; }

        QPushButton#masterToggleButtonMonitoring {
            background-color: #5f676e;
            border: 1px solid #78828a;
            font-weight: bold;
            padding: 10px 12px;
        }
        QPushButton#masterToggleButtonMonitoring:hover { background-color: #6a737b; }

        QComboBox, QLineEdit {
            background-color: #40454c;
            border: 1px solid #50555c;
            border-radius: 4px;
            padding: 6px 10px;
        }
        QComboBox QAbstractItemView {
            background-color: #2c3136;
            border: 1px solid #3c4048;
            selection-background-color: #0078d7;
        }

        QSlider::groove:horizontal {
            height: 4px;
            background: #50555c;
            border-radius: 2px;
        }
        QSlider::handle:horizontal {
            background: #00aaff;
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }

        QCheckBox {
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 16px; height: 16px;
        }
        QCheckBox::indicator:unchecked {
            border: 1px solid #3c4048; background: #2c3136; border-radius: 4px;
        }
        QCheckBox::indicator:checked {
            background-color: #0078d7; border: 1px solid #0088f7; border-radius: 4px;
        }
        """
    )
