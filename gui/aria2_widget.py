# @author: awen

import os
import time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QGroupBox, QHBoxLayout,
    QFileDialog, QSizePolicy,
)
from PyQt6.QtCore import QThread, pyqtSignal

from config import DEFAULT_RPC_PORT
from core.aria2_rpc import Aria2RPC
from gui.styles import DEFAULT_RPC_URL, DEFAULT_RPC_SECRET, DEFAULT_SAVE_DIR
from utils.logger import logger


class Aria2Worker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, action, rpc_url, secret, aria2_path="", save_dir=""):
        super().__init__()
        self._action = action
        self._rpc_url = rpc_url
        self._secret = secret
        self._aria2_path = aria2_path
        self._save_dir = save_dir
        self.process = None

    def run(self):
        rpc = Aria2RPC(rpc_url=self._rpc_url, secret=self._secret)

        if self._action == "start":
            self._do_start(rpc)
        elif self._action == "stop":
            self._do_stop(rpc)

    def _do_start(self, rpc):
        ok, ver = rpc.verify_connection()
        if ok:
            self.finished.emit(True, f"EXTERNAL:{ver}")
            return

        if not os.path.isfile(self._aria2_path):
            self.finished.emit(False, f"文件不存在: {self._aria2_path}")
            return

        try:
            self.process = Aria2RPC.start_aria2(
                aria2_path=self._aria2_path,
                rpc_port=DEFAULT_RPC_PORT,
                secret=self._secret,
                save_dir=self._save_dir,
            )
            time.sleep(1)
            ok, ver = rpc.verify_connection()
            if ok:
                self.finished.emit(True, f"aria2 已启动 v{ver}")
            else:
                self.finished.emit(False, "启动后验证失败，请检查配置")
        except Exception as e:
            logger.exception("启动 aria2 失败")
            self.finished.emit(False, f"启动失败: {e}")

    def _do_stop(self, rpc):
        try:
            rpc._call("aria2.shutdown")
            time.sleep(0.5)
        except Exception:
            pass

        for _ in range(10):
            ok, _ = rpc.verify_connection()
            if not ok:
                break
            time.sleep(0.5)

        logger.info("aria2 已关闭")
        self.finished.emit(True, "aria2 已关闭")


