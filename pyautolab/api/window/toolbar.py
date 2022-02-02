from __future__ import annotations

from qtpy.QtGui import QAction
from qtpy.QtWidgets import QWidget

from pyautolab.app.mainwindow import MainWindow
from pyautolab.core.utils.qt_helpers import find_mainwindow_instance

_main_win: MainWindow | None = find_mainwindow_instance()


def add_action(action: QAction) -> None:
    if _main_win is not None:
        _main_win.ui.toolbar.addAction(action)


def add_widget(widget: QWidget) -> None:
    if _main_win is not None:
        _main_win.ui.toolbar.addWidget(widget)
