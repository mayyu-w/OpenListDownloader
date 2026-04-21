# @author: awen

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QGroupBox, QPushButton, QLabel, QSpacerItem, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt

from core.file_scanner import FileInfo
from utils.format import format_file_size


class FileListWidget(QWidget):
    selection_changed = pyqtSignal(int)
    download_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: list = []
        self._checkboxes: list = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("文件列表")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(6, 6, 6, 6)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.download_btn = QPushButton("开始下载")
        self.download_btn.setEnabled(False)
        self.download_btn.setObjectName("primaryBtn")
        self.download_btn.clicked.connect(self.download_requested.emit)
        toolbar.addWidget(self.download_btn)

        toolbar.addSpacerItem(QSpacerItem(12, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        sep = QWidget()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background: #d0d7de;")
        toolbar.addWidget(sep)

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setObjectName("toolBtn")
        self.select_all_btn.clicked.connect(lambda: self.select_all(True))
        toolbar.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("全不选")
        self.deselect_all_btn.setObjectName("toolBtn")
        self.deselect_all_btn.clicked.connect(lambda: self.select_all(False))
        toolbar.addWidget(self.deselect_all_btn)

        self.invert_btn = QPushButton("反选")
        self.invert_btn.setObjectName("toolBtn")
        self.invert_btn.clicked.connect(self.invert_selection)
        toolbar.addWidget(self.invert_btn)

        toolbar.addStretch()

        self.total_label = QLabel("")
        self.total_label.setStyleSheet("color: #5a6a7a; font-size: 12px;")
        toolbar.addWidget(self.total_label)
        group_layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["选择", "序号", "文件名", "大小", "类型", "修改时间"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 50)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        group_layout.addWidget(self.table)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def populate(self, files: list):
        self._files = files
        self._checkboxes = []
        self.table.setRowCount(len(files))

        for row, fi in enumerate(files):
            cb = QCheckBox()
            cb.stateChanged.connect(lambda: self.selection_changed.emit(self._selected_count()))
            self._checkboxes.append(cb)

            cb_widget = QWidget()
            cb_widget.setStyleSheet("background: transparent;")
            cb_layout = QVBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, cb_widget)

            idx_item = QTableWidgetItem(str(row + 1))
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, idx_item)

            self.table.setItem(row, 2, QTableWidgetItem(fi.name))
            self.table.setItem(row, 3, QTableWidgetItem(format_file_size(fi.size)))
            self.table.setItem(row, 4, QTableWidgetItem(self._get_type(fi.name)))
            self.table.setItem(row, 5, QTableWidgetItem(fi.modified))

            self.table.setRowHeight(row, 28)

        self._update_total_label()

    def clear_files(self):
        self._files = []
        self._checkboxes = []
        self.table.setRowCount(0)
        self._update_total_label()

    def get_selected_files(self) -> list:
        selected = []
        for i, cb in enumerate(self._checkboxes):
            if cb.isChecked():
                selected.append(self._files[i])
        return selected

    def select_all(self, checked: bool):
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)
        self.selection_changed.emit(self._selected_count())

    def invert_selection(self):
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(not cb.isChecked())
            cb.blockSignals(False)
        self.selection_changed.emit(self._selected_count())

    def _selected_count(self) -> int:
        return sum(1 for cb in self._checkboxes if cb.isChecked())

    def _update_total_label(self):
        total = len(self._files)
        if total > 0:
            total_size = sum(f.size for f in self._files)
            self.total_label.setText(f"共 {total} 个文件 ({format_file_size(total_size)})")
        else:
            self.total_label.setText("")

    @staticmethod
    def _get_type(filename: str) -> str:
        dot = filename.rfind(".")
        if dot == -1:
            return ""
        return filename[dot:].upper()

    def get_total_info(self) -> tuple:
        total = len(self._files)
        selected = self._selected_count()
        selected_size = sum(
            self._files[i].size
            for i, cb in enumerate(self._checkboxes)
            if cb.isChecked()
        )
        return total, selected, selected_size
