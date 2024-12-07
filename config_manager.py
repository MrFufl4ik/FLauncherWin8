import json, os
from consts import LNC_CONFIG_NAME, MCC_CONFIG_NAME, UPD_CONFIG_NAME

current_directory = os.getcwd()


def lnc_config_get(launcher_path) -> dict:
    config_file_path = os.path.join(launcher_path, LNC_CONFIG_NAME)
    with open(config_file_path, 'r') as f:
        try:
            return json.load(f)
        except:
            pass
    return None


def upd_config_get(modpack_path: str) -> dict:
    config_file_path = os.path.join(modpack_path, UPD_CONFIG_NAME)
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as f:
            try:
                return json.load(f)
            except:
                pass
    return None


def mc_config_get(modpack_path: str) -> dict:
    config_file_path = os.path.join(modpack_path, MCC_CONFIG_NAME)
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as f:
            try:
                return json.load(f)
            except:
                pass
    return None


def mc_config_set(modpack_path: str, config: dict) -> int:
    config_file_path = os.path.join(modpack_path, MCC_CONFIG_NAME)

    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as f:
            try:
                existing_config = json.load(f)
            except json.JSONDecodeError:
                existing_config = {}
    else:
        existing_config = {}

    existing_config.update(config)

    with open(config_file_path, 'w') as f:
        try:
            json.dump(existing_config, f, indent=4)
            return 0
        except:
            return 1

    return 1
