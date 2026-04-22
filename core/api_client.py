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
        token_data = data.get("data")
        if not token_data or not isinstance(token_data, dict):
            raise ValueError("登录失败: 服务器返回数据格式异常")
        token = token_data.get("token")
        if not token:
            raise ValueError("登录失败: 未获取到有效令牌")
        return token

    def _request(self, path: str, body: dict) -> dict:
        max_retries = 3
        last_error = ""
        for attempt in range(max_retries):
            self.token_manager.ensure_token()
            headers = self.token_manager.auth_header
            url = f"{self.token_manager._base_url}{path}"
            try:
                resp = self.session.post(url, json=body, headers=headers, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    logger.warning("请求异常 (%d/%d): %s", attempt + 1, max_retries, e)
                    self.token_manager.invalidate()
                    continue
                raise

            if data.get("code") != 200:
                last_error = data.get("message", "未知错误")
                if attempt < max_retries - 1:
                    logger.warning("请求失败 code=%s msg=%s (%d/%d)",
                                   data.get("code"), last_error, attempt + 1, max_retries)
                    self.token_manager.invalidate()
                    continue
                raise ValueError(f"请求失败: {last_error}")

            result = data.get("data")
            if result is None:
                raise ValueError("服务器返回数据格式异常")
            return result

        raise ValueError(f"请求失败，已重试 {max_retries} 次: {last_error}")

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
