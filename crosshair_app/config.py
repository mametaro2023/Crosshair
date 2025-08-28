import os
import json

APP_VERSION = "ver1.4"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".crosshair_config.json")
DEFAULT_PRESET_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "CrosshairPresets")
PRESET_EXTENSION = ".mametaro"

def load_config():
    defaults = {
        "crosshair_visible": True,
        "dot_visible": True,
        "dot_radius": 5,
        "crosshair_color": "#00FF66",
        "dot_outer_color": "#FFFFFF",
        "dot_inner_color": "#000000",
        "disabled_keys": [],
        "crosshair_alpha": 1.0,
        "dot_alpha": 1.0,
        "fade_on_shoot": False,
        "last_selected": "デフォルト設定",
        "preset_folder": DEFAULT_PRESET_FOLDER,
        "monitor_apex": False
    }
    
    if not os.path.exists(CONFIG_FILE):
        return defaults

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

        if "crosshair_visible" in config:
            print("古い形式の設定ファイルを検出しました。新しいプリセット形式に変換します。")
            
            imported_preset_name = "旧バージョンからのインポート設定"
            preset_folder = config.get("preset_folder", DEFAULT_PRESET_FOLDER)
            os.makedirs(preset_folder, exist_ok=True)
            imported_preset_path = os.path.join(preset_folder, imported_preset_name + PRESET_EXTENSION)
            
            with open(imported_preset_path, "w", encoding="utf-8") as f_preset:
                json.dump(config, f_preset, indent=4)
            
            new_main_config = {
                "last_selected": imported_preset_name,
                "preset_folder": preset_folder,
                "monitor_apex": config.get("monitor_apex", False)
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f_main:
                json.dump(new_main_config, f_main, indent=4)
            
            print(f"設定を '{imported_preset_name}' として保存しました。")

            for key, value in defaults.items():
                config.setdefault(key, value)
            return config
            
        else:
            defaults["preset_folder"] = config.get("preset_folder", DEFAULT_PRESET_FOLDER)
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
