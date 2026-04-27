# @author: awen

from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit


class NoMenuLineEdit(QLineEdit):
    """禁用右键菜单的文本输入框"""

    def contextMenuEvent(self, event):
        pass


class NoMenuPlainTextEdit(QPlainTextEdit):
    """禁用右键菜单的纯文本编辑框"""

    def contextMenuEvent(self, event):
        pass


LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #f5f7fa;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #2c3e50;
}

QGroupBox {
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 12px 10px 12px;
    background-color: #ffffff;
}
QGroupBox QWidget {
    background-color: transparent;
}
QGroupBox QPushButton {
    background: #1a73e8;
    color: #ffffff;
}
QGroupBox QPushButton:hover {
    background: #1557b0;
}
QGroupBox QPushButton:pressed {
    background: #0d47a1;
}
QGroupBox QPushButton:disabled {
    background: #b0c4de;
    color: #e8edf2;
}
QGroupBox QPushButton#browseBtn,
QGroupBox QPushButton#verifyBtn,
QGroupBox QPushButton#startBtn {
    background: #e8eef5;
    color: #1a73e8;
    border: 1px solid #b0c4de;
}
QGroupBox QPushButton#browseBtn:hover,
QGroupBox QPushButton#verifyBtn:hover,
QGroupBox QPushButton#startBtn:hover {
    background: #d0dff0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #1a73e8;
}

QLineEdit {
    padding: 6px 10px;
    border: 1px solid #c8cfd8;
    border-radius: 5px;
    background: #ffffff;
    selection-background-color: #1a73e8;
    selection-color: #ffffff;
    min-height: 22px;
}
QLineEdit:focus {
    border: 2px solid #1a73e8;
    padding: 5px 9px;
}
QLineEdit:disabled {
    background: #eef1f5;
    color: #9aa5b1;
}
QLineEdit::placeholder {
    color: #9aa5b1;
}

QPushButton {
    padding: 7px 18px;
    border: none;
    border-radius: 5px;
    background: #1a73e8;
    color: #ffffff;
    font-weight: bold;
    min-height: 22px;
}
QPushButton:hover {
    background: #1557b0;
}
QPushButton:pressed {
    background: #0d47a1;
}
QPushButton:disabled {
    background: #b0c4de;
    color: #e8edf2;
}

QPushButton#browseBtn,
QPushButton#startBtn {
    padding: 5px 12px;
    font-size: 12px;
    background: #e8eef5;
    color: #1a73e8;
    border: 1px solid #b0c4de;
}
QPushButton#browseBtn:hover,
QPushButton#startBtn:hover {
    background: #d0dff0;
}

QPushButton#toolBtn {
    padding: 5px 14px;
    font-size: 12px;
    background: #e8eef5;
    color: #1a73e8;
    border: 1px solid #b0c4de;
    font-weight: bold;
}
QPushButton#toolBtn:hover {
    background: #d0dff0;
    border-color: #1a73e8;
}

QPushButton#primaryBtn {
    padding: 6px 20px;
    font-size: 13px;
    background: #1a73e8;
    color: #ffffff;
    font-weight: bold;
    border: none;
}
QPushButton#primaryBtn:hover {
    background: #1557b0;
}
QPushButton#primaryBtn:disabled {
    background: #b0c4de;
    color: #e8edf2;
}

QPushButton#dangerBtn {
    padding: 5px 14px;
    font-size: 12px;
    background: #fef0f0;
    color: #f56c6c;
    border: 1px solid #fbc4c4;
    font-weight: bold;
}
QPushButton#dangerBtn:hover {
    background: #f56c6c;
    color: #ffffff;
    border-color: #f56c6c;
}
QPushButton#dangerBtn:pressed {
    background: #e04040;
    color: #ffffff;
}

QTableWidget {
    background: #ffffff;
    alternate-background-color: #f0f4f8;
    gridline-color: #e4e9ef;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    selection-background-color: #e0ecff;
    selection-color: #1a73e8;
}
QTableWidget::item {
    padding: 4px 8px;
    border-bottom: 1px solid #eef1f5;
}
QTableWidget::item:selected {
    background: #e0ecff;
    color: #1a73e8;
}
QHeaderView::section {
    background: #f0f4f8;
    color: #5a6a7a;
    padding: 6px 8px;
    border: none;
    border-bottom: 2px solid #1a73e8;
    font-weight: bold;
    font-size: 12px;
}

QProgressBar {
    border: 1px solid #d0d7de;
    border-radius: 5px;
    background: #e8eef5;
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a73e8, stop:1 #4fc3f7);
    border-radius: 4px;
}

QStatusBar {
    background: #ffffff;
    color: #5a6a7a;
    border-top: 1px solid #d0d7de;
    padding: 4px 12px;
    font-size: 12px;
}

QSplitter::handle {
    background: #d0d7de;
    width: 3px;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #f0f4f8;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #b0c4de;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #90a4c4;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #f0f4f8;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #b0c4de;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #90a4c4;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QCheckBox {
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #b0c4de;
    border-radius: 3px;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #1a73e8;
    border-color: #1a73e8;
}
QCheckBox::indicator:hover {
    border-color: #1a73e8;
}

QLabel#statusOk {
    color: #2e7d32;
    font-weight: bold;
}
QLabel#statusErr {
    color: #c62828;
}

QMessageBox {
    background: #ffffff;
}
QMessageBox QLabel {
    color: #2c3e50;
    font-size: 13px;
}
QMessageBox QPushButton {
    min-width: 80px;
}
"""

DEFAULT_SERVER_URL = "http://host:port"
DEFAULT_RPC_URL = "http://host:6800/jsonrpc"
DEFAULT_RPC_SECRET = ""
DEFAULT_SAVE_DIR = ""
