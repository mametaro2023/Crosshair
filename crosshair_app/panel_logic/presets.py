
import os
import json
from PyQt5 import QtWidgets
from .. import config

def load_presets(self):
    self.preset_box.blockSignals(True)
    self.preset_box.clear() 
    self.preset_box.addItem(self.overlay.UNSAVED_PRESET_TEXT)
    self.preset_box.addItem("デフォルト設定")
    self.overlay.presets = {"デフォルト設定": self.overlay.default_config}
    for file in os.listdir(self.overlay.overall_preset_folder):
        if file.endswith(config.PRESET_EXTENSION):
            name = os.path.splitext(file)[0]
            path = os.path.join(self.overlay.overall_preset_folder, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.overlay.presets[name] = data
                self.preset_box.addItem(name)
            except Exception as e:
                print(f"プリセット読み込み失敗: {file}: {e}")
    if self.overlay.is_dirty:
        self.preset_box.setCurrentIndex(0)
    elif self.overlay.last_selected_preset in self.overlay.presets:
        index = self.preset_box.findText(self.overlay.last_selected_preset)
        self.preset_box.setCurrentIndex(index)
    else:
        self.preset_box.setCurrentIndex(0)
    self.preset_box.blockSignals(False)

def save_preset(self):
    path, _ = QtWidgets.QFileDialog.getSaveFileName(
        self, "プリセットを保存", self.overlay.overall_preset_folder,
        f"プリセットファイル (*{config.PRESET_EXTENSION})")
    if path:
        if not path.endswith(config.PRESET_EXTENSION):
            path += config.PRESET_EXTENSION
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.overlay.get_config(), f, indent=4)
            self.overlay.last_selected_preset = os.path.splitext(os.path.basename(path))[0]
            self.overlay.save_global_config()
            self.load_presets()
            self.overlay.is_dirty = False
            return True
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "保存失敗", str(e))
    return False

def load_selected_preset(self):
    name = self.preset_box.currentText()
    if name == self.overlay.UNSAVED_PRESET_TEXT:
        return
    config_to_load = self.overlay.presets.get(name, self.overlay.default_config)
    self.overlay.apply_config(config_to_load)
    self.overlay.last_selected_preset = name
    self.overlay.save_global_config()
    print(f"プリセット {name} を読み込みました")
    self.update_control_panel_ui()
    self.overlay.update()
    self.overlay.is_dirty = False
