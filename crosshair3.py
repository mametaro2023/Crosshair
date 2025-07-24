import sys
import threading
import queue
from PyQt5 import QtCore, QtGui, QtWidgets

command_queue = queue.Queue()

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
        self.dot_radius = 5

        self.crosshair_visible = True
        self.dot_visible = True

    def toggle_crosshair(self):
        self.crosshair_visible = not self.crosshair_visible

    def toggle_dot(self):
        self.dot_visible = not self.dot_visible

    def set_dot_size(self, diameter):
        self.dot_radius = max(1, min(diameter, 100)) // 2

    def print_parameters(self):
        print("=== 現在のパラメータ ===")
        print(f"  クロスヘア表示: {'ON' if self.crosshair_visible else 'OFF'}")
        print(f"  ドット表示   : {'ON' if self.dot_visible else 'OFF'}")
        print(f"  ドット直径   : {self.dot_radius * 2}")
        print("=====================")

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # クロスヘア
        if self.crosshair_visible:
            pen = QtGui.QPen(QtGui.QColor("#00FF66"), 2)
            painter.setPen(pen)
            gap = 10
            # 左右
            painter.drawLine(self.center_x - self.size, self.center_y,
                             self.center_x - gap, self.center_y)
            painter.drawLine(self.center_x + gap, self.center_y,
                             self.center_x + self.size, self.center_y)
            # 上下
            painter.drawLine(self.center_x, self.center_y - self.size,
                             self.center_x, self.center_y - gap)
            painter.drawLine(self.center_x, self.center_y + gap,
                             self.center_x, self.center_y + self.size)

        # ドット (外周1px白, 内側黒)
        if self.dot_visible and self.dot_radius > 0:
            # 外側の白い円
            painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
            painter.setPen(QtGui.QPen(QtCore.Qt.white))
            painter.drawEllipse(QtCore.QRect(
                self.center_x - self.dot_radius,
                self.center_y - self.dot_radius,
                self.dot_radius * 2,
                self.dot_radius * 2
            ))
            # 内側の黒い円（白枠の1px内側）
            if self.dot_radius > 1:
                inner_r = self.dot_radius - 1
                painter.setBrush(QtGui.QBrush(QtCore.Qt.black))
                painter.setPen(QtGui.QPen(QtCore.Qt.black))
                painter.drawEllipse(QtCore.QRect(
                    self.center_x - inner_r,
                    self.center_y - inner_r,
                    inner_r * 2,
                    inner_r * 2
                ))

def input_thread():
    print("終了するにはウィンドウを閉じてください。")
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
        elif raw == "-help":
            print("使用可能なコマンド一覧:")
            print("  -crosshair          : クロスヘア（緑色の十字）の表示/非表示を切り替え")
            print("  -dot                : 中央のドットの表示/非表示を切り替え")
            print("  -dotsize [0〜100]   : 中央のドットの直径を指定ピクセルに変更")
            print("  -help               : このヘルプを表示します")
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
                overlay.print_parameters()
            elif cmd == "toggle_dot":
                overlay.toggle_dot()
                overlay.print_parameters()
            elif cmd == "set_dot_size":
                overlay.set_dot_size(val)
                overlay.print_parameters()
            overlay.update()
        QtCore.QTimer.singleShot(100, poll_commands)

    QtCore.QTimer.singleShot(100, poll_commands)
    overlay.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    threading.Thread(target=input_thread, daemon=True).start()
    gui_main()
