# @author: awen

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QGroupBox, QHBoxLayout, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal

from gui.styles import DEFAULT_SERVER_URL


class LoginWidget(QWidget):
    login_requested = pyqtSignal(str, str, str)
    disconnect_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        group = QGroupBox("服务器连接")
        layout = QFormLayout()

        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText(DEFAULT_SERVER_URL)
        layout.addRow("服务器地址:", self.server_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("admin")
        layout.addRow("用户名:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("请输入密码")
        layout.addRow("密码:", self.password_input)

        self.load_btn = QPushButton("加载配置")
        self.load_btn.setObjectName("browseBtn")
        self.load_btn.setFixedWidth(90)
        self.load_btn.clicked.connect(self._on_load_config)

        self.login_btn = QPushButton("连接")
        self.login_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.login_btn.clicked.connect(self._on_login)

        self.disconnect_btn = QPushButton("断开连接")
        self.disconnect_btn.setObjectName("dangerBtn")
        self.disconnect_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        self.disconnect_btn.setVisible(False)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.login_btn)
        btn_row.addWidget(self.disconnect_btn)
        layout.addRow(btn_row)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        layout.addRow(self.status_label)

        group.setLayout(layout)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(group)

    def _on_login(self):
        base_url = self.server_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not base_url or not username or not password:
            self.set_status(False, "请填写所有字段")
            return
        self.login_requested.emit(base_url, username, password)

    def _on_load_config(self):
        from utils.config_manager import load_config
        cfg = load_config()
        if cfg.get("server_url"):
            self.server_input.setText(cfg["server_url"])
        if cfg.get("username"):
            self.username_input.setText(cfg["username"])

    def set_status(self, connected: bool, msg: str = ""):
        if connected:
            self.status_label.setObjectName("statusOk")
            self.status_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
            self.status_label.setText(f"已连接 {msg}" if msg else "已连接")
            self.login_btn.setText("已连接")
            self.login_btn.setEnabled(False)
            self.server_input.setEnabled(False)
            self.username_input.setEnabled(False)
            self.password_input.setEnabled(False)
            self.load_btn.setEnabled(False)
            self.disconnect_btn.setVisible(True)
        else:
            self.status_label.setObjectName("statusErr")
            self.status_label.setStyleSheet("color: #c62828;")
            self.status_label.setText(msg or "未连接")
            self.login_btn.setText("连接")
            self.login_btn.setEnabled(True)
            self.server_input.setEnabled(True)
            self.username_input.setEnabled(True)
            self.password_input.setEnabled(True)
            self.load_btn.setEnabled(True)
            self.disconnect_btn.setVisible(False)

    def get_credentials(self) -> tuple:
        return (
            self.server_input.text().strip(),
            self.username_input.text().strip(),
            self.password_input.text().strip(),
        )
