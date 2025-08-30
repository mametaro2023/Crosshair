import keyboard
from PyQt5 import QtCore, QtWidgets

class OverlayHotkeysMixin:
    def set_toggle_hotkey(self, new_hotkey):
        if new_hotkey == "半角/全角":
            QtWidgets.QMessageBox.information(self.panel, "設定不可", "「半角/全角」キーはホットキーとして設定できません。")
            return

        # 既存のホットキーをすべて解除
        if self.toggle_hotkey:
            try:
                keyboard.remove_hotkey(self.toggle_hotkey)
                # 半角/全角キーとの組み合わせも解除
                keyboard.remove_hotkey(f"{self.toggle_hotkey}+半角/全角")
            except (KeyError, AttributeError):
                pass
        self.toggle_hotkey = new_hotkey
        try:
            # 通常のホットキーを登録
            keyboard.add_hotkey(self.toggle_hotkey, self.toggle_master_visibility)
            # 半角/全角キーとの組み合わせも登録
            keyboard.add_hotkey(f"{self.toggle_hotkey}+半角/全角", self.toggle_master_visibility)
            print(f"オーバーレイ表示切替ホットキーを '{self.toggle_hotkey}' に設定しました。")
        except Exception as e:
            print(f"ホットキー '{self.toggle_hotkey}' の登録に失敗: {e}")

    def unregister_toggle_hotkey(self):
        """ホットキーを一時的に登録解除する"""
        if self.toggle_hotkey:
            try:
                keyboard.remove_hotkey(self.toggle_hotkey)
                keyboard.remove_hotkey(f"{self.toggle_hotkey}+半角/全角")
                print(f"ホットキー '{self.toggle_hotkey}' を一時的に無効化しました。")
            except KeyError:
                pass # すでに解除されている場合は何もしない

    def register_toggle_hotkey(self):
        """ホットキーを再度登録する"""
        if self.toggle_hotkey:
            try:
                keyboard.add_hotkey(self.toggle_hotkey, self.toggle_master_visibility)
                keyboard.add_hotkey(f"{self.toggle_hotkey}+半角/全角", self.toggle_master_visibility)
                print(f"ホットキー '{self.toggle_hotkey}' を再度有効化しました。")
            except (ValueError, KeyError): # すでに登録されている場合がある
                pass
            except Exception as e:
                print(f"ホットキー '{self.toggle_hotkey}' の再登録に失敗: {e}")

    def toggle_master_visibility(self):
        """ホットキーまたはボタンから呼び出される"""
        self.master_enabled = not self.master_enabled
        self.update() # オーバーレイ自体の再描画 (これはスレッドセーフ)
        self.master_visibility_changed.emit() # UI更新のためにシグナルを発行
