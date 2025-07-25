
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
    print("  -gui                 : GUIモードに切り替え（以後もGUIで起動）")
    print("  -cui                 : CUIモードに切り替え（以後もCUIで起動）")
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
        "launch_mode": "gui",
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
        self.launch_mode = config.get("launch_mode", "cui")

        self.crosshair_alpha = config.get("crosshair_alpha", 1.0)
        self.dot_alpha = config.get("dot_alpha", 1.0)



        self.disabled_keys = config["disabled_keys"]
        # 起動時に保存されたキーを無効化
        for k in self.disabled_keys:
            try:
                keyboard.block_key(k)
            except Exception as e:
                print(f"キー {k} の無効化に失敗: {e}")

    class KeyCaptureDialog(QtWidgets.QDialog):
        def __init__(self, parent=None, message="キーを押してください", allow_keys=None, cancel_callback=None, key_callback=None):
            super().__init__(parent)
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
            self.setWindowTitle("キー入力待機")
            self.setWindowModality(QtCore.Qt.ApplicationModal)
            self.setLayout(QtWidgets.QVBoxLayout())
            self.label = QtWidgets.QLabel(message)
            self.layout().addWidget(self.label)
            self.cancel_callback = cancel_callback
            self.key_callback = key_callback
            self.allow_keys = allow_keys

            cancel_button = QtWidgets.QPushButton("キャンセル")
            cancel_button.clicked.connect(self.cancel)
            self.layout().addWidget(cancel_button)
            self.resize(300, 100)

        def cancel(self):
            self.reject()
            if self.cancel_callback:
                self.cancel_callback()

        def keyPressEvent(self, event):
            # まず event.text() で取得を試みる
            key = event.text().lower()
            if not key:
                # 取得できなければ従来の方法へフォールバック
                key = QtGui.QKeySequence(event.key()).toString().lower()
            if key == "return":
                QtWidgets.QMessageBox.information(self, "無効化不可", "Enterキーは無効化できません。")
                return
            self.accept()
            if self.key_callback:
                self.key_callback(key)

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
            "launch_mode": self.launch_mode if hasattr(self, "launch_mode") else "cui"
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
            try:
                keyboard.unblock_key(key)
            except KeyError:
                pass  # すでにアンブロックされている場合は無視


    def enable_all_keys(self):
        for k in self.disabled_keys:
            keyboard.unblock_key(k)
        self.disabled_keys.clear()

    def show_control_panel(self):
        self.panel = QtWidgets.QWidget()
        self.panel.setWindowTitle("Crosshair Control Panel")
        layout = QtWidgets.QVBoxLayout()

        # クロスヘア表示切替
        self.crosshair_btn = QtWidgets.QPushButton("クロスヘア表示/非表示")
        self.crosshair_state = QtWidgets.QLabel("ON" if self.crosshair_visible else "OFF")
        self.crosshair_btn.clicked.connect(self.toggle_crosshair_button)
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(self.crosshair_btn)
        h1.addWidget(self.crosshair_state)
        layout.addLayout(h1)

        # ドット表示切替
        self.dot_btn = QtWidgets.QPushButton("ドット表示/非表示")
        self.dot_state = QtWidgets.QLabel("ON" if self.dot_visible else "OFF")
        self.dot_btn.clicked.connect(self.toggle_dot_button)
        h2 = QtWidgets.QHBoxLayout()
        h2.addWidget(self.dot_btn)
        h2.addWidget(self.dot_state)
        layout.addLayout(h2)

        # ドットサイズスライダー
        dotsize_layout = QtWidgets.QHBoxLayout()
        dotsize_label = QtWidgets.QLabel("ドットサイズ")
        self.dot_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.dot_slider.setMinimum(0)
        self.dot_slider.setMaximum(100)
        self.dot_slider.setValue(self.dot_radius * 2)
        self.dot_value = QtWidgets.QLabel(str(self.dot_radius * 2))
        self.dot_slider.valueChanged.connect(self.update_dot_size)
        dotsize_layout.addWidget(dotsize_label)
        dotsize_layout.addWidget(self.dot_slider)
        dotsize_layout.addWidget(self.dot_value)
        layout.addLayout(dotsize_layout)

        # カラー選択ヘルパー関数
        def make_color_button(label_text, getter, setter):
            layout_ = QtWidgets.QHBoxLayout()
            button = QtWidgets.QPushButton(label_text)
            square = QtWidgets.QLabel()
            square.setFixedSize(20, 20)
            square.setStyleSheet(f"background-color: {getter()}; border: 1px solid black;")
            def pick_color():
                color = QtWidgets.QColorDialog.getColor(QtGui.QColor(getter()))
                if color.isValid():
                    setter(color.name())
                    square.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
                    self.update()
                    save_config(self.get_config())
            button.clicked.connect(pick_color)
            layout_.addWidget(button)
            layout_.addWidget(square)
            return layout_

        layout.addLayout(make_color_button("クロスヘア色", lambda: self.crosshair_color, self.set_crosshair_color))
        layout.addLayout(make_color_button("ドット外枠色", lambda: self.dot_outer_color, self.set_dot_outer_color))
        layout.addLayout(make_color_button("ドット内側色", lambda: self.dot_inner_color, self.set_dot_inner_color))

        # クロスヘア透明度スライダー
        alpha_layout = QtWidgets.QHBoxLayout()
        alpha_label = QtWidgets.QLabel("クロスヘア透明度")
        self.alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.alpha_slider.setMinimum(0)
        self.alpha_slider.setMaximum(100)
        self.alpha_slider.setValue(int(self.crosshair_alpha * 100))
        self.alpha_value = QtWidgets.QLabel(str(self.crosshair_alpha))
        self.alpha_slider.valueChanged.connect(self.update_alpha)
        alpha_layout.addWidget(alpha_label)
        alpha_layout.addWidget(self.alpha_slider)
        alpha_layout.addWidget(self.alpha_value)
        layout.addLayout(alpha_layout)

        # ドット透明度スライダー
        dot_alpha_layout = QtWidgets.QHBoxLayout()
        dot_alpha_label = QtWidgets.QLabel("ドット透明度")
        self.dot_alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.dot_alpha_slider.setMinimum(0)
        self.dot_alpha_slider.setMaximum(100)
        self.dot_alpha_slider.setValue(int(self.dot_alpha * 100))
        self.dot_alpha_value = QtWidgets.QLabel(str(self.dot_alpha))
        self.dot_alpha_slider.valueChanged.connect(self.update_dot_alpha)
        dot_alpha_layout.addWidget(dot_alpha_label)
        dot_alpha_layout.addWidget(self.dot_alpha_slider)
        dot_alpha_layout.addWidget(self.dot_alpha_value)
        layout.addLayout(dot_alpha_layout)

        # キー無効化
        disable_layout = QtWidgets.QHBoxLayout()
        disable_btn = QtWidgets.QPushButton("キーを無効化")
        self.disabled_keys_label = QtWidgets.QLabel(", ".join(self.disabled_keys) if self.disabled_keys else "なし")
        disable_btn.clicked.connect(self.disable_key_gui)
        disable_layout.addWidget(disable_btn)
        disable_layout.addWidget(self.disabled_keys_label)
        layout.addLayout(disable_layout)

        # キー有効化
        enable_btn = QtWidgets.QPushButton("キーを有効化")
        enable_btn.clicked.connect(self.enable_key_gui)
        layout.addWidget(enable_btn)

        # すべて有効化
        enable_all_btn = QtWidgets.QPushButton("すべてのキーを有効化")
        enable_all_btn.clicked.connect(self.enable_all_keys_gui)
        layout.addWidget(enable_all_btn)

        # CUIモードへ切り替え
        cui_btn = QtWidgets.QPushButton("CUIモードに切り替え")
        cui_btn.clicked.connect(self.switch_to_cui)
        layout.addWidget(cui_btn)

        self.panel.setLayout(layout)
        self.panel.setGeometry(100, 100, 300, 100)
        self.panel.show()

    def toggle_crosshair_button(self):
        self.toggle_crosshair()
        self.crosshair_state.setText("ON" if self.crosshair_visible else "OFF")
        self.update()
        save_config(self.get_config())

    def toggle_dot_button(self):
        self.toggle_dot()
        self.dot_state.setText("ON" if self.dot_visible else "OFF")
        self.update()
        save_config(self.get_config())

    def update_dot_size(self, val):
        self.set_dot_size(val)
        self.dot_value.setText(str(val))
        self.update()
        save_config(self.get_config())    
        
    def update_alpha(self, val):
        alpha = round(val / 100, 2)
        self.crosshair_alpha = alpha
        self.alpha_value.setText(str(alpha))
        self.update()
        save_config(self.get_config())

    def update_dot_alpha(self, val):
        alpha = round(val / 100, 2)
        self.dot_alpha = alpha
        self.dot_alpha_value.setText(str(alpha))
        self.update()
        save_config(self.get_config())

    def set_crosshair_color(self, val):
        self.crosshair_color = val

    def set_dot_outer_color(self, val):
        self.dot_outer_color = val

    def set_dot_inner_color(self, val):
        self.dot_inner_color = val

    def disable_key_gui(self):
        def on_key_selected(key):
            self.disable_key(key)
            self.disabled_keys_label.setText(", ".join(self.disabled_keys))
            save_config(self.get_config())
            self.update()

        dlg = self.KeyCaptureDialog(
            self,
            message="無効化したいキーを押してください（Enterキーは無効化できません）",
            key_callback=on_key_selected
        )
        dlg.exec_()

    def capture_disable_key(self, msgbox):
        if self._disable_cancelled:
            return  # キャンセルされたら何もしない

        key = keyboard.read_key()
        msgbox.close()

        if key == "enter":
            QtWidgets.QMessageBox.information(None, "無効化失敗", "Enterキーは無効化できません。")
            return

        self.disable_key(key)
        self.disabled_keys_label.setText(", ".join(self.disabled_keys))
        save_config(self.get_config())
        self.update()

    def enable_key_gui(self):
        def on_key_selected(key):
            for k in self.disabled_keys:
                try:
                    keyboard.unblock_key(k)
                except:
                    pass

            for k in self.disabled_keys:
                if k != key:
                    try:
                        keyboard.block_key(k)
                    except:
                        pass

            self.enable_key(key)

            if key in self.disabled_keys:
                self.disabled_keys.remove(key)

            self.disabled_keys_label.setText(", ".join(self.disabled_keys) if self.disabled_keys else "なし")
            save_config(self.get_config())
            self.update()

        for k in self.disabled_keys:
            try:
               keyboard.unblock_key(k)
            except:
              pass

        dlg = self.KeyCaptureDialog(
            self,
            message="有効化したいキーを押してください（現在無効化中のキー: " + ", ".join(self.disabled_keys) + "）",
            key_callback=on_key_selected
        )
        dlg.exec_()

    def capture_enable_key(self, msgbox):
        if self._enable_cancelled:
            return  # キャンセルされたら何もしない

        # 一時的に無効化キーを解除してキーを取得
        for k in self.disabled_keys:
            try:
                keyboard.unblock_key(k)
            except KeyError:
                pass

        key = keyboard.read_key()

        # 再度無効化（除外キー以外）
        for k in self.disabled_keys:
            if k != key:
                try:
                    keyboard.block_key(k)
                except Exception:
                    pass

        msgbox.close()

        self.enable_key(key)
        self.disabled_keys_label.setText(", ".join(self.disabled_keys) if self.disabled_keys else "なし")
        save_config(self.get_config())
        self.update()

    def enable_all_keys_gui(self):
        self.enable_all_keys()
        self.disabled_keys_label.setText("なし")
        save_config(self.get_config())
        self.update()

    def switch_to_cui(self):
        config = load_config()
        config["launch_mode"] = "cui"
        save_config(config)
        QtWidgets.QMessageBox.information(None, "切り替え", "CUIモードに切り替えます。再起動します。")
        os.execv(sys.executable, [sys.executable] + sys.argv)