class Aria2Widget(QWidget):
    config_loaded = pyqtSignal()
    running_changed = pyqtSignal(bool)
    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._worker = None
        self._process = None
        self._setup_ui()

    def _setup_ui(self):
        group = QGroupBox("aria2 配置")
        layout = QFormLayout()

        path_row = QHBoxLayout()
        self.aria2_path_input = QLineEdit()
        self.aria2_path_input.setPlaceholderText("aria2c.exe 完整路径")
        path_row.addWidget(self.aria2_path_input)
        self.browse_aria2_btn = QPushButton("浏览")
        self.browse_aria2_btn.setObjectName("browseBtn")
        self.browse_aria2_btn.clicked.connect(self._browse_aria2)
        path_row.addWidget(self.browse_aria2_btn)
        layout.addRow("aria2 路径:", path_row)

        self.rpc_url_input = QLineEdit()
        self.rpc_url_input.setPlaceholderText(DEFAULT_RPC_URL)
        layout.addRow("RPC 地址:", self.rpc_url_input)

        self.rpc_secret_input = QLineEdit()
        self.rpc_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.rpc_secret_input.setPlaceholderText("请输入 RPC 密码")
        layout.addRow("RPC 密码:", self.rpc_secret_input)

        dir_row = QHBoxLayout()
        self.save_dir_input = QLineEdit()
        self.save_dir_input.setPlaceholderText(DEFAULT_SAVE_DIR)
        dir_row.addWidget(self.save_dir_input)
        self.browse_dir_btn = QPushButton("浏览")
        self.browse_dir_btn.setObjectName("browseBtn")
        self.browse_dir_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.browse_dir_btn)
        layout.addRow("保存目录:", dir_row)

        btn_row = QHBoxLayout()
        self.load_btn = QPushButton("加载配置")
        self.load_btn.setObjectName("browseBtn")
        self.load_btn.setFixedWidth(90)
        self.load_btn.clicked.connect(self._on_load_config)
        btn_row.addWidget(self.load_btn)

        self.action_btn = QPushButton("启动 aria2")
        self.action_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.action_btn.clicked.connect(self._on_action_clicked)
        btn_row.addWidget(self.action_btn)
        layout.addRow(btn_row)

        status_row = QHBoxLayout()
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(12, 12)
        self.status_dot.setStyleSheet("background: #b0c4de; border-radius: 6px;")
        status_row.addWidget(self.status_dot)
        self.status_label = QLabel("未启动")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        layout.addRow("状态:", status_row)

        group.setLayout(layout)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(group)

    def _browse_aria2(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 aria2c", "", "可执行文件 (*.exe);;所有文件 (*)"
        )
        if path:
            self.aria2_path_input.setText(path)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择下载保存目录")
        if path:
            self.save_dir_input.setText(path)

    def _rpc_args(self):
        return self.rpc_url_input.text().strip(), self.rpc_secret_input.text().strip()

    def _on_load_config(self):
        from utils.config_manager import load_config
        cfg = load_config()
        if cfg.get("aria2_path"):
            self.aria2_path_input.setText(cfg["aria2_path"])
        if cfg.get("rpc_url"):
            self.rpc_url_input.setText(cfg["rpc_url"])
        if cfg.get("rpc_secret"):
            self.rpc_secret_input.setText(cfg["rpc_secret"])
        if cfg.get("save_dir"):
            self.save_dir_input.setText(cfg["save_dir"])
        self.config_loaded.emit()

    def _on_action_clicked(self):
        if self._worker:
            return
        if self._running:
            self.stop_requested.emit()
        else:
            self._do_start()

    def _do_start(self):
        aria2_path = self.aria2_path_input.text().strip()
        if not aria2_path:
            self._set_status(False, "请先填写 aria2 路径")
            return

        self.action_btn.setEnabled(False)
        self.action_btn.setText("正在启动...")
        self._set_inputs_enabled(False)
        self._show_loading("正在连接 / 启动 aria2...")

        rpc_url, secret = self._rpc_args()
        self._worker = Aria2Worker(
            action="start", rpc_url=rpc_url, secret=secret,
            aria2_path=aria2_path, save_dir=self.save_dir_input.text().strip(),
        )
        self._worker.finished.connect(self._on_start_finished)
        self._worker.start()

    def _do_stop(self):
        self.action_btn.setEnabled(False)
        self.action_btn.setText("正在关闭...")
        self._set_inputs_enabled(False)
        self._show_loading("正在关闭 aria2...")

        rpc_url, secret = self._rpc_args()
        self._worker = Aria2Worker(action="stop", rpc_url=rpc_url, secret=secret)
        self._worker.finished.connect(self._on_stop_finished)
        self._worker.start()

    def _on_start_finished(self, ok: bool, msg: str):
        worker_process = self._worker.process if self._worker else None
        self._worker = None
        if ok:
            if msg.startswith("EXTERNAL:"):
                ver = msg.split(":", 1)[1]
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, "检测到已有 aria2",
                    f"检测到已有 aria2 v{ver} 在运行中。\n\n"
                    "是 - 使用现有实例（关闭程序时不会停止该进程）\n"
                    "否 - 请手动关闭后再点击启动",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._process = None
                    self._running = True
                    self._update_ui(True, f"已连接到外部 aria2 v{ver}")
                    self.running_changed.emit(True)
                else:
                    self._set_status(False, "请先关闭现有 aria2 后重试")
                    self.action_btn.setEnabled(True)
                    self.action_btn.setText("启动 aria2")
                    self._set_inputs_enabled(True)
                return

            self._process = worker_process
            self._running = True
            self._update_ui(True, msg)
            self._save_config()
            self.running_changed.emit(True)
        else:
            self._set_status(False, msg)
            self.action_btn.setEnabled(True)
            self.action_btn.setText("启动 aria2")
            self._set_inputs_enabled(True)

    def _on_stop_finished(self, ok: bool, msg: str):
        self._worker = None
        self._running = False
        self._process = None
        self._update_ui(False, msg)
        self.running_changed.emit(False)

    def force_cleanup(self):
        """应用退出时强制清理自启动的 aria2 进程"""
        if self._process is None:
            return
        logger.info("正在清理 aria2 进程 (PID=%s)", self._process.pid)
        try:
            rpc_url, secret = self._rpc_args()
            rpc = Aria2RPC(rpc_url=rpc_url, secret=secret)
            rpc._call("aria2.shutdown")
        except Exception:
            pass
        try:
            self._process.wait(timeout=3)
        except Exception:
            try:
                self._process.terminate()
            except Exception:
                pass
        self._process = None
        self._running = False

    def _save_config(self):
        from utils.config_manager import save_config
        save_config(
            aria2_path=self.aria2_path_input.text().strip(),
            rpc_url=self.rpc_url_input.text().strip(),
            rpc_secret=self.rpc_secret_input.text().strip(),
            save_dir=self.save_dir_input.text().strip(),
        )

    def _show_loading(self, msg: str):
        self.status_dot.setStyleSheet("background: #f9a825; border-radius: 6px;")
        self.status_label.setStyleSheet("color: #f9a825; font-weight: bold;")
        self.status_label.setText(msg)

    def _set_status(self, ok: bool, msg: str):
        if ok:
            self.status_dot.setStyleSheet("background: #2e7d32; border-radius: 6px;")
            self.status_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            self.status_dot.setStyleSheet("background: #c62828; border-radius: 6px;")
            self.status_label.setStyleSheet("color: #c62828;")
        self.status_label.setText(msg)

    def _update_ui(self, running: bool, msg: str):
        self._set_status(running, msg)
        self.action_btn.setEnabled(True)
        self.action_btn.setText("关闭 aria2" if running else "启动 aria2")
        self._set_inputs_enabled(not running)

    def _set_inputs_enabled(self, enabled: bool):
        self.aria2_path_input.setEnabled(enabled)
        self.browse_aria2_btn.setEnabled(enabled)
        self.save_dir_input.setEnabled(enabled)
        self.browse_dir_btn.setEnabled(enabled)
        self.load_btn.setEnabled(enabled)

    def get_rpc_config(self) -> dict:
        return {
            "rpc_url": self.rpc_url_input.text().strip(),
            "secret": self.rpc_secret_input.text().strip(),
            "save_dir": self.save_dir_input.text().strip(),
        }
