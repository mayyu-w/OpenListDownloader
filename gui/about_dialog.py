# @author: awen

import os
import urllib.error
import urllib.request

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)

from version import __version__

_REPO_OWNER = "mayyu-w"
_REPO_NAME = "OpenListDownloader"
_RELEASE_BASE = f"https://github.com/{_REPO_OWNER}/{_REPO_NAME}/releases"
_LATEST_URL = f"https://github.com/{_REPO_OWNER}/{_REPO_NAME}/releases/latest"


def _parse_version(tag: str) -> tuple:
    return tuple(int(x) for x in tag.lstrip("v").split("."))


class _CheckUpdateWorker(QThread):
    result_ready = pyqtSignal(str)   # remote tag_name (e.g. "v0.7.0")
    error_occurred = pyqtSignal(str) # error message

    def run(self):
        try:
            req = urllib.request.Request(
                _LATEST_URL,
                headers={"User-Agent": "OpenListDownloader"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                final_url = resp.url
            parts = final_url.rstrip("/").split("/")
            tag = parts[-1] if parts else ""
            if tag:
                self.result_ready.emit(tag)
            else:
                self.error_occurred.emit("未获取到版本信息")
        except Exception as e:
            self.error_occurred.emit(str(e))


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setMinimumWidth(360)
        self.setFixedSize(360, 220)
        self._remote_tag = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(0)

        # 图标居中
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "icon.ico",
        )
        if os.path.isfile(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon_path).pixmap(64, 64))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
            layout.addSpacing(10)

        # 应用名称
        name_label = QLabel("OpenList 文件下载器")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(name_label)
        layout.addSpacing(4)

        # 版本号
        ver_label = QLabel(f"v{__version__}")
        ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_label.setStyleSheet("color: #5a6a7a; font-size: 13px;")
        layout.addWidget(ver_label)
        layout.addSpacing(4)

        # 状态提示
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #5a6a7a; font-size: 12px;")
        layout.addWidget(self.status_label)
        layout.addSpacing(16)

        # 底部按钮栏
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #d0d7de;")
        layout.addWidget(line)
        layout.addSpacing(12)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.changelog_btn = QPushButton("更新日志")
        self.changelog_btn.setObjectName("toolBtn")
        self.changelog_btn.clicked.connect(self._on_changelog)
        btn_row.addWidget(self.changelog_btn)

        btn_row.addStretch()

        self.update_btn = QPushButton("检测更新")
        self.update_btn.setObjectName("primaryBtn")
        self.update_btn.clicked.connect(self._on_check_update)
        btn_row.addWidget(self.update_btn)

        self.close_btn = QPushButton("关闭")
        self.close_btn.setObjectName("browseBtn")
        self.close_btn.clicked.connect(self.close)
        btn_row.addWidget(self.close_btn)

        layout.addLayout(btn_row)

    def _on_changelog(self):
        url = f"{_RELEASE_BASE}/tag/v{__version__}"
        QDesktopServices.openUrl(QUrl(url))

    def _on_check_update(self):
        if self._remote_tag:
            url = f"{_RELEASE_BASE}/tag/{self._remote_tag}"
            QDesktopServices.openUrl(QUrl(url))
            return

        self.update_btn.setEnabled(False)
        self.update_btn.setText("检测中...")
        self.status_label.setText("")

        self._worker = _CheckUpdateWorker(self)
        self._worker.result_ready.connect(self._on_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_result(self, remote_tag: str):
        local = _parse_version(__version__)
        remote = _parse_version(remote_tag)
        if remote > local:
            self._remote_tag = remote_tag
            self.status_label.setText(f"发现新版本 {remote_tag}")
            self.status_label.setStyleSheet("color: #1a73e8; font-size: 12px;")
            self.update_btn.setText("前往下载")
            self.update_btn.setEnabled(True)
        else:
            self.status_label.setText("已是最新版本")
            self.status_label.setStyleSheet("color: #4caf50; font-size: 12px;")
            self.update_btn.setText("检测更新")
            self.update_btn.setEnabled(True)

    def _on_error(self, msg: str):
        self.status_label.setText(f"检测失败: {msg}")
        self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
        self.update_btn.setText("检测更新")
        self.update_btn.setEnabled(True)
