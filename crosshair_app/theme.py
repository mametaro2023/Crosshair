from PyQt5 import QtGui, QtWidgets

def apply_modern_dark_theme(app: QtWidgets.QApplication) -> None:
    app.setStyle("Fusion")

    # カラーパレットの定義
    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(30, 30, 30))
    dark_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(212, 212, 212))
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(37, 37, 38))
    dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(45, 45, 45))
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(30, 30, 30))
    dark_palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(212, 212, 212))
    dark_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(212, 212, 212))
    dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(51, 51, 51))
    dark_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(212, 212, 212))
    dark_palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 59, 59))
    dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(55, 148, 255))
    dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 122, 204))
    dark_palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(127, 127, 127))
    dark_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, QtGui.QColor(127, 127, 127))

    app.setPalette(dark_palette)

    # スタイルシートの定義
    app.setStyleSheet("""
        QWidget {
            color: #d4d4d4;
            font-family: 'Yu Gothic UI', 'Meiryo', 'Segoe UI', sans-serif;
            font-size: 9pt;
        }
        
        /* メインウィンドウとダイアログ */
        #controlPanel, QDialog {
            background-color: #1e1e1e;
        }

        /* メニューバー */
        QMenuBar {
            background-color: #2d2d2d;
            border-bottom: 1px solid #3c3c3c;
        }
        QMenuBar::item:selected {
            background-color: #3c3c3c;
        }
        QMenu {
            background-color: #252526;
            border: 1px solid #3c3c3c;
        }
        QMenu::item:selected {
            background-color: #007acc;
        }

        /* グループボックス */
        QGroupBox {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            margin-top: 12px;
            padding: 10px 8px 8px 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            left: 10px;
            color: #00aaff;
            font-size: 10pt;
            font-weight: bold;
        }

        /* プッシュボタン */
        QPushButton {
            background-color: #333333;
            border: 1px solid #4d4d4d;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #404040;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
        }
        QPushButton:disabled {
            background-color: #252526;
            color: #6a6a6a;
            border-color: #3a3a3a;
        }
        QPushButton[accent="true"] {
            background-color: #007acc;
            border: none;
            color: #ffffff;
        }
        QPushButton[accent="true"]:hover { background-color: #008ae6; }
        QPushButton[accent="true"]:pressed { background-color: #006bb3; }

        /* マスター切り替えボタン */
        QPushButton#masterToggleButton {
            background-color: #b83b2c; /* Red */
            border: none;
        }
        QPushButton#masterToggleButton:hover { background-color: #c94a3b; }
        QPushButton#masterToggleButtonActive {
            background-color: #3b8b2c; /* Green */
            border: none;
        }
        QPushButton#masterToggleButtonActive:hover { background-color: #4a9c3b; }
        QPushButton#masterToggleButtonMonitoring {
            background-color: #5f676e;
            border: none;
        }

        /* コンボボックスとラインエディット */
        QComboBox, QLineEdit {
            background-color: #252526;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 6px 10px;
        }
        QComboBox:hover, QLineEdit:hover {
            border-color: #007acc;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #252526;
            border: 1px solid #3c3c3c;
            selection-background-color: #007acc;
            outline: 0px;
        }

        /* スライダー */
        QSlider::groove:horizontal {
            height: 4px;
            background: #3c3c3c;
            border-radius: 2px;
        }
        QSlider::handle:horizontal {
            background: #00aaff;
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        QSlider::handle:horizontal:hover {
            background: #37b8ff;
        }

        /* チェックボックス */
        QCheckBox {
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
        }
        QCheckBox::indicator:unchecked {
            background-color: #252526;
            border: 1px solid #3c3c3c;
        }
        QCheckBox::indicator:unchecked:hover {
            border-color: #007acc;
        }
        QCheckBox::indicator:checked {
            background-color: #007acc;
            border: 1px solid #007acc;
            /* You can add a check mark icon here using image property */
            /* image: url(:/icons/check.svg); */
        }
        
        /* ラベル */
        QLabel {
            background-color: transparent;
        }

        /* タブウィジェット */
        QTabWidget::pane {
            border-top: 1px solid #3c3c3c;
        }
        QTabBar::tab {
            background: #2d2d2d;
            border: 1px solid #3c3c3c;
            border-bottom: none;
            padding: 8px 20px;
            font-weight: bold;
            color: #a0a0a0;
        }
        QTabBar::tab:selected {
            background: #1e1e1e;
            border-color: #3c3c3c;
            border-bottom-color: #1e1e1e; /* paneのtop-borderと重なる部分を隠す */
            color: #ffffff;
        }
        QTabBar::tab:!selected:hover {
            background: #3c3c3c;
        }
    """)
