# @author: awen

import json
import os
import subprocess

import requests

from config import REQUEST_TIMEOUT
from utils.logger import logger


class Aria2RPC:
    def __init__(self, rpc_url: str = "http://localhost:6800/jsonrpc", secret: str = ""):
        self.rpc_url = rpc_url
        self.secret = secret
        self._id = "openlist_downloader"

    def _call(self, method: str, params: list = None) -> dict:
        if params is None:
            params = []
        rpc_params = []
        if self.secret:
            rpc_params.append(f"token:{self.secret}")
        rpc_params.extend(params)

        payload = {
            "jsonrpc": "2.0",
            "id": self._id,
            "method": method,
            "params": rpc_params,
        }
        resp = requests.post(self.rpc_url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"aria2 RPC 错误: {data['error'].get('message', '')}")
        return data.get("result")

    def verify_connection(self) -> tuple:
        try:
            result = self._call("aria2.getVersion")
            version = result.get("version", "未知")
            return True, version
        except Exception as e:
            return False, str(e)

    def add_download(self, url: str, save_dir: str,
                     filename: str = "", headers: dict = None) -> str:
        options = {"dir": save_dir}
        if filename:
            options["out"] = filename
        if headers:
            options["header"] = [f"{k}: {v}" for k, v in headers.items()]

        gid = self._call("aria2.addUri", [[url], options])
        return gid

    def add_batch_downloads(self, tasks: list) -> list:
        gids = []
        for task in tasks:
            gid = self.add_download(
                url=task["url"],
                save_dir=task.get("save_dir", ""),
                filename=task.get("filename", ""),
                headers=task.get("headers"),
            )
            gids.append(gid)
        return gids

    def _parse_status(self, result: dict) -> dict:
        status = result.get("status", "unknown")
        total = int(result.get("totalLength", 0))
        completed = int(result.get("completedLength", 0))
        speed = int(result.get("downloadSpeed", 0))
        progress = int(completed / total * 100) if total > 0 else 0
        return {
            "gid": result.get("gid", ""),
            "status": status,
            "total_length": total,
            "completed_length": completed,
            "speed": speed,
            "progress": progress,
            "error_code": result.get("errorCode", ""),
            "error_message": result.get("errorMessage", ""),
        }

    def get_download_status(self, gid: str) -> dict:
        keys = [
            "gid", "status", "totalLength", "completedLength",
            "downloadSpeed", "errorCode", "errorMessage", "files",
        ]
        result = self._call("aria2.tellStatus", [gid, keys])
        return self._parse_status(result)

    def get_active_downloads(self) -> list[dict]:
        keys = [
            "gid", "status", "totalLength", "completedLength",
            "downloadSpeed", "errorCode", "errorMessage", "files",
        ]
        results = self._call("aria2.tellActive", [keys])
        return [self._parse_status(r) for r in results]

    def get_stopped_downloads(self, offset: int = 0, count: int = 100) -> list[dict]:
        keys = [
            "gid", "status", "totalLength", "completedLength",
            "downloadSpeed", "errorCode", "errorMessage", "files",
        ]
        results = self._call("aria2.tellStopped", [offset, count, keys])
        return [self._parse_status(r) for r in results]

    def pause_download(self, gid: str):
        self._call("aria2.pause", [gid])

    def resume_download(self, gid: str):
        self._call("aria2.unpause", [gid])

    def pause_all(self):
        self._call("aria2.pauseAll")

    def resume_all(self):
        self._call("aria2.unpauseAll")

    def remove_download(self, gid: str):
        self._call("aria2.remove", [gid])

    def force_remove_download(self, gid: str):
        self._call("aria2.forceRemove", [gid])

    @staticmethod
    def check_aria2_binary(aria2_path: str) -> tuple:
        if not aria2_path:
            return False, "aria2 路径为空"
        if not os.path.isfile(aria2_path):
            return False, f"文件不存在: {aria2_path}"
        if not os.access(aria2_path, os.X_OK) and aria2_path.endswith(".exe"):
            return True, "文件存在"
        return True, "文件存在"

    @staticmethod
    def start_aria2(aria2_path: str, rpc_port: int = 6800,
                    secret: str = "", save_dir: str = "") -> subprocess.Popen:
        cmd = [
            aria2_path,
            "--enable-rpc",
            f"--rpc-listen-port={rpc_port}",
            "--continue=true",
            "--max-concurrent-downloads=5",
            "--split=5",
            "--max-connection-per-server=5",
        ]
        if secret:
            cmd.append(f"--rpc-secret={secret}")
        if save_dir:
            cmd.append(f"--dir={save_dir}")

        logger.info("启动 aria2: %s", " ".join(
            arg if not arg.startswith("--rpc-secret=") else "--rpc-secret=***"
            for arg in cmd
        ))
        proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
        return proc
