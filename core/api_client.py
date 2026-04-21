# @author: awen

import requests

from config import REQUEST_TIMEOUT, PER_PAGE
from core.token_manager import TokenManager
from utils.logger import logger


class OpenListClient:
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        self.session = requests.Session()

    @staticmethod
    def do_login(base_url: str, username: str, password: str) -> str:
        resp = requests.post(
            f"{base_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 200:
            raise ValueError(f"登录失败: {data.get('message', '未知错误')}")
        token = data["data"]["token"]
        return token

    def _request(self, path: str, body: dict) -> dict:
        self.token_manager.ensure_token()
        headers = self.token_manager.auth_header
        url = f"{self.token_manager._base_url}{path}"
        resp = self.session.post(url, json=body, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 200:
            logger.warning("请求失败 code=%s msg=%s, 尝试重新登录", data.get("code"), data.get("message"))
            self.token_manager.invalidate()
            self.token_manager.refresh()
            headers = self.token_manager.auth_header
            resp = self.session.post(url, json=body, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 200:
                raise ValueError(f"请求失败: {data.get('message', '未知错误')}")
        return data.get("data", {})

    def list_files(self, path: str, page: int = 1, per_page: int = PER_PAGE) -> dict:
        body = {
            "path": path,
            "password": "",
            "page": page,
            "per_page": per_page,
            "refresh": False,
        }
        return self._request("/api/fs/list", body)

    def get_file_info(self, path: str) -> dict:
        body = {"path": path, "password": ""}
        return self._request("/api/fs/get", body)
