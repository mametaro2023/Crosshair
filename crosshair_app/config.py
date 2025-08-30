import os
import json

APP_VERSION = "ver1.6" 
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".crosshair_config.json")
DEFAULT_OVERALL_PRESET_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "CrosshairPresets")
DEFAULT_SHAPE_PRESET_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "CrosshairShapes")
PRESET_EXTENSION = ".mametaro"

def load_config():
    defaults = {
        "last_selected": "デフォルト設定",
        "overall_preset_folder": DEFAULT_OVERALL_PRESET_FOLDER,
        "shape_preset_folder": DEFAULT_SHAPE_PRESET_FOLDER,
        "monitor_apex": False,
        "toggle_hotkey": "ctrl+f1",
        "drawing_order": "dot_on_top" # Add this line
    }
    
    if not os.path.exists(CONFIG_FILE):
        return defaults

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

        if "crosshair_visible" in config: # 旧形式かの判定
            print("古い形式の設定ファイルを検出しました。新しいプリセット形式に変換します。")
            
            imported_preset_name = "旧バージョンからのインポート設定"
            overall_folder = config.get("preset_folder", DEFAULT_OVERALL_PRESET_FOLDER)
            os.makedirs(overall_folder, exist_ok=True)
            imported_preset_path = os.path.join(overall_folder, imported_preset_name + PRESET_EXTENSION)
            
            with open(imported_preset_path, "w", encoding="utf-8") as f_preset:
                json.dump(config, f_preset, indent=4)
            
            new_main_config = {
                "last_selected": imported_preset_name,
                "overall_preset_folder": overall_folder,
                "shape_preset_folder": DEFAULT_SHAPE_PRESET_FOLDER, # 新しいパスを追加
                "monitor_apex": config.get("monitor_apex", False),
                "toggle_hotkey": config.get("toggle_hotkey", "ctrl+f1")
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f_main:
                json.dump(new_main_config, f_main, indent=4)
            
            print(f"設定を '{imported_preset_name}' として保存しました。")
            return new_main_config
            
        else:
            # 新形式の場合は、デフォルト値を適用
            for key, value in defaults.items():
                config.setdefault(key, value)
            return config
            
    except Exception as e:
        print(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
        return defaults

    return defaults

def save_global_config(config):
    """ last_selected, preset_folder, monitor_apex のみを保存 """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"グローバル設定の保存に失敗: {e}")
