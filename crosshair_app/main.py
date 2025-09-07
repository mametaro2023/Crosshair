import sys
import threading
import time
import keyboard
from PyQt5 import QtCore, QtGui, QtWidgets

# For single instance check
if sys.platform == "win32":
    try:
        from win32event import CreateMutex  # type: ignore
        from win32api import GetLastError  # type: ignore
        from winerror import ERROR_ALREADY_EXISTS  # type: ignore
    except ImportError:
        # pywin32 is not installed, single instance check will be skipped.
        CreateMutex = None 
else:
    CreateMutex = None

from . import theme
from . import config
from . import utils

# Import the new mixins
from .core.overlay_base import CrosshairOverlayBase
from .core.overlay_drawing import OverlayDrawingMixin
from .core.overlay_hotkeys import OverlayHotkeysMixin
from .core.overlay_updates import OverlayUpdatesMixin
from .core.overlay_utils import OverlayUtilsMixin

class SingleInstance: 
    def __init__(self, name):
        self.mutex = None
        self.mutex_name = name
        if CreateMutex:
            self.mutex = CreateMutex(None, 1, self.mutex_name)
            self.already_running = (GetLastError() == ERROR_ALREADY_EXISTS)
        else:
            self.already_running = False

    def is_running(self):
        return self.already_running

class CrosshairOverlay(
    CrosshairOverlayBase,
    OverlayDrawingMixin,
    OverlayHotkeysMixin,
    OverlayUpdatesMixin,
    OverlayUtilsMixin
):
    def __init__(self, screens):
        super().__init__(screens) # Call the __init__ of CrosshairOverlayBase

        # Initialize hotkeys after base is initialized
        loaded_config = config.load_config()
        loaded_toggle_hotkey = loaded_config.get("toggle_hotkey", "ctrl+f1")
        self.set_toggle_hotkey(loaded_toggle_hotkey)

        # Initialize disabled keys after base is initialized
        for k in self.disabled_keys:
            try: keyboard.block_key(k)
            except Exception as e: print(f"キー {k} の無効化に失敗: {e}")

        # Connect signals after all mixins are initialized
        self.update_check_done.connect(self.show_update_dialog)
        self.download_progress.connect(self.update_progress_dialog)
        self.master_visibility_changed.connect(self._update_ui_for_visibility_change)

    def clean_up(self):
        super().clean_up() # Call clean_up from CrosshairOverlayBase
        self.enable_all_keys() # From OverlayUtilsMixin
        if self.toggle_hotkey: # From OverlayHotkeysMixin
            try:
                keyboard.remove_hotkey(self.toggle_hotkey)
            except (KeyError, AttributeError):
                pass

def check_updates_thread(overlay):
    """バックグラウンドでアップデートを確認するスレッド"""
    time.sleep(2) 
    print("アップデートを確認しています...")
    update_info = utils.check_for_updates(config.APP_VERSION)
    if update_info:
        print(f"新しいバージョンが見つかりました: {update_info['latest_version']}")
        overlay.update_check_done.emit(update_info)
    else:
        print("新しいバージョンは見つかりませんでした。")

def gui_main():
    # --- Single Instance Check ---
    instance = SingleInstance("CrosshairApp-mametaro-GlobalMutex-2023")
    if instance.is_running():
        # Create a temporary app to show a message box
        temp_app = QtWidgets.QApplication.instance() # Check if an instance already exists
        if temp_app is None: # If not, create one
            temp_app = QtWidgets.QApplication(sys.argv)
        
        error_box = QtWidgets.QMessageBox()
        error_box.setIcon(QtWidgets.QMessageBox.Warning)
        error_box.setText("Crosshairはすでに実行中です。")
        error_box.setWindowTitle("多重起動エラー")
        error_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        error_box.exec_()
        sys.exit(0)

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    theme.apply_modern_dark_theme(app)
    
    screens = app.screens()
    overlay = CrosshairOverlay(screens)
    
    target_index = overlay.selected_monitor_index
    if 0 <= target_index < len(screens):
        target_screen = screens[target_index]
        overlay.setGeometry(target_screen.geometry())
        overlay.showFullScreen()
    else:
        overlay.showFullScreen()

    overlay.show_control_panel()

    update_thread = threading.Thread(target=check_updates_thread, args=(overlay,), daemon=True)
    update_thread.start()

    app.aboutToQuit.connect(overlay.clean_up)
    sys.exit(app.exec_())

if __name__ == "__main__":
    gui_main()
