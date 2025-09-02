from PyQt5 import QtCore, QtWidgets

class CollapsibleSection(QtWidgets.QWidget):
    def __init__(self, title="", parent=None, expanded=True):
        super().__init__(parent)
        self.title = title

        self.toggle_button = QtWidgets.QPushButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setObjectName("collapsibleHeader")
        
        self.content_area = QtWidgets.QWidget()
        self.content_area.setObjectName("collapsibleContent")
        self.content_layout = QtWidgets.QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(10, 5, 10, 10)
        self.content_layout.setSpacing(8)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.content_area)

        self.toggle_button.clicked.connect(self.toggle)
        self.set_expanded(expanded)

    def set_content_layout(self, layout):
        old_layout = self.content_area.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
            QtWidgets.QWidget().setLayout(old_layout)
        self.content_area.setLayout(layout)

    def toggle(self, checked):
        self.set_expanded(checked)

    def set_expanded(self, expanded):
        self.toggle_button.setChecked(expanded)
        self.content_area.setVisible(expanded)
        arrow = "▼" if expanded else "▶"
        self.toggle_button.setText(f"{arrow}  {self.title}")
