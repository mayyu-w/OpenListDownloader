# @author: awen

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QLineEdit, QGroupBox, QFormLayout,
    QStatusBar, QMessageBox, QSplitter, QProgressBar,
    QScrollArea, QSizePolicy, QMenuBar,
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtGui import QDesktopServices

from core.api_client import OpenListClient
from core.token_manager import TokenManager
from core.file_scanner import FileScanner
from core.aria2_rpc import Aria2RPC
from gui.login_widget import LoginWidget
from gui.file_list_widget import FileListWidget
from gui.aria2_widget import Aria2Widget
from gui.download_progress_widget import DownloadProgressWidget
from utils.format import format_file_size
from utils.logger import logger
from version import __version__
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenList 文件下载器")
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.ico")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setMinimumSize(1200, 800)
        self.resize(1300, 850)

        self.token_manager = TokenManager(OpenListClient.do_login)
        self.client = OpenListClient(self.token_manager)
        self.scanner: FileScanner = None
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_download_progress)
        self._rpc: Aria2RPC = None

        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setMinimumWidth(400)
        left_scroll.setMaximumWidth(400)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        self.login_widget = LoginWidget()
        self.login_widget.login_requested.connect(self._on_login)
        self.login_widget.disconnect_requested.connect(self._on_disconnect)
        left_layout.addWidget(self.login_widget)

        scan_group = QGroupBox("文件扫描")
        scan_layout = QFormLayout()
        scan_layout.setSpacing(8)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("如: /阿里云盘/影视")
        scan_layout.addRow("远程路径:", self.path_input)

        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("如: .mp4,.mkv,.avi（留空不过滤）")
        scan_layout.addRow("文件后缀:", self.suffix_input)

        scan_btn_row = QHBoxLayout()
        self.scan_load_btn = QPushButton("加载配置")
        self.scan_load_btn.setObjectName("browseBtn")
        self.scan_load_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.scan_load_btn.clicked.connect(self._on_load_scan_config)
        scan_btn_row.addWidget(self.scan_load_btn)

        self.scan_btn = QPushButton("扫描文件")
        self.scan_btn.setEnabled(False)
        self.scan_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.scan_btn.clicked.connect(self._on_scan)
        scan_btn_row.addWidget(self.scan_btn)
        scan_layout.addRow(scan_btn_row)

        self.scan_progress = QProgressBar()
        self.scan_progress.setFixedHeight(16)
        self.scan_progress.setRange(0, 1)
        self.scan_progress.setValue(0)
        self.scan_progress.setTextVisible(False)
        scan_layout.addRow(self.scan_progress)

        scan_group.setLayout(scan_layout)
        left_layout.addWidget(scan_group)

        self.aria2_widget = Aria2Widget()
        self.aria2_widget.running_changed.connect(self._on_aria2_running_changed)
        self.aria2_widget.stop_requested.connect(self._on_aria2_stop_requested)
        left_layout.addWidget(self.aria2_widget)

        left_layout.addStretch()
        left_scroll.setWidget(left_panel)

        self.file_list_widget = FileListWidget()
        self.file_list_widget.selection_changed.connect(self._on_selection_changed)
        self.file_list_widget.download_requested.connect(self._on_download)
        self.file_list_widget.open_download_dir_requested.connect(self._on_open_download_dir)
        self.file_list_widget.clear_finished_requested.connect(self._on_clear_finished)

        self.download_progress_widget = DownloadProgressWidget()

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.file_list_widget)
        right_splitter.addWidget(self.download_progress_widget)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 2)
        right_splitter.setHandleWidth(3)

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setHandleWidth(3)

        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 请连接 OpenList 服务器")

        version_label = QLabel(f"v{__version__}")
        version_label.setStyleSheet("color: #9aa5b1; font-size: 11px; margin-right: 6px;")
        self.status_bar.addPermanentWidget(version_label)

    def _on_login(self, base_url: str, username: str, password: str):
        self.login_widget.set_status(False, "正在连接...")
        try:
            self.token_manager.update_credentials(base_url, username, password)
            self.token_manager.refresh()
            self.login_widget.set_status(True, base_url)
            self.scan_btn.setEnabled(True)
            self.status_bar.showMessage(f"已连接: {base_url}")
            from utils.config_manager import save_config
            save_config(server_url=base_url, username=username)
        except Exception as e:
            self.login_widget.set_status(False, f"连接失败: {e}")
            self.scan_btn.setEnabled(False)
            logger.exception("登录失败")

    def _on_disconnect(self):
        active = self.download_progress_widget.get_active_gids()
        if active:
            reply = QMessageBox.warning(
                self, "断开连接",
                f"当前有 {len(active)} 个下载任务尚未完成。\n断开连接后更换账号可能导致续传失败。\n\n是否确认断开？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return
        self.login_widget.set_status(False, "未连接")
        self.scan_btn.setEnabled(False)
        self.path_input.clear()
        self.suffix_input.clear()
        self.file_list_widget.clear_files()
        self.status_bar.showMessage("已断开连接 - 请重新登录")

    def _on_load_scan_config(self):
        from utils.config_manager import load_config
        cfg = load_config()
        if cfg.get("scan_path"):
            self.path_input.setText(cfg["scan_path"])
        if cfg.get("scan_suffix"):
            self.suffix_input.setText(cfg["scan_suffix"])

    def _on_scan(self):
        path = self.path_input.text().strip()
        if not path:
            QMessageBox.warning(self, "提示", "请输入远程路径")
            return

        suffix_text = self.suffix_input.text().strip()
        suffixes = []
        if suffix_text:
            suffixes = [s.strip() for s in suffix_text.split(",") if s.strip()]

        self.scan_btn.setEnabled(False)
        self.scan_progress.setRange(0, 0)
        self.file_list_widget.clear_files()
        self.status_bar.showMessage(f"正在扫描: {path}")

        from utils.config_manager import save_config
        save_config(scan_path=path, scan_suffix=suffix_text)

        self.scanner = FileScanner(self.client, path, suffixes)
        self.scanner.scan_progress.connect(self._on_scan_progress)
        self.scanner.scan_finished.connect(self._on_scan_finished)
        self.scanner.scan_error.connect(self._on_scan_error)
        self.scanner.start()

    def _on_scan_progress(self, current_path: str):
        self.status_bar.showMessage(f"扫描中: {current_path}")

    def _on_scan_finished(self, files: list):
        self.scan_btn.setEnabled(True)
        self.scan_progress.setRange(0, 1)
        self.scan_progress.setValue(1)
        self.file_list_widget.populate(files)
        self.status_bar.showMessage(f"扫描完成, 共 {len(files)} 个文件")

    def _on_scan_error(self, error: str):
        self.scan_btn.setEnabled(True)
        self.scan_progress.setRange(0, 1)
        self.scan_progress.setValue(1)
        self.status_bar.showMessage(f"扫描失败: {error}")
        QMessageBox.critical(self, "扫描错误", error)

    def _on_selection_changed(self, count: int):
        self.file_list_widget.download_btn.setEnabled(count > 0)
        total, selected, selected_size = self.file_list_widget.get_total_info()
        self.status_bar.showMessage(
            f"文件总数: {total} | 已选: {selected} | 选中大小: {format_file_size(selected_size)}"
        )

    def _on_download(self):
        selected = self.file_list_widget.get_selected_files()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要下载的文件")
            return

        if not self.aria2_widget._running:
            QMessageBox.warning(self, "提示", "请先启动 aria2")
            return

        rpc_config = self.aria2_widget.get_rpc_config()
        if not rpc_config["save_dir"]:
            QMessageBox.warning(self, "提示", "请先设置下载保存目录")
            return

        dup_names = self.download_progress_widget.find_completed_names(
            [fi.name for fi in selected]
        )
        if dup_names:
            preview = "\n".join(dup_names[:10])
            suffix = f"\n...等共 {len(dup_names)} 个" if len(dup_names) > 10 else ""
            reply = QMessageBox.question(
                self, "重复下载",
                f"以下文件在下载记录中已标记为完成，可能已存在于保存目录中：\n{preview}{suffix}\n\n是否仍然继续下载？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        rpc = Aria2RPC(rpc_url=rpc_config["rpc_url"], secret=rpc_config["secret"])
        ok, ver = rpc.verify_connection()
        if not ok:
            QMessageBox.critical(self, "错误", f"aria2 连接失败: {ver}\n请确认 aria2 已启动")
            return

        self._rpc = rpc
        self.file_list_widget.download_btn.setEnabled(False)
        self.status_bar.showMessage("正在获取下载链接并添加任务...")

        for fi in selected:
            task_id = self.download_progress_widget.add_task(fi.name, fi.size)
            try:
                info = self.client.get_file_info(fi.path)
                raw_url = info.get("raw_url", "")
                if not raw_url:
                    logger.warning("未获取到下载链接: %s", fi.name)
                    self.download_progress_widget.set_task_error(task_id, "未获取到下载链接")
                    continue

                gid = rpc.add_download(
                    url=raw_url,
                    save_dir=rpc_config["save_dir"],
                    filename=fi.name,
                    headers=self.token_manager.auth_header if self.token_manager.auth_header else None,
                )
                logger.info("已添加下载: %s GID=%s", fi.name, gid)
                self.download_progress_widget.set_task_gid(task_id, gid)
            except Exception as e:
                logger.error("下载失败 %s: %s", fi.name, e)
                self.download_progress_widget.set_task_error(task_id, str(e))

        self.file_list_widget.download_btn.setEnabled(True)
        self.status_bar.showMessage("下载任务已添加，正在监控进度...")
        self._poll_timer.start(2000)

    def _setup_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        help_menu = menu_bar.addMenu("帮助")

        act_config = QAction("配置目录", self)
        act_config.triggered.connect(self._open_config_dir)
        help_menu.addAction(act_config)

        act_log = QAction("日志目录", self)
        act_log.triggered.connect(self._open_log_dir)
        help_menu.addAction(act_log)

    def _open_config_dir(self):
        from utils.config_manager import load_config
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        os.makedirs(config_dir, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(config_dir))

    def _open_log_dir(self):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(log_dir))

    def closeEvent(self, event):
        self._poll_timer.stop()
        if self.scanner and self.scanner.isRunning():
            self.scanner.cancel()
            self.scanner.wait(3000)
        event.accept()

    def _on_aria2_running_changed(self, running: bool):
        self.file_list_widget.open_dir_btn.setEnabled(running)

    def _on_aria2_stop_requested(self):
        active = self.download_progress_widget.get_active_gids()
        if active:
            reply = QMessageBox.question(
                self, "确认关闭",
                f"当前有 {len(active)} 个任务正在下载中，关闭 aria2 将停止所有下载。\n是否立即停止下载并关闭 aria2？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return
        self._poll_timer.stop()
        self.aria2_widget._do_stop()

    def _on_open_download_dir(self):
        save_dir = self.aria2_widget.save_dir_input.text().strip()
        if not save_dir or not os.path.isdir(save_dir):
            QMessageBox.warning(self, "提示", "下载目录不存在或未设置")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(save_dir))

    def _on_clear_finished(self):
        self.download_progress_widget.clear_finished()
        self._update_clear_finished_btn()

    def _update_clear_finished_btn(self):
        self.file_list_widget.clear_finished_btn.setEnabled(
            self.download_progress_widget.has_finished_tasks()
        )

    def _poll_download_progress(self):
        if not self._rpc:
            self._poll_timer.stop()
            return
        active = self.download_progress_widget.get_active_gids()
        if not active:
            self._poll_timer.stop()
            self.status_bar.showMessage("所有下载任务已完成")
            self._update_clear_finished_btn()
            return
        for row, gid in active:
            try:
                info = self._rpc.get_download_status(gid)
                self.download_progress_widget.update_task_progress(row, info)
            except Exception as e:
                logger.warning("查询进度失败 GID=%s: %s", gid, e)
        self._update_clear_finished_btn()
        if self.download_progress_widget.all_finished():
            self._poll_timer.stop()
            self.status_bar.showMessage("所有下载任务已完成")
            self._update_clear_finished_btn()
