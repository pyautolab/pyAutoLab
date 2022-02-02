from __future__ import annotations

from qtpy.QtGui import QAction

from pyautolab.app.mainwindow import MainWindow
from pyautolab.core.utils.qt_helpers import find_mainwindow_instance

_main_win: MainWindow | None = find_mainwindow_instance()


def add_action_to_tool_menu(action: QAction) -> None:
    if _main_win is not None:
        _main_win.ui.tool_menu.addAction(action)


def add_action_to_run_menu(action: QAction) -> None:
    if _main_win is not None:
        _main_win.ui.tool_menu.addAction(action)
