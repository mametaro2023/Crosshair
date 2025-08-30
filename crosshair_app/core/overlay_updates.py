import threading
from PyQt5 import QtCore, QtWidgets

from .. import dialogs
from .. import utils

class OverlayUpdatesMixin:
    @QtCore.pyqtSlot(dict)
    def show_update_dialog(self, update_info):
        if hasattr(self, 'panel'):
            dialog = dialogs.UpdateDialog(self.panel, update_info)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                self.start_update_process(update_info['download_url'])
        else:
            print("コントロールパネルが初期化されていません。")

    def start_update_process(self, download_url):
        self.progress_dialog = dialogs.ProgressDialog(self.panel)
        self.progress_dialog.show()

        self.download_thread = threading.Thread(target=self.download_worker, args=(download_url,), daemon=True)
        self.download_thread.start()

    @QtCore.pyqtSlot(int)
    def update_progress_dialog(self, value):
        if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():
            self.progress_dialog.update_progress(value)

    def download_worker(self, url):
        def progress_callback(progress):
            self.download_progress.emit(progress)

        downloaded_path = utils.download_asset_with_progress(url, progress_callback)
        
        if downloaded_path:
            # ダウンロード成功
            QtCore.QMetaObject.invokeMethod(self.progress_dialog, "update_progress", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(int, 100))
            QtCore.QMetaObject.invokeMethod(self.progress_dialog, "close", QtCore.Qt.QueuedConnection)
            
            # ZIPを展開し、新しい実行ファイルのパスを取得
            new_exe_in_temp_path = utils.extract_and_find_exe(downloaded_path)

            if new_exe_in_temp_path:
                current_exe_path = utils.get_executable_path()
                updater_script = utils.create_updater_script(downloaded_path, current_exe_path, new_exe_in_temp_path)
                
                if updater_script:
                    utils.run_updater_and_exit(updater_script)
                else:
                    print("アップデーターの作成に失敗しました。")
                    QtWidgets.QMessageBox.critical(self.panel, "アップデートエラー", "アップデーターの作成に失敗しました。")
            else:
                print("ZIPファイルから実行ファイルが見つかりませんでした。")
                QtWidgets.QMessageBox.critical(self.panel, "アップデートエラー", "ZIPファイルから実行ファイルが見つかりませんでした。")
        else:
            # ダウンロード失敗
            QtCore.QMetaObject.invokeMethod(self.progress_dialog, "close", QtCore.Qt.QueuedConnection)
            print("ダウンロードに失敗しました。")
            QtWidgets.QMessageBox.critical(self.panel, "アップデートエラー", "ダウンロードに失敗しました。")
