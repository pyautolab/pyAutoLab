from __future__ import annotations

from typing import Any

from pyautolab.app.mainwindow import MainWindow
from pyautolab.core.utils.plugin_helpers import DeviceStatus
from pyautolab.core.utils.qt_helpers import find_mainwindow_instance

_main_win: MainWindow = find_mainwindow_instance()  # type: ignore


def get_setting(setting_name: str) -> Any:
    if _main_win is None:
        return None
    return _main_win.settings.get(setting_name)


def get_device_status(device_name: str) -> DeviceStatus | None:
    if _main_win is not None:
        device_statuses = _main_win.device_statuses
        for device_status in device_statuses:
            if device_status.name == device_name:
                return device_status
    return None


def get_device_statuses() -> list[DeviceStatus]:
    return _main_win.device_statuses
