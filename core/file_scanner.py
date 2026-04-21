# @author: awen

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
    scan_finished = pyqtSignal(list)
    scan_error = pyqtSignal(str)

    def __init__(self, client: OpenListClient, root_path: str,
                 suffixes: list, parent=None):
        super().__init__(parent)
        self.client = client
        self.root_path = root_path
        self.suffixes = [s.lower() for s in suffixes]
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            logger.info("开始扫描: %s (后缀过滤: %s)", self.root_path, self.suffixes or "无")
            results = self._scan_dir(self.root_path, depth=0)
            if not self._cancelled:
                logger.info("扫描完成, 共找到 %d 个文件", len(results))
                self.scan_finished.emit(results)
        except Exception as e:
            if not self._cancelled:
                logger.exception("扫描出错")
                self.scan_error.emit(str(e))

    def _scan_dir(self, path: str, depth: int) -> list:
        if self._cancelled:
            return []
        if depth > MAX_DEPTH:
            logger.warning("超过最大递归深度 %d, 跳过: %s", MAX_DEPTH, path)
            return []

        self.scan_progress.emit(path)
        all_files = []
        page = 1

        while page <= MAX_PAGES and not self._cancelled:
            data = self.client.list_files(path, page=page, per_page=PER_PAGE)
            content = data.get("content") or []
            if not content:
                logger.debug("目录 %s 第 %d 页无内容, 停止", path, page)
                break

            logger.debug("目录 %s 第 %d 页返回 %d 项", path, page, len(content))

            for item in content:
                if self._cancelled:
                    return all_files
                name = item.get("name", "")
                item_path = f"{path.rstrip('/')}/{name}"
                is_dir = item.get("is_dir", False)

                if is_dir:
                    sub_files = self._scan_dir(item_path, depth + 1)
                    all_files.extend(sub_files)
                else:
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