COMMANDS = {
    "-crosshair": "toggle_crosshair",
    "-dot": "toggle_dot",
    "--crosshair-color": "pick_crosshair_color",
    "--dot-out-color": "pick_dot_outer_color",
    "--dot-in-color": "pick_dot_inner_color",
    "--all-enable-keys": "enable_all_keys",
    "-gui": "enter_gui_mode",
    "-exit": "exit",
    "-help": "help",
    "--crosshair-alpha": "set_crosshair_alpha",
    "--dot-alpha": "set_dot_alpha",
    "launch_mode": "cui",
    "-gui": "switch_to_gui",
    "-cui": "switch_to_cui",
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
        elif raw == "-gui":
            config = load_config()
            config["launch_mode"] = "gui"
            save_config(config)
            print("GUIモードに切り替えます。再起動してください。")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        elif raw == "-cui":
            config = load_config()
            config["launch_mode"] = "cui"
            save_config(config)
            print("CUIモードに切り替えます。再起動してください。")
            os.execv(sys.executable, [sys.executable] + sys.argv)
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

    # 起動時のモードに応じてGUIパネルを自動表示
    config = load_config()
    if config.get("launch_mode") == "gui":
        overlay.show_control_panel()
    
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
            elif cmd == "enter_gui_mode":
                overlay.show_control_panel()
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
    config = load_config()
    if config.get("launch_mode") == "gui":
        gui_main()  # GUIモード → コントロールパネル＋オーバーレイのみ
    else:
        threading.Thread(target=input_thread, daemon=True).start()
        gui_main()  # CUIモード → オーバーレイ＋CUIプロンプト

