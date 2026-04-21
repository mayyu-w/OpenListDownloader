# @author: awen

import logging
import os
import sys
import time
from logging.handlers import TimedRotatingFileHandler


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
RETENTION_DAYS = 90


def _clean_old_logs(log_dir: str):
    if not os.path.isdir(log_dir):
        return
    cutoff = time.time() - RETENTION_DAYS * 86400
    for f in os.listdir(log_dir):
        fp = os.path.join(log_dir, f)
        if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
            try:
                os.remove(fp)
            except OSError:
                pass


def setup_logger(name: str = "OpenListDownloader") -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.DEBUG)

    os.makedirs(LOG_DIR, exist_ok=True)
    _clean_old_logs(LOG_DIR)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    log.addHandler(console)

    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "app.log"),
        when="midnight",
        interval=1,
        backupCount=RETENTION_DAYS,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d.log"
    file_handler.namer = lambda name: name.replace("app.log.", "app-") if name.startswith("app.log.") else name
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    return log


logger = setup_logger()
