# @author: awen

from utils.logger import logger


class TokenManager:
    def __init__(self, login_func):
        self._token: str = ""
        self._username: str = ""
        self._password: str = ""
        self._base_url: str = ""
        self._login_func = login_func

    @property
    def token(self) -> str:
        return self._token

    @property
    def auth_header(self) -> dict:
        if not self._token:
            return {}
        return {"Authorization": self._token}

    @property
    def is_authenticated(self) -> bool:
        return bool(self._token)

    def update_credentials(self, base_url: str, username: str, password: str):
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._token = ""

    def refresh(self) -> str:
        if not self._username or not self._password:
            raise ValueError("用户名或密码为空")
        logger.info("正在登录 %s ...", self._base_url)
        token = self._login_func(self._base_url, self._username, self._password)
        self._token = token
        logger.info("登录成功")
        return token

    def ensure_token(self) -> str:
        if not self._token:
            self.refresh()
        return self._token

    def invalidate(self):
        self._token = ""
