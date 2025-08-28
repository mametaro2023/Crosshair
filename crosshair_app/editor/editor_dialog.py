import json
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from .canvas import Canvas

class EditorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, shape_preset_folder=""):
        super().__init__(parent)
        self.shape_preset_folder = shape_preset_folder
        self.setWindowTitle("クロスヘアエディタ")
        self.setMinimumSize(560, 440)

        self.saved_path = None

        # Layouts
        self.main_layout = QtWidgets.QHBoxLayout(self)
        left_panel_layout = QtWidgets.QVBoxLayout()
        left_panel_layout.setSpacing(15)

        # Left Panel Widgets
        self._create_tools_group(left_panel_layout)
        self._create_palette_group(left_panel_layout)
        left_panel_layout.addStretch()

        # Canvas (Right Panel)
        self.canvas = Canvas(self)

        # Assemble main layout
        self.main_layout.addLayout(left_panel_layout)
        self.main_layout.addWidget(self.canvas)

        # --- Dialog Buttons ---
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        left_panel_layout.addWidget(button_box)

    def _create_tools_group(self, parent_layout):
        tools_group = QtWidgets.QGroupBox("ツール")
        tools_layout = QtWidgets.QHBoxLayout(tools_group)
        
        pen_button = QtWidgets.QPushButton("ペン")
        pen_button.setCheckable(True)
        pen_button.setChecked(True)
        pen_button.clicked.connect(lambda: self.canvas.set_tool('pen'))

        eraser_button = QtWidgets.QPushButton("消しゴム")
        eraser_button.setCheckable(True)
        eraser_button.clicked.connect(lambda: self.canvas.set_tool('eraser'))

        # Exclusive buttons
        button_group = QtWidgets.QButtonGroup(self)
        button_group.setExclusive(True)
        button_group.addButton(pen_button)
        button_group.addButton(eraser_button)

        tools_layout.addWidget(pen_button)
        tools_layout.addWidget(eraser_button)
        parent_layout.addWidget(tools_group)

    def _create_palette_group(self, parent_layout):
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
        
        parent_layout.addWidget(palette_group)

    def _make_color_button_handler(self, color):
        """Create a closure to capture the color for the button handler."""
        def handler():
            self.canvas.set_pen_color(color)
        return handler

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