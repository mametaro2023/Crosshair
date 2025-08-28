from PyQt5 import QtCore, QtWidgets
import keyboard

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, preset_folder_path=""):
        super().__init__(parent)
        self.setWindowTitle("環境設定")
        self.setLayout(QtWidgets.QVBoxLayout())

        path_layout = QtWidgets.QHBoxLayout()
        self.path_label = QtWidgets.QLabel(preset_folder_path)
        self.browse_btn = QtWidgets.QPushButton("参照")
        self.browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.browse_btn)

        self.layout().addLayout(path_layout)

        close_btn = QtWidgets.QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        self.layout().addWidget(close_btn)

    def browse_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "フォルダを選択", self.path_label.text())
        if folder:
            self.path_label.setText(folder)

    def get_selected_path(self):
        return self.path_label.text()

class KeyCaptureDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, message="キーを押してください", key_callback=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("キー入力待機")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setLayout(QtWidgets.QVBoxLayout())
        
        self.label = QtWidgets.QLabel(message)
        self.layout().addWidget(self.label)
        
        self.key_callback = key_callback
        self.captured_key = None
        self.hook = None

        cancel_button = QtWidgets.QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        self.layout().addWidget(cancel_button)
        self.resize(300, 100)

    def _on_key_press(self, event):
        key = event.name
        
        if key == "enter":
            QtCore.QMetaObject.invokeMethod(self, "_show_enter_error", QtCore.Qt.QueuedConnection)
            return

        self.captured_key = key
        QtCore.QMetaObject.invokeMethod(self, "accept", QtCore.Qt.QueuedConnection)
        return True

    @QtCore.pyqtSlot()
    def _show_enter_error(self):
        QtWidgets.QMessageBox.information(self, "無効化不可", "Enterキーは無効化できません。")

    def exec_(self):
        self.hook = keyboard.on_press(self._on_key_press, suppress=True)
        result = super().exec_()
        keyboard.unhook(self.hook)
        if result == QtWidgets.QDialog.Accepted and self.key_callback and self.captured_key:
            self.key_callback(self.captured_key)
        return result

class ProgressDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("アップデート中...")
        self.setFixedSize(300, 100)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel("ダウンロード中...")
        layout.addWidget(self.label)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

    @QtCore.pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.label.setText(f"ダウンロード中... {value}%")
        if value == 100:
            self.label.setText("ダウンロード完了。アップデートを準備中...")

class UpdateDialog(QtWidgets.QDialog):
    def __init__(self, parent, update_info):
        super().__init__(parent)
        self.setWindowTitle("新しいバージョンが利用可能です")
        self.setMinimumWidth(400)

        layout = QtWidgets.QVBoxLayout(self)

        title_label = QtWidgets.QLabel(f" {update_info['latest_version']} が利用可能です。")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title_label)

        layout.addWidget(QtWidgets.QLabel("リリースノート:"))
        
        notes_text = QtWidgets.QTextEdit()
        notes_text.setHtml(update_info['release_notes'].replace('\n', '<br>'))
        notes_text.setReadOnly(True)
        layout.addWidget(notes_text)

        button_box = QtWidgets.QDialogButtonBox()
        update_button = button_box.addButton("今すぐアップデート", QtWidgets.QDialogButtonBox.AcceptRole)
        later_button = button_box.addButton("後で", QtWidgets.QDialogButtonBox.RejectRole)
        
        layout.addWidget(button_box)

        update_button.clicked.connect(self.accept)
        later_button.clicked.connect(self.reject)


def show_update_dialog(parent, update_info):
    """アップデート通知ダイアログを表示する"""
    if parent and update_info:
        dialog = UpdateDialog(parent, update_info)
        return dialog.exec_() == QtWidgets.QDialog.Accepted
    return False