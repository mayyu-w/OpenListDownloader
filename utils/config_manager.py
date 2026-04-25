# @author: awen

import json
import os

try:
    import keyring
    _HAS_KEYRING = True
except ImportError:
    _HAS_KEYRING = False

from utils.logger import logger

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "config", "user_config.json")
SERVICE_NAME = "OpenListDownloader"

_DEFAULTS = {
    "server_url": "",
    "scan_path": "",
    "scan_suffix": "",
    "scan_recursive": True,
    "scan_depth": 20,
    "aria2_path": "",
    "rpc_url": "",
    "rpc_secret": "",
    "save_dir": "",
}


def load_config() -> dict:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except Exception as e:
        logger.warning("加载配置失败: %s", e)
        data = {}

    if _HAS_KEYRING:
        try:
            secret = keyring.get_password(SERVICE_NAME, "rpc_secret")
            if secret is not None:
                data["rpc_secret"] = secret
        except Exception:
            pass

    logger.info("已加载用户配置")
    return data


def save_config(**kwargs):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            current = json.load(f)
    except (FileNotFoundError, Exception):
        current = {}

    secret = kwargs.pop("rpc_secret", None)
    secret_stored_in_keyring = False

    if secret is not None and _HAS_KEYRING:
        try:
            keyring.set_password(SERVICE_NAME, "rpc_secret", secret)
            secret_stored_in_keyring = True
        except Exception:
            pass

    if not secret_stored_in_keyring and secret is not None:
        kwargs["rpc_secret"] = secret

    for k, v in kwargs.items():
        if v is not None:
            current[k] = v

    if secret_stored_in_keyring:
        current.pop("rpc_secret", None)

    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    logger.info("配置已保存")
