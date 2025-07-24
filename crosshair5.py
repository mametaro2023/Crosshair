import sys
import threading
import queue
import json
import os
from PyQt5 import QtCore, QtGui, QtWidgets

CONFIG_FILE = "config.json"
command_queue = queue.Queue()

def load_config():
    defaults = {
        "crosshair_visible": True,
        "dot_visible": True,
        "dot_radius": 5,
        "crosshair_color": "#00FF66",
        "dot_outer_color": "#FFFFFF",
        "dot_inner_color": "#000000"
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            # 既存の設定に足りないキーを補完
            for key, value in defaults.items():
                config.setdefault(key, value)
            return config
        except Exception:
            pass
    return defaults

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("設定保存に失敗:", e)

class CrosshairOverlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.WindowTransparentForInput |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.showFullScreen()

        screen = QtWidgets.QApplication.primaryScreen().size()
        self.center_x = screen.width() // 2
        self.center_y = screen.height() // 2
        self.size = 20

        config = load_config()
        self.crosshair_visible = config["crosshair_visible"]
        self.dot_visible = config["dot_visible"]
        self.dot_radius = config["dot_radius"]
        self.crosshair_color = config["crosshair_color"]
        self.dot_outer_color = config["dot_outer_color"]
        self.dot_inner_color = config["dot_inner_color"]

    def toggle_crosshair(self):
        self.crosshair_visible = not self.crosshair_visible

    def toggle_dot(self):
        self.dot_visible = not self.dot_visible

    def set_dot_size(self, diameter):
        self.dot_radius = max(1, min(diameter, 100)) // 2

    def pick_crosshair_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.crosshair_color), self)
        if color.isValid():
            self.crosshair_color = color.name()

    def pick_dot_outer_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.dot_outer_color), self)
        if color.isValid():
            self.dot_outer_color = color.name()

    def pick_dot_inner_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.dot_inner_color), self)
        if color.isValid():
            self.dot_inner_color = color.name()

    def get_config(self):
        return {
            "crosshair_visible": self.crosshair_visible,
            "dot_visible": self.dot_visible,
            "dot_radius": self.dot_radius,
            "crosshair_color": self.crosshair_color,
            "dot_outer_color": self.dot_outer_color,
            "dot_inner_color": self.dot_inner_color
        }

    def print_parameters(self):
        print("=== 現在のパラメータ ===")
        print(f"  クロスヘア表示: {'ON' if self.crosshair_visible else 'OFF'}")
        print(f"  クロスヘア色 : {self.crosshair_color}")
        print(f"  ドット表示   : {'ON' if self.dot_visible else 'OFF'}")
        print(f"  ドット外枠色 : {self.dot_outer_color}")
        print(f"  ドット内側色 : {self.dot_inner_color}")
        print(f"  ドット直径   : {self.dot_radius * 2}")
        print("=====================")

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # クロスヘア
        if self.crosshair_visible:
            pen = QtGui.QPen(QtGui.QColor(self.crosshair_color), 2)
            painter.setPen(pen)
            gap = 10
            painter.drawLine(self.center_x - self.size, self.center_y,
                             self.center_x - gap, self.center_y)
            painter.drawLine(self.center_x + gap, self.center_y,
                             self.center_x + self.size, self.center_y)
            painter.drawLine(self.center_x, self.center_y - self.size,
                             self.center_x, self.center_y - gap)
            painter.drawLine(self.center_x, self.center_y + gap,
                             self.center_x, self.center_y + self.size)

        # ドット
        if self.dot_visible and self.dot_radius > 0:
            painter.setBrush(QtGui.QBrush(QtGui.QColor(self.dot_outer_color)))
            painter.setPen(QtGui.QPen(QtGui.QColor(self.dot_outer_color)))
            painter.drawEllipse(QtCore.QRect(
                self.center_x - self.dot_radius,
                self.center_y - self.dot_radius,
                self.dot_radius * 2,
                self.dot_radius * 2
            ))
            if self.dot_radius > 1:
                inner_r = self.dot_radius - 1
                painter.setBrush(QtGui.QBrush(QtGui.QColor(self.dot_inner_color)))
                painter.setPen(QtGui.QPen(QtGui.QColor(self.dot_inner_color)))
                painter.drawEllipse(QtCore.QRect(
                    self.center_x - inner_r,
                    self.center_y - inner_r,
                    inner_r * 2,
                    inner_r * 2
                ))

def input_thread():
    print("終了するにはウィンドウを閉じるか -exit を入力してください。")
    print("-help でコマンド一覧を表示できます。")
    while True:
        raw = input(">>> ").strip().lower()
        if raw == "-crosshair":
            command_queue.put(("toggle_crosshair", None))
        elif raw == "-dot":
            command_queue.put(("toggle_dot", None))
        elif raw.startswith("-dotsize"):
            parts = raw.split()
            if len(parts) == 2 and parts[1].isdigit():
                size = int(parts[1])
                command_queue.put(("set_dot_size", size))
            else:
                print("使用方法: -dotsize [0〜100]")
        elif raw == "--crosshair-color":
            command_queue.put(("pick_crosshair_color", None))
        elif raw == "--dot-out-color":
            command_queue.put(("pick_dot_outer_color", None))
        elif raw == "--dot-in-color":
            command_queue.put(("pick_dot_inner_color", None))
        elif raw == "-exit":
            command_queue.put(("exit", None))
            break
        elif raw == "-help":
            print("使用可能なコマンド一覧:")
            print("  -crosshair            : クロスヘア（十字）の表示/非表示を切り替え")
            print("  -dot                  : 中央のドットの表示/非表示を切り替え")
            print("  -dotsize [0〜100]     : 中央のドットの直径を指定ピクセルに変更")
            print("  --crosshair-color     : クロスヘアの色をカラーピッカーで変更")
            print("  --dot-out-color       : ドット外枠の色をカラーピッカーで変更")
            print("  --dot-in-color        : ドット内側の色をカラーピッカーで変更")
            print("  -exit                 : プログラムを終了")
            print("  -help                 : このヘルプを表示します")
        elif raw == "":
            continue
        else:
            print("不明なコマンドです。-help で確認してください。")

def gui_main():
    app = QtWidgets.QApplication(sys.argv)
    overlay = CrosshairOverlay()

    def poll_commands():
        while not command_queue.empty():
            cmd, val = command_queue.get()
            if cmd == "toggle_crosshair":
                overlay.toggle_crosshair()
            elif cmd == "toggle_dot":
                overlay.toggle_dot()
            elif cmd == "set_dot_size":
                overlay.set_dot_size(val)
            elif cmd == "pick_crosshair_color":
                overlay.pick_crosshair_color()
            elif cmd == "pick_dot_outer_color":
                overlay.pick_dot_outer_color()
            elif cmd == "pick_dot_inner_color":
                overlay.pick_dot_inner_color()
            elif cmd == "exit":
                save_config(overlay.get_config())
                app.quit()
                return
            overlay.print_parameters()
            overlay.update()
        QtCore.QTimer.singleShot(100, poll_commands)

    app.aboutToQuit.connect(lambda: save_config(overlay.get_config()))
    QtCore.QTimer.singleShot(100, poll_commands)
    overlay.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    threading.Thread(target=input_thread, daemon=True).start()
    gui_main()
