from __future__ import annotations

import logging
import platform
from pathlib import Path

import psutil
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo


def physics_mem_usage() -> float:
    """
    Return physical memory usage (float)
    Requires the cross-platform psutil (>=v0.3) library
    (https://github.com/giampaolo/psutil)
    """
    return psutil.virtual_memory().percent


def cpu_usage():
    """
    Return CPU usage (float)
    Requires the cross-platform psutil (>=v0.3) library
    (https://github.com/giampaolo/psutil)
    """
    return psutil.cpu_percent(interval=0)


def search_ports(filter: str) -> list[ListPortInfo]:
    return [port for port in list_ports.comports() if filter in str(port.description)]


def get_pyautolab_data_folder_path() -> Path:
    os = platform.system()
    root_folder_name = "pyautolab" if os == "Linux" else ".pyautolab"
    data_folder_path = Path.home() / root_folder_name
    if not data_folder_path.exists():
        data_folder_path.mkdir()
    return Path.home() / root_folder_name


def create_logger(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.propagate = False
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(name)s] [%(levelname)s] %(message)s"))
    logger.addHandler(ch)
    return logger
