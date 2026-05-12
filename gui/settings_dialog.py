# @author: awen

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QCheckBox,
    QDialogButtonBox, QGroupBox,
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(360)
        self.setFixedSize(400, 200)
        self._settings = dict(settings)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        group = QGroupBox("显示与行为")
        form = QFormLayout()
        form.setSpacing(12)

        self.dark_mode_check = QCheckBox("使用暗色主题")
        self.dark_mode_check.setChecked(self._settings.get("dark_mode", False))
        form.addRow(self.dark_mode_check)

        self.close_to_tray_check = QCheckBox("关闭按钮最小化到系统托盘")
        self.close_to_tray_check.setChecked(self._settings.get("close_to_tray", True))
        form.addRow(self.close_to_tray_check)

        group.setLayout(form)
        layout.addWidget(group)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_settings(self) -> dict:
        return {
            "dark_mode": self.dark_mode_check.isChecked(),
            "close_to_tray": self.close_to_tray_check.isChecked(),
        }
