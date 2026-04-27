# @author: awen

import os
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from gui.main_window import MainWindow
from gui.styles import LIGHT_THEME


def _ensure_single_instance():
    """通过文件锁确保同一时间只运行一个客户端实例"""
    lock_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "config", ".app.lock"
    )
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)

    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    except OSError as e:
        return None, f"无法创建锁文件: {e}"

    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(lock_fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, IOError):
        os.close(lock_fd)
        return None, None  # 已有实例在运行

    return lock_fd, None


def main():
    lock_fd, error = _ensure_single_instance()
    if lock_fd is None and error is None:
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None, "程序已运行",
            "OpenListDownloader 已在运行中，请勿重复打开。\n"
            "如需多实例运行，请先关闭已有窗口。",
        )
        sys.exit(1)
    if lock_fd is None:
        print(error)
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(LIGHT_THEME)

    def _global_excepthook(exc_type, exc_value, exc_tb):
        import traceback
        from utils.logger import logger
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.critical("未捕获异常:\n%s", tb_text)
        try:
            QMessageBox.critical(None, "程序错误", f"发生未预期的错误:\n\n{exc_value}")
        except Exception:
            pass

    sys.excepthook = _global_excepthook

    window = MainWindow()
    window.show()
    exit_code = app.exec()

    os.close(lock_fd)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
