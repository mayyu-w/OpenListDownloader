# @author: awen

import sys

from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.styles import LIGHT_THEME


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(LIGHT_THEME)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
