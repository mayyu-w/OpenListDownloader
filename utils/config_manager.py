# @author: awen

import json
import os

from utils.logger import logger

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "user_config.json")

_DEFAULTS = {
    "server_url": "",
    "scan_path": "",
    "scan_suffix": "",
    "aria2_path": "",
    "rpc_url": "",
    "rpc_secret": "",
    "save_dir": "",
}


def load_config() -> dict:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("已加载用户配置")
        return data
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.warning("加载配置失败: %s", e)
        return {}


def save_config(**kwargs):
    current = load_config()
    for k, v in kwargs.items():
        if v is not None:
            current[k] = v
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    logger.info("配置已保存")
