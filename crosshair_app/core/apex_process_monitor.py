import psutil
import time
import threading
from PyQt5 import QtCore

class ApexProcessMonitor(QtCore.QObject):
    apex_status_changed = QtCore.pyqtSignal(bool) # True if Apex is running, False otherwise

    def __init__(self, apex_tracker, parent=None):
        super().__init__(parent)
        self.apex_tracker = apex_tracker
        self._is_monitoring = False
        self._auto_tracking_enabled = False
        self._apex_is_running = False
        self._auto_started_tracking = False # New flag
        self._monitor_thread = None

    def set_auto_tracking_enabled(self, enabled: bool):
        self._auto_tracking_enabled = enabled
        if enabled:
            # When auto-tracking is enabled, immediately check Apex status
            self._check_apex_status_and_act()
        else:
            # If auto-tracking is disabled, stop tracking ONLY if it was started by auto-tracking
            if self._auto_started_tracking:
                print("Auto-tracking disabled. Stopping auto-started tracking.")
                self.apex_tracker.stop_tracking()
                self._auto_started_tracking = False # Reset the flag

    def start_monitoring(self):
        if self._is_monitoring:
            return
        self._is_monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        self._is_monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1) # Wait for the thread to finish

    def _monitor_loop(self):
        while self._is_monitoring:
            self._check_apex_status_and_act()
            time.sleep(5) # Check every 5 seconds

    def _check_apex_status_and_act(self):
        current_apex_status = self._is_apex_running()
        if current_apex_status != self._apex_is_running:
            self._apex_is_running = current_apex_status
            self.apex_status_changed.emit(self._apex_is_running)
            print(f"Apex status changed: {'Running' if self._apex_is_running else 'Not Running'}")

            if self._auto_tracking_enabled:
                if self._apex_is_running:
                    if not self.apex_tracker._is_running: # Only start if not already running
                        print("Apex is running and auto-tracking is enabled. Starting tracking...")
                        self.apex_tracker.start_tracking()
                        self._auto_started_tracking = True
                else:
                    if self._auto_started_tracking: # Only stop if auto-started
                        print("Apex is not running and auto-tracking is enabled. Stopping auto-started tracking...")
                        self.apex_tracker.stop_tracking()
                        self._auto_started_tracking = False
        elif self._auto_tracking_enabled and self._apex_is_running and not self.apex_tracker._is_running:
            # This handles the case where auto-tracking is enabled while Apex is already running
            # and tracking hasn't started yet (e.g., on app startup)
            print("Apex is running, auto-tracking is enabled, but tracking is not active. Starting tracking...")
            self.apex_tracker.start_tracking()
            self._auto_started_tracking = True


    def _is_apex_running(self) -> bool:
        for process in psutil.process_iter(['name']):
            if process.info['name'] == 'r5apex.exe':
                return True
        return False
