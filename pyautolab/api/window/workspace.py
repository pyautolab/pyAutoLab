from __future__ import annotations

from qtpy.QtWidgets import QWidget

from pyautolab.app.mainwindow import MainWindow
from pyautolab.core.utils.plugin_helpers import DeviceTab
from pyautolab.core.utils.qt_helpers import find_mainwindow_instance

_main_win: MainWindow | None = find_mainwindow_instance()


def add_tab(tab: QWidget, name: str, enable_remove_button: bool = False) -> None:
    if _main_win is None:
        return
    _main_win.ui.workspace.add_tab(tab, name, enable_remove_button)


def get_tab(name: str) -> QWidget | None:
    if _main_win is None:
        return None
    return _main_win.ui.workspace.get_tab(name)


def get_device_tab(name: str) -> DeviceTab | None:
    if _main_win is None:
        return None
    return _main_win.ui.workspace.get_device_tab(name)


def remove_tab(name: str) -> None:
    if _main_win is None:
        return
    _main_win.ui.workspace.remove_tab(name)
