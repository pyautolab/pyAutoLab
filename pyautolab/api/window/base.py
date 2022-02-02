from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtGui import QAction, QIcon
from qtpy.QtWidgets import QMessageBox

from pyautolab.app.mainwindow import MainWindow
from pyautolab.core.utils.qt_helpers import create_action, create_timer, find_mainwindow_instance
from pyautolab.core.widgets.timer import AutoLabTimer

_main_win: MainWindow | None = find_mainwindow_instance()


def create_window_action(
    text: str = "",
    icon: QIcon = None,
    toggled=None,
    triggered=None,
    name: str = None,
    shortcut: str = None,
    is_checked: bool = False,
    is_checkable: bool = False,
    enable: bool = True,
) -> QAction:
    return create_action(
        _main_win,
        text,
        icon,
        toggled,
        triggered,
        name,
        shortcut,
        is_checked,
        is_checkable,
        enable,
    )


def create_window_timer(
    timeout=None, enable_count: bool = False, enable_clock: bool = False, timer_type: Qt.TimerType = None
) -> AutoLabTimer:
    return create_timer(_main_win, timeout, enable_count, enable_clock, timer_type)


def show_question_message(
    title: str, text: str, buttons: QMessageBox.StandardButton = ...
) -> QMessageBox.StandardButton:
    return QMessageBox.question(_main_win, title, text, buttons=buttons)


def show_information_message(
    title: str, text: str, buttons: QMessageBox.StandardButton = ...
) -> QMessageBox.StandardButton:
    return QMessageBox.information(_main_win, title, text, buttons=buttons)


def show_warning_message(
    title: str, text: str, buttons: QMessageBox.StandardButton = ...
) -> QMessageBox.StandardButton:
    return QMessageBox.warning(_main_win, title, text, buttons)


def show_error_message(title: str, text: str, buttons: QMessageBox.StandardButton = ...) -> QMessageBox.StandardButton:
    return QMessageBox.critical(_main_win, title, text, buttons=buttons)
