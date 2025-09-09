import os
import sys
import keyboard
from PyQt5 import QtCore, QtWidgets

from .. import ui

class OverlayUtilsMixin:
    def disable_key(self, key):
        if key == "enter": print("Enterキーは無効化できません。"); return
        if key not in self.disabled_keys: self.disabled_keys.append(key); keyboard.block_key(key)

    def enable_key(self, key):
        if key in self.disabled_keys:
            self.disabled_keys.remove(key)
            try: keyboard.unblock_key(key)
            except KeyError: pass

    def enable_all_keys(self):
        for k in self.disabled_keys:
            try: keyboard.unblock_key(k)
            except: pass
        self.disabled_keys.clear()

    def show_control_panel(self):
        self.panel = ui.ControlPanel(self)
        
        self.panel.monitor_selection_box.blockSignals(True)
        
        primary_screen_index = self.screens.index(QtWidgets.QApplication.primaryScreen())
        for i, screen in enumerate(self.screens):
            size = screen.size()
            item_text = f" モニター {i+1}: {size.width()}x{size.height()}"
            if i == primary_screen_index:
                item_text += " (プライマリ)"
            self.panel.monitor_selection_box.addItem(item_text)
        
        self.panel.monitor_selection_box.setCurrentIndex(self.selected_monitor_index)
        self.panel.monitor_selection_box.blockSignals(False)

        self.panel.show()

    @QtCore.pyqtSlot()
    def _update_ui_for_visibility_change(self):
        """GUIスレッドで実行されるスロット"""
        if hasattr(self, 'panel'):
            self.panel.update_master_toggle_button_ui()

    @QtCore.pyqtSlot(bool, bool)
    def set_master_enabled(self, enabled, manual_toggle=False):
        """オーバーレイの表示/非表示をスレッドセーフに切り替える"""
        if self.master_enabled == enabled and not manual_toggle:
            return
        self.master_enabled = enabled
        self.update() # オーバーレイ自体の再描画
        # UIの更新は master_visibility_changed シグナル経由で行う
        self.master_visibility_changed.emit()

        # ゲームモニターによってトリガーされ、ゲームが開始された場合はパネルを表示
        if enabled and not manual_toggle and hasattr(self, 'panel'):
            # GUIスレッドで実行するために、インボークするかシグナルを使うのがより安全
            QtCore.QMetaObject.invokeMethod(self.panel, "show", QtCore.Qt.QueuedConnection)
            QtCore.QMetaObject.invokeMethod(self.panel, "activateWindow", QtCore.Qt.QueuedConnection)

    def restart_application(self):
        """アプリケーションを再起動する"""
        self.clean_up()
        
        if hasattr(self, 'panel'):
            self.panel.close()

        try:
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            print(f"再起動に失敗しました: {e}")
            QtWidgets.QMessageBox.critical(self.panel, "再起動失敗", f"アプリケーションの再起動に失敗しました。\n{e}")
