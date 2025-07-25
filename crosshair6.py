
import sys
import threading
import queue
import json
import os
import keyboard
from PyQt5 import QtCore, QtGui, QtWidgets

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".crosshair_config.json")
command_queue = queue.Queue()
overlay = None


def print_help():
    print("使用可能なコマンド一覧:")
    print("  -crosshair            : クロスヘア（十字）の表示/非表示を切り替え")
    print("  -dot                  : 中央のドットの表示/非表示を切り替え")
    print("  -dotsize [0〜100]     : 中央のドットの直径を指定ピクセルに変更")
    print("  --crosshair-color     : クロスヘアの色をカラーピッカーで変更")
    print("  --dot-out-color       : ドット外枠の色をカラーピッカーで変更")
    print("  --dot-in-color        : ドット内側の色をカラーピッカーで変更")
    print("  --crosshair-alpha [0.0〜1.0] : クロスヘアの透明度を変更")
    print("  --dot-alpha [0.0〜1.0]       : ドットの透明度を変更（外枠・内側共通）")
    print("  --disable-key         : 指定したキーを無効化する")
    print("  --multiple-disable-keys : 複数のキーをまとめて無効化する（Enterキーで確定）")
    print("  --enable-key          : 無効化されたキーを1つ有効化する")
    print("  --all-enable-keys     : 無効化されたキーを全て有効化する")
    print("  -exit                 : プログラムを終了")
    print("  -help                 : このヘルプを表示します")

def load_config():
    defaults = {
        "crosshair_visible": True,
        "dot_visible": True,
        "dot_radius": 5,
        "crosshair_color": "#00FF66",
        "dot_outer_color": "#FFFFFF",
        "dot_inner_color": "#000000",
        "disabled_keys": [],  # 追加
        "crosshair_alpha": 1.0,
        "dot_alpha": 1.0,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
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

        self.crosshair_alpha = config.get("crosshair_alpha", 1.0)
        self.dot_alpha = config.get("dot_alpha", 1.0)

        self.disabled_keys = config["disabled_keys"]
        # 起動時に保存されたキーを無効化
        for k in self.disabled_keys:
            try:
                keyboard.block_key(k)
            except Exception as e:
                print(f"キー {k} の無効化に失敗: {e}")


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
            "dot_inner_color": self.dot_inner_color,
            "disabled_keys": self.disabled_keys,
            "crosshair_alpha": self.crosshair_alpha,
            "dot_alpha": self.dot_alpha,
        }

    def print_parameters(self):
        print("=== 現在のパラメータ ===")
        print(f"  クロスヘア表示: {'ON' if self.crosshair_visible else 'OFF'}")
        print(f"  クロスヘア色 : {self.crosshair_color}")
        print(f"  ドット表示   : {'ON' if self.dot_visible else 'OFF'}")
        print(f"  ドット外枠色 : {self.dot_outer_color}")
        print(f"  ドット内側色 : {self.dot_inner_color}")
        print(f"  ドット直径   : {self.dot_radius * 2}")
        print(f"  クロスヘア透明度: {self.crosshair_alpha}")
        print(f"  ドット透明度   : {self.dot_alpha}")
        print(f"  無効化キー   : {', '.join(self.disabled_keys) if self.disabled_keys else 'なし'}")
        print("=====================")

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # クロスヘア
        if self.crosshair_visible:
            color = QtGui.QColor(self.crosshair_color)
            color.setAlphaF(self.crosshair_alpha)
            pen = QtGui.QPen(color, 2)
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
            outer_color = QtGui.QColor(self.dot_outer_color)
            outer_color.setAlphaF(self.dot_alpha)
            painter.setBrush(QtGui.QBrush(outer_color))
            painter.setPen(QtGui.QPen(outer_color))
            painter.drawEllipse(QtCore.QRect(
                self.center_x - self.dot_radius,
                self.center_y - self.dot_radius,
                self.dot_radius * 2,
                self.dot_radius * 2
            ))
            if self.dot_radius > 1:
                inner_r = self.dot_radius - 1
                inner_color = QtGui.QColor(self.dot_inner_color)
                inner_color.setAlphaF(self.dot_alpha)
                painter.setBrush(QtGui.QBrush(inner_color))
                painter.setPen(QtGui.QPen(inner_color))
                painter.drawEllipse(QtCore.QRect(
                    self.center_x - inner_r,
                    self.center_y - inner_r,
                    inner_r * 2,
                    inner_r * 2
                ))

    
    def disable_key(self, key):
        if key == "enter":
            print("Enterキーは無効化できません。")
            return
        if key not in self.disabled_keys:
            self.disabled_keys.append(key)
            keyboard.block_key(key)

    def enable_key(self, key):
        if key in self.disabled_keys:
            self.disabled_keys.remove(key)
            keyboard.unblock_key(key)

    def enable_all_keys(self):
        for k in self.disabled_keys:
            keyboard.unblock_key(k)
        self.disabled_keys.clear()

