# @author: awen

import threading
from dataclasses import dataclass, field

from PyQt6.QtCore import QThread, pyqtSignal

from config import PER_PAGE, MAX_DEPTH, MAX_PAGES
from core.api_client import OpenListClient
from utils.logger import logger


@dataclass
class FileInfo:
    name: str
    path: str
    size: int
    is_dir: bool
    modified: str
    download_url: str = ""


class FileScanner(QThread):
    scan_progress = pyqtSignal(str)
    scan_finished = pyqtSignal(list, int)
    scan_error = pyqtSignal(str)

    def __init__(self, client: OpenListClient, root_path: str,
                 suffixes: list, recursive: bool = True, max_depth: int = 20,
                 parent=None):
        super().__init__(parent)
        self.client = client
        self.root_path = root_path
        self.suffixes = [s.lower() for s in suffixes]
        self.recursive = recursive
        self.max_depth = max_depth
        self._cancel_event = threading.Event()
        self.total_scanned = 0

    def cancel(self):
        self._cancel_event.set()

    def run(self):
        try:
            logger.info("开始扫描: %s (后缀过滤: %s, 递归: %s, 最大深度: %d)",
                        self.root_path, self.suffixes or "无",
                        self.recursive, self.max_depth)
            self.total_scanned = 0
            results = self._scan_dir(self.root_path, depth=0)
            if not self._cancel_event.is_set():
                logger.info("扫描完成, 共找到 %d 个文件 (总计 %d)", len(results), self.total_scanned)
                self.scan_finished.emit(results, self.total_scanned)
        except Exception as e:
            if not self._cancel_event.is_set():
                logger.exception("扫描出错")
                self.scan_error.emit(str(e))

    def _scan_dir(self, path: str, depth: int) -> list:
        if self._cancel_event.is_set():
            return []
        if depth > MAX_DEPTH:
            logger.warning("超过最大递归深度 %d, 跳过: %s", MAX_DEPTH, path)
            return []

        self.scan_progress.emit(path)
        all_files = []
        page = 1

        while page <= MAX_PAGES and not self._cancel_event.is_set():
            data = self.client.list_files(path, page=page, per_page=PER_PAGE)
            content = data.get("content") or []
            if not content:
                logger.debug("目录 %s 第 %d 页无内容, 停止", path, page)
                break

            logger.debug("目录 %s 第 %d 页返回 %d 项", path, page, len(content))

            for item in content:
                if self._cancel_event.is_set():
                    return all_files
                name = item.get("name", "")
                item_path = f"{path.rstrip('/')}/{name}"
                is_dir = item.get("is_dir", False)

                if is_dir:
                    if not self.recursive:
                        continue
                    if depth >= self.max_depth:
                        logger.warning("超过用户设定递归深度 %d, 跳过: %s", self.max_depth, item_path)
                        continue
                    sub_files = self._scan_dir(item_path, depth + 1)
                    all_files.extend(sub_files)
                else:
                    self.total_scanned += 1
                    if self.suffixes and not self._match_suffix(name):
                        continue
                    fi = FileInfo(
                        name=name,
                        path=item_path,
                        size=item.get("size", 0),
                        is_dir=False,
                        modified=item.get("modified", ""),
                    )
                    all_files.append(fi)

            if len(content) < PER_PAGE:
                break
            page += 1

        return all_files

    def _match_suffix(self, filename: str) -> bool:
        lower = filename.lower()
        return any(lower.endswith(s) for s in self.suffixes)
