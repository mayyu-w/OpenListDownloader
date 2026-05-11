# @author: awen

import time
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QProgressBar, QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal

from utils.format import format_file_size


_STATUS_TEXT = {
    "waiting": "等待中",
    "active": "下载中",
    "paused": "已暂停",
    "complete": "已完成",
    "error": "失败",
    "removed": "已移除",
}

_STATUS_ORDER = {
    "下载中": 0,
    "等待中": 1,
    "已暂停": 2,
    "已完成": 3,
    "失败": 4,
    "已移除": 5,
}


class DownloadProgressWidget(QWidget):
    pause_all_requested = pyqtSignal()
    resume_all_requested = pyqtSignal()
    delete_all_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks: dict[int, dict] = {}
        self._next_id = 1
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("下载进度")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(6, 6, 6, 6)

        toolbar = QHBoxLayout()
        self.pause_all_btn = QPushButton("全部暂停")
        self.pause_all_btn.setObjectName("toolBtn")
        self.pause_all_btn.clicked.connect(self.pause_all_requested.emit)

        self.resume_all_btn = QPushButton("继续下载")
        self.resume_all_btn.setObjectName("toolBtn")
        self.resume_all_btn.clicked.connect(self.resume_all_requested.emit)

        self.clear_finished_btn = QPushButton("清除已完成")
        self.clear_finished_btn.setObjectName("browseBtn")
        self.clear_finished_btn.clicked.connect(self._on_clear_finished)

        self.delete_all_btn = QPushButton("删除全部任务")
        self.delete_all_btn.setObjectName("toolBtn")
        self.delete_all_btn.clicked.connect(self.delete_all_requested.emit)

        toolbar.addWidget(self.pause_all_btn)
        toolbar.addWidget(self.resume_all_btn)
        toolbar.addWidget(self.clear_finished_btn)
        toolbar.addWidget(self.delete_all_btn)
        toolbar.addStretch()
        group_layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["序号", "文件名", "大小", "进度", "速度", "状态", "添加时间", "完成时间"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(3, 180)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        group_layout.addWidget(self.table)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def _find_row(self, task_id: int) -> int:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == task_id:
                return row
        return -1

    def add_task(self, filename: str, size: int) -> int:
        task_id = self._next_id
        self._next_id += 1
        now = datetime.now().strftime("%H:%M:%S")
        self._tasks[task_id] = {
            "id": task_id,
            "filename": filename,
            "size": size,
            "status": "waiting",
            "progress": 0,
            "gid": "",
            "add_time": now,
            "finish_time": "",
            "error_message": "",
            "last_active_time": 0.0,
            "speed": 0,
        }
        self._append_table_row(self._tasks[task_id])
        return task_id

    def set_task_gid(self, task_id: int, gid: str):
        task = self._tasks.get(task_id)
        if not task:
            return
        task["gid"] = gid
        task["status"] = "active"
        task["last_active_time"] = time.time()
        self._refresh_row(task_id)

    def set_task_error(self, task_id: int, message: str):
        task = self._tasks.get(task_id)
        if not task:
            return
        task["status"] = "error"
        task["error_message"] = message
        task["finish_time"] = datetime.now().strftime("%H:%M:%S")
        self._refresh_row(task_id)

    def update_task_progress(self, task_id: int, info: dict):
        task = self._tasks.get(task_id)
        if not task:
            return
        task["progress"] = info.get("progress", 0)
        task["speed"] = info.get("speed", 0)
        status = info.get("status", task["status"])
        task["last_active_time"] = time.time()
        if status == "complete":
            task["status"] = "complete"
            task["progress"] = 100
            task["finish_time"] = datetime.now().strftime("%H:%M:%S")
        elif status == "error":
            task["status"] = "error"
            task["error_message"] = info.get("error_message", "未知错误")
            task["finish_time"] = datetime.now().strftime("%H:%M:%S")
        elif status == "removed":
            task["status"] = "removed"
            task["finish_time"] = datetime.now().strftime("%H:%M:%S")
        else:
            task["status"] = status
        self._refresh_row(task_id)

    def get_active_task_ids(self) -> list[int]:
        return [
            tid for tid, t in self._tasks.items()
            if t["gid"] and t["status"] == "active"
        ]

    def get_pending_task_gids(self) -> dict[str, int]:
        return {
            t["gid"]: tid for tid, t in self._tasks.items()
            if t["gid"] and t["status"] == "waiting"
        }

    def get_unfinished_count(self) -> int:
        return sum(
            1 for t in self._tasks.values()
            if t["status"] in ("active", "waiting")
        )

    def mark_stale_active_tasks(self, timeout_seconds: int = 60) -> list[int]:
        import time
        now = time.time()
        stale_ids = []
        for tid, t in self._tasks.items():
            if t["status"] != "active" or not t["gid"]:
                continue
            last_active = t.get("last_active_time")
            if last_active and (now - last_active) > timeout_seconds:
                stale_ids.append(tid)
        return stale_ids

    def find_completed_names(self, filenames: list[str]) -> list[str]:
        completed = {t["filename"] for t in self._tasks.values() if t["status"] == "complete"}
        return [f for f in filenames if f in completed]

    def all_finished(self) -> bool:
        return all(
            t["status"] in ("complete", "error", "removed")
            for t in self._tasks.values()
        )

    def has_finished_tasks(self) -> bool:
        return any(t["status"] == "complete" for t in self._tasks.values())

    def clear_finished(self):
        self._tasks = {
            k: v for k, v in self._tasks.items() if v["status"] != "complete"
        }
        self._rebuild_table()
        self._update_button_states()

    def clear_all(self):
        self._tasks.clear()
        self._rebuild_table()
        self._update_button_states()

    def get_all_gids(self) -> list[str]:
        return [t["gid"] for t in self._tasks.values() if t["gid"]]

    def _on_clear_finished(self):
        self.clear_finished()

    def _update_button_states(self):
        has_any = bool(self._tasks)
        has_active = any(t["status"] == "active" for t in self._tasks.values())
        has_paused = any(t["status"] == "paused" for t in self._tasks.values())
        has_completed = any(t["status"] == "complete" for t in self._tasks.values())

        self.pause_all_btn.setEnabled(has_active)
        self.resume_all_btn.setEnabled(has_paused)
        self.clear_finished_btn.setEnabled(has_completed)
        self.delete_all_btn.setEnabled(has_any)

    def remove_waiting_tasks(self):
        self._tasks = {
            k: v for k, v in self._tasks.items()
            if not (v["status"] == "waiting" and not v["gid"])
        }
        self._rebuild_table()
        self._update_button_states()

    def _append_table_row(self, task: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._fill_row(row, task)

    def _refresh_row(self, task_id: int):
        row = self._find_row(task_id)
        if row < 0:
            return
        self._fill_row(row, self._tasks[task_id])

    def batch_update(self, updates: list[tuple[int, dict]]):
        self.table.setSortingEnabled(False)
        self.table.setUpdatesEnabled(False)
        for task_id, info in updates:
            self.update_task_progress(task_id, info)
        self.table.setUpdatesEnabled(True)
        self.table.setSortingEnabled(True)
        self._update_button_states()

    def _rebuild_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        sorted_tasks = sorted(self._tasks.values(), key=lambda t: t["id"])
        for row, task in enumerate(sorted_tasks):
            self.table.insertRow(row)
            self._fill_row(row, task)
        self.table.setSortingEnabled(True)

    def _fill_row(self, row: int, task: dict):
        idx_item = self.table.item(row, 0)
        if idx_item is None:
            idx_item = QTableWidgetItem()
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, idx_item)
        idx_item.setText(str(task["id"]))
        idx_item.setData(Qt.ItemDataRole.UserRole, task["id"])

        name_item = self.table.item(row, 1)
        if name_item is None:
            self.table.setItem(row, 1, QTableWidgetItem(task["filename"]))
        else:
            name_item.setText(task["filename"])

        size_item = self.table.item(row, 2)
        if size_item is None:
            size_item = QTableWidgetItem()
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, size_item)
        size_item.setText(format_file_size(task["size"]))

        bar = self.table.cellWidget(row, 3)
        if bar is None:
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(True)
            bar.setFixedHeight(20)
            self.table.setCellWidget(row, 3, bar)
        bar.setValue(task["progress"])
        bar.setFormat(f"{task['progress']}%")
        bar.setStyleSheet(self._progress_style(task["status"]))

        speed_text = f"{format_file_size(task['speed'])}/s" if task["speed"] > 0 else ""
        speed_item = self.table.item(row, 4)
        if speed_item is None:
            speed_item = QTableWidgetItem()
            speed_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, speed_item)
        speed_item.setText(speed_text)

        status_text = _STATUS_TEXT.get(task["status"], task["status"])
        if task["status"] == "error" and task.get("error_message"):
            status_text += f" ({task['error_message']})"
        status_item = self.table.item(row, 5)
        if status_item is None:
            status_item = QTableWidgetItem()
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, status_item)
        status_item.setText(status_text)
        status_item.setData(Qt.ItemDataRole.UserRole, _STATUS_ORDER.get(status_text, 99))

        add_item = self.table.item(row, 6)
        if add_item is None:
            add_item = QTableWidgetItem()
            add_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, add_item)
        add_item.setText(task["add_time"])

        finish_item = self.table.item(row, 7)
        if finish_item is None:
            finish_item = QTableWidgetItem()
            finish_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, finish_item)
        finish_item.setText(task["finish_time"])

        self.table.setRowHeight(row, 28)

    @staticmethod
    def _progress_style(status: str) -> str:
        if status == "complete":
            return """
                QProgressBar { border: 1px solid #c8e6c9; border-radius: 4px;
                    background: #e8f5e9; height: 20px; text-align: center; }
                QProgressBar::chunk { background: #4caf50; border-radius: 3px; }
            """
        if status == "error":
            return """
                QProgressBar { border: 1px solid #ffcdd2; border-radius: 4px;
                    background: #ffebee; height: 20px; text-align: center; }
                QProgressBar::chunk { background: #f44336; border-radius: 3px; }
            """
        return """
            QProgressBar { border: 1px solid #d0d7de; border-radius: 4px;
                background: #e8eef5; height: 20px; text-align: center; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #1a73e8, stop:1 #4fc3f7); border-radius: 3px; }
        """