COMMANDS = {
    "-crosshair": "toggle_crosshair",
    "-dot": "toggle_dot",
    "--crosshair-color": "pick_crosshair_color",
    "--dot-out-color": "pick_dot_outer_color",
    "--dot-in-color": "pick_dot_inner_color",
    "--all-enable-keys": "enable_all_keys",
    "-exit": "exit",
    "-help": "help",
    "--crosshair-alpha": "set_crosshair_alpha",
    "--dot-alpha": "set_dot_alpha",
}

def clear_keyboard_buffer():
    try:
        # バッファに残っているイベントを全て読み捨てる
        while True:
            event = keyboard.read_event(suppress=False)
            # ここに到達するとイベントを消費する
            if event.event_type == keyboard.KEY_UP:
                # 何も押されていないときはbreak
                break
    except:
        # イベントが無い場合や例外発生時は終了
        pass

def input_thread():
    print("終了するにはウィンドウを閉じるか -exit を入力してください。")
    print("-help でコマンド一覧を表示できます。")
    while True:
        raw = input(">>> ").strip().lower()
        if raw.startswith("-dotsize"):
            parts = raw.split()
            if len(parts) == 2 and parts[1].isdigit():
                command_queue.put(("set_dot_size", int(parts[1])))
            else:
                print("使用方法: -dotsize [0〜100]")
        elif raw == "--disable-key":
            print("どのキーを無効化しますか？キーを押してください。")
            clear_keyboard_buffer()
            key = keyboard.read_key()
            if key == "enter":
                print("Enterキーは無効化できません。")
            else:
                command_queue.put(("disable_key", key))
                print(f"キー {key} を無効化しました。")
        elif raw == "--multiple-disable-keys":
            print("無効化したいキーをすべて押し、最後にEnterを押してください。")
            keys = []
            clear_keyboard_buffer()
            while True:
                k = keyboard.read_event(suppress=False)
                if k.event_type == keyboard.KEY_DOWN:
                    if k.name == "enter":
                        break
                    if k.name not in keys:
                        keys.append(k.name)
            for k in keys:
                command_queue.put(("disable_key", k))
            print(f"キー {', '.join(keys)} を無効化しました。")
        elif raw == "--enable-key":
            print(f"無効化されているキー: {', '.join(overlay.disabled_keys) if overlay.disabled_keys else 'なし'}")
            print("有効化したいキーを押してください。")
            clear_keyboard_buffer()
            key = keyboard.read_key()
            command_queue.put(("enable_key", key))
            print(f"キー {key} を有効化しました。")
        elif raw.startswith("--crosshair-alpha"):
            parts = raw.split()
            if len(parts) == 2:
                try:
                    alpha = float(parts[1])
                    command_queue.put(("set_crosshair_alpha", alpha))
                except ValueError:
                    print("使用方法: --crosshair-alpha [0.0〜1.0]")
            else:
                print("使用方法: --crosshair-alpha [0.0〜1.0]")

        elif raw.startswith("--dot-alpha"):
            parts = raw.split()
            if len(parts) == 2:
                try:
                    alpha = float(parts[1])
                    command_queue.put(("set_dot_alpha", alpha))
                except ValueError:
                    print("使用方法: --dot-alpha [0.0〜1.0]")
            else:
                print("使用方法: --dot-alpha [0.0〜1.0]")
        elif raw in COMMANDS:
            if raw == "-exit":
                if overlay:
                    save_config(overlay.get_config())
                    overlay.enable_all_keys()
                command_queue.put(("exit", None))
                break
            elif raw == "-help":
                print_help()
            else:
                command_queue.put((COMMANDS[raw], None))
        elif raw == "":
            continue
        else:
            print("不明なコマンドです。-help で確認してください。")



def gui_main():
    global overlay
    app = QtWidgets.QApplication(sys.argv)
    overlay = CrosshairOverlay()
    
     # 起動時にパラメータとヘルプを表示
    overlay.print_parameters()
    print_help()

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
            elif cmd == "disable_key":
                overlay.disable_key(val)
            elif cmd == "enable_key":
                overlay.enable_key(val)
            elif cmd == "enable_all_keys":
                overlay.enable_all_keys()
            elif cmd == "set_crosshair_alpha":
                overlay.crosshair_alpha = max(0.0, min(val, 1.0))
            elif cmd == "set_dot_alpha":
                overlay.dot_alpha = max(0.0, min(val, 1.0))
            elif cmd == "exit":
                app.quit()
                return
            overlay.print_parameters()
            save_config(overlay.get_config())
            overlay.update()
        QtCore.QTimer.singleShot(100, poll_commands)

    app.aboutToQuit.connect(lambda: [
    save_config(overlay.get_config()),
    overlay.enable_all_keys()  # 終了時に解除
    ])
    QtCore.QTimer.singleShot(100, poll_commands)
    overlay.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    threading.Thread(target=input_thread, daemon=True).start()
    gui_main()
