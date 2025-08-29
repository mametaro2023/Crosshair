from PyQt5 import QtCore, QtWidgets
import keyboard
import threading

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, overall_folder="", shape_folder=""):
        super().__init__(parent)
        self.setWindowTitle("環境設定")
        layout = QtWidgets.QVBoxLayout(self)

        # 全体プリセットフォルダ
        overall_group = QtWidgets.QGroupBox("全体プリセットの保存先")
        overall_layout = QtWidgets.QHBoxLayout(overall_group)
        self.overall_path_label = QtWidgets.QLabel(overall_folder)
        overall_browse_btn = QtWidgets.QPushButton("参照")
        overall_browse_btn.clicked.connect(lambda: self.browse_folder(self.overall_path_label))
        overall_layout.addWidget(self.overall_path_label)
        overall_layout.addWidget(overall_browse_btn)
        layout.addWidget(overall_group)

        # 形状プリセットフォルダ
        shape_group = QtWidgets.QGroupBox("形状プリセット (.crshr) の保存先")
        shape_layout = QtWidgets.QHBoxLayout(shape_group)
        self.shape_path_label = QtWidgets.QLabel(shape_folder)
        shape_browse_btn = QtWidgets.QPushButton("参照")
        shape_browse_btn.clicked.connect(lambda: self.browse_folder(self.shape_path_label))
        shape_layout.addWidget(self.shape_path_label)
        shape_layout.addWidget(shape_browse_btn)
        layout.addWidget(shape_group)

        # 閉じるボタン
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def browse_folder(self, label_to_update):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "フォルダを選択", label_to_update.text())
        if folder:
            label_to_update.setText(folder)

    def get_selected_paths(self):
        return self.overall_path_label.text(), self.shape_path_label.text()

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

        cancel_button = QtWidgets.QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        self.layout().addWidget(cancel_button)
        self.resize(300, 100)

    def _capture_hotkey_thread(self):
        # read_hotkeyは修飾キーを含むキーの組み合わせを文字列として返す
        # suppress=Falseにすることで、他のアプリケーションへのキー入力を妨げない
        hotkey = keyboard.read_hotkey(suppress=False)
        
        if hotkey == "enter":
            QtCore.QMetaObject.invokeMethod(self, "_show_enter_error", QtCore.Qt.QueuedConnection)
            # エラー表示後も入力を待機し続ける
            self._capture_hotkey_thread()
            return
        
        if hotkey == "半角/全角":
            QtCore.QMetaObject.invokeMethod(self, "_show_ime_key_error", QtCore.Qt.QueuedConnection)
            self._capture_hotkey_thread()
            return

        self.captured_key = hotkey
        QtCore.QMetaObject.invokeMethod(self, "accept", QtCore.Qt.QueuedConnection)

    @QtCore.pyqtSlot()
    def _show_enter_error(self):
        QtWidgets.QMessageBox.information(self, "設定不可", "Enterキーはショートカットキーとして設定できません。")

    @QtCore.pyqtSlot()
    def _show_ime_key_error(self):
        QtWidgets.QMessageBox.information(self, "設定不可", "「半角/全角」キーはショートカットキーとして設定できません。")

    def exec_(self):
        # バックグラウンドスレッドでキー入力を待機
        capture_thread = threading.Thread(target=self._capture_hotkey_thread, daemon=True)
        capture_thread.start()
        
        result = super().exec_()
        
        # ダイアログが正常に閉じられた場合、コールバックを呼び出す
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