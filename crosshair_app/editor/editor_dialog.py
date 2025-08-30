import json
import os
import keyboard
from PyQt5 import QtCore, QtGui, QtWidgets
from .canvas import Canvas

class EditorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, shape_preset_folder=""):
        super().__init__(parent)
        self.shape_preset_folder = shape_preset_folder
        self.setWindowTitle("クロスヘアエディタ")
        self.setMinimumSize(560, 440)

        self.saved_path = None

        # Set stylesheet for tool buttons
        self.setStyleSheet("""
            QPushButton[objectName="toolButton"] {
                background-color: #333333;
                color: #cccccc;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton[objectName="toolButton"]:hover {
                background-color: #444444;
            }
            QPushButton[objectName="toolButton_selected"] {
                background-color: #0078d7; /* Accent color */
                color: white;
                border: 1px solid #0078d7;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        # Layouts
        self.main_layout = QtWidgets.QHBoxLayout(self)
        left_panel_layout = QtWidgets.QVBoxLayout()
        left_panel_layout.setSpacing(15)

        # Canvas (Right Panel)を先に作成
        self.canvas = Canvas(self)

        # Left Panel Widgets
        self._create_tools_group(left_panel_layout)
        self._create_palette_group(left_panel_layout)
        left_panel_layout.addStretch()

        # Assemble main layout
        self.main_layout.addLayout(left_panel_layout)
        self.main_layout.addWidget(self.canvas)

        # --- Dialog Buttons ---
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        left_panel_layout.addWidget(button_box)

        # ホットキーの登録
        self.register_hotkeys()

        # 初期表示の更新
        self._update_current_color_display()

    def register_hotkeys(self):
        # Ctrl+Z で元に戻す
        keyboard.add_hotkey('ctrl+z', self.canvas.undo, suppress=False)
        # Ctrl+Shift+Z でやり直し
        keyboard.add_hotkey('ctrl+shift+z', self.canvas.redo, suppress=False)

    def unregister_hotkeys(self):
        keyboard.remove_hotkey('ctrl+z')
        keyboard.remove_hotkey('ctrl+shift+z')

    def closeEvent(self, event):
        self.unregister_hotkeys()
        super().closeEvent(event)

    def _create_tools_group(self, parent_layout):
        tools_group = QtWidgets.QGroupBox("ツール")
        tools_layout = QtWidgets.QHBoxLayout(tools_group)
        
        pen_button = QtWidgets.QPushButton("ペン")
        pen_button.setCheckable(True)
        pen_button.setChecked(True)
        pen_button.clicked.connect(lambda: self.canvas.set_tool('pencil'))
        pen_button.setObjectName("toolButton_selected") # Initial selected state

        eraser_button = QtWidgets.QPushButton("消しゴム")
        eraser_button.setCheckable(True)
        eraser_button.clicked.connect(lambda: self.canvas.set_tool('eraser'))
        eraser_button.setObjectName("toolButton")

        line_button = QtWidgets.QPushButton("直線")
        line_button.setCheckable(True)
        line_button.clicked.connect(lambda: self.canvas.set_tool('line'))
        line_button.setObjectName("toolButton")

        circle_button = QtWidgets.QPushButton("円")
        circle_button.setCheckable(True)
        circle_button.clicked.connect(lambda: self.canvas.set_tool('circle'))
        circle_button.setObjectName("toolButton")

        # Exclusive buttons
        button_group = QtWidgets.QButtonGroup(self)
        button_group.setExclusive(True)
        button_group.addButton(pen_button)
        button_group.addButton(eraser_button)
        button_group.addButton(line_button)
        button_group.addButton(circle_button)

        tools_layout.addWidget(pen_button)
        tools_layout.addWidget(eraser_button)
        tools_layout.addWidget(line_button)
        tools_layout.addWidget(circle_button)

        # Connect button group to update tool display
        button_group.buttonClicked.connect(self._update_current_tool_display)

        parent_layout.addWidget(tools_group)

    def _update_current_tool_display(self, clicked_button):
        for button in clicked_button.group().buttons():
            if button is clicked_button:
                button.setObjectName("toolButton_selected")
            else:
                button.setObjectName("toolButton")
            button.style().unpolish(button)
            button.style().polish(button)

    def _create_palette_group(self, parent_layout):
        brush_size_group = QtWidgets.QGroupBox("ブラシサイズ")
        brush_size_layout = QtWidgets.QHBoxLayout(brush_size_group)
        self.brush_size_spinbox = QtWidgets.QSpinBox()
        self.brush_size_spinbox.setRange(1, 10) # 1から10ピクセルまで
        self.brush_size_spinbox.setValue(self.canvas.brush_size) # 初期値
        self.brush_size_spinbox.valueChanged.connect(self.canvas.set_brush_size)
        brush_size_layout.addWidget(self.brush_size_spinbox)
        parent_layout.addWidget(brush_size_group)

        # 現在の色の表示
        self.current_color_display = QtWidgets.QLabel()
        self.current_color_display.setFixedSize(48, 24) # 小さな四角で色を表示
        self.current_color_display.setStyleSheet("border: 1px solid #808080; background-color: black;") # 初期色
        self.current_color_display.setAlignment(QtCore.Qt.AlignCenter)
        self.current_color_display.setText("色") # Placeholder text
        
        color_display_layout = QtWidgets.QHBoxLayout()
        color_display_layout.addWidget(QtWidgets.QLabel("現在の色:"))
        color_display_layout.addWidget(self.current_color_display)
        color_display_layout.addStretch()
        parent_layout.addLayout(color_display_layout)

        palette_group = QtWidgets.QGroupBox("カラーパレット")
        palette_layout = QtWidgets.QGridLayout(palette_group)
        palette_layout.setSpacing(4)

        colors = [
            "#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF",
            "#FFFF00", "#FF00FF", "#00FFFF", "#808080", "#00FF66"
        ]

        for i, color_hex in enumerate(colors):
            button = QtWidgets.QPushButton()
            button.setFixedSize(24, 24)
            button.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #808080;")
            button.clicked.connect(self._make_color_button_handler(QtGui.QColor(color_hex)))
            palette_layout.addWidget(button, i // 5, i % 5)
        
        # カスタム色選択ボタン
        custom_color_button = QtWidgets.QPushButton("カスタム色を選択...")
        custom_color_button.clicked.connect(self._pick_custom_color)
        palette_layout.addWidget(custom_color_button, len(colors) // 5, 0, 1, 5) # 新しい行に5列スパンで配置

        parent_layout.addWidget(palette_group)

    def _make_color_button_handler(self, color):
        """Create a closure to capture the color for the button handler."""
        def handler():
            self.canvas.set_pen_color(color)
            self._update_current_color_display()
        return handler

    def _pick_custom_color(self):
        current_color = self.canvas.pen_color
        color = QtWidgets.QColorDialog.getColor(current_color, self, "色を選択")
        if color.isValid():
            self.canvas.set_pen_color(color)
            self._update_current_color_display()

    def _update_current_color_display(self):
        color_hex = self.canvas.pen_color.name()
        self.current_color_display.setStyleSheet(f"border: 1px solid #808080; background-color: {color_hex};")
        self.current_color_display.setText(color_hex.upper())
        # テキストの色を背景色に応じて調整
        qcolor = QtGui.QColor(color_hex)
        # 知覚される輝度を計算 (ITU-R BT.709)
        luminance = (0.2126 * qcolor.red() + 0.7152 * qcolor.green() + 0.0722 * qcolor.blue()) / 255
        text_color = '#000000' if luminance > 0.5 else '#ffffff' # 0.5は一般的なしきい値

        # 完全なスタイルシート文字列を構築
        stylesheet = f"""
            QLabel {{
                border: 1px solid #808080;
                background-color: {color_hex};
                color: {text_color};
                font-weight: bold;
            }}
        """
        self.current_color_display.setStyleSheet(stylesheet)

    def save(self):
        pixel_data = self.canvas.get_pixel_data()
        if not pixel_data:
            QtWidgets.QMessageBox.warning(self, "空のクロスヘア", "何も描画されていません。")
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "クロスヘアを保存", self.shape_preset_folder,
            f"カスタムクロスヘア (*.crshr)")
        
        if path:
            if not path.endswith(".crshr"):
                path += ".crshr"
            
            name = os.path.splitext(os.path.basename(path))[0]
            crshr_data = {
                "name": name,
                "size": [Canvas.GRID_SIZE, Canvas.GRID_SIZE],
                "pixels": pixel_data
            }

            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(crshr_data, f, indent=4)
                self.saved_path = path
                self.accept()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "保存失敗", f"ファイルの保存中にエラーが発生しました:\n{e}")