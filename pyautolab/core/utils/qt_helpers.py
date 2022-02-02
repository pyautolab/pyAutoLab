from __future__ import annotations

import functools

from qtpy.QtCore import QEventLoop, QObject, QSize, Qt, QTimer
from qtpy.QtGui import QAction, QCursor, QIcon, QKeySequence
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from typing_extensions import Literal

from pyautolab.core.widgets.combobox import FlexiblePopupCombobox
from pyautolab.core.widgets.timer import AutoLabTimer


def add_unit(widget: QWidget, text: str) -> QWidget:
    h_layout = QHBoxLayout()
    h_layout.addWidget(widget)
    h_layout.addWidget(QLabel(text))
    widget_with_label = QWidget()
    widget_with_label.setLayout(h_layout)
    h_layout.setContentsMargins(0, 0, 0, 0)
    return widget_with_label


def create_action(
    parent: QObject,
    text: str = "",
    icon: QIcon = None,
    toggled=None,
    triggered=None,
    name: str = None,
    shortcut: str = None,
    is_checked: bool = False,
    is_checkable: bool = False,
    enable: bool = True,
    menu_role: QAction.MenuRole = None,
) -> QAction:
    action = QAction(parent)
    action.setText(text)
    if triggered is not None:
        action.triggered.connect(triggered)
    if toggled is not None:
        action.toggled.connect(toggled)
        action.setCheckable(True)
    if icon is not None:
        action.setIcon(icon)
    if name is not None:
        action.setObjectName(name)
    if shortcut is not None:
        action.setShortcut(QKeySequence(shortcut))
    if menu_role is not None:
        action.setMenuRole(menu_role)
    action.setChecked(is_checked)
    action.setCheckable(is_checkable)
    action.setEnabled(enable)
    return action


def create_combobox(parent: QWidget = None) -> QComboBox:
    return FlexiblePopupCombobox(parent=parent)


def create_push_button(
    clicked=None,
    fixed_width: int = None,
    fixed_height: int = None,
    icon: QIcon = None,
    text: str = "",
    toggled=None,
    object_name: str = None,
):
    button = QPushButton()
    button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    button.setText(text)
    if clicked is not None:
        button.clicked.connect(clicked)
    if fixed_height is not None:
        button.setFixedHeight(fixed_height)
    if fixed_width is not None:
        button.setFixedWidth(fixed_width)
    if icon is not None:
        button.setIcon(icon)
    if toggled is not None:
        button.toggled.connect(None)
        button.setCheckable(True)
    if object_name is not None:
        button.setObjectName(object_name)
    return button


def create_timer(
    parent=None,
    timeout=None,
    enable_count: bool = False,
    enable_clock: bool = False,
    timer_type: Qt.TimerType = None,
):
    timer = AutoLabTimer(parent, enable_count, enable_clock)
    if timeout is not None:
        timer.timeout.connect(timeout)
    if timer_type is not None:
        timer.setTimerType(timer_type)
    return timer


def create_tool_button(
    arrow_type: Qt.ArrowType = None,
    fixed_height: int = None,
    fixed_width: int = None,
    icon: QIcon = None,
    icon_size: QSize = None,
    is_text_beside_icon: bool = False,
    text: str = "",
    toggled=None,
    triggered=None,
    clicked=None,
    pressed=None,
    released=None,
    object_name: str = None,
):
    button = QToolButton()
    button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    button.setText(text)
    if arrow_type is not None:
        button.setArrowType(arrow_type)
    if fixed_height is not None:
        button.setFixedHeight(fixed_height)
    if fixed_width is not None:
        button.setFixedWidth(fixed_width)
    if icon is not None:
        button.setIcon(icon)
    if icon_size is not None:
        button.setIconSize(icon_size)
    if is_text_beside_icon:
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    if toggled is not None:
        button.toggled.connect(toggled)
        button.setCheckable(True)
    if clicked is not None:
        button.clicked.connect(clicked)
    if triggered is not None:
        button.triggered.connect(triggered)
    if pressed is not None:
        button.pressed.connect(pressed)
    if released is not None:
        button.released.connect(released)
    if object_name is not None:
        button.setObjectName(object_name)
    return button


def create_v_box_layout(contents: list[QWidget | QLayout], parent: QWidget = None) -> QVBoxLayout:
    v_layout = QVBoxLayout() if parent is None else QVBoxLayout(parent)
    for content in contents:
        if isinstance(content, QWidget):
            v_layout.addWidget(content)
        else:
            v_layout.addLayout(content)
    return v_layout


def create_h_box_layout(contents: list[QWidget | QLayout], parent: QWidget = None) -> QHBoxLayout:
    h_layout = QHBoxLayout() if parent is None else QHBoxLayout(parent)
    for content in contents:
        if isinstance(content, QWidget):
            h_layout.addWidget(content)
        else:
            h_layout.addLayout(content)
    return h_layout


def popup_exception_message(
    parent: QWidget = None,
    exception: type[Exception] = Exception,
    message_type: Literal["warning", "critical"] = "critical",
):
    def _popup_exception_message(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except exception as e:
                if message_type == "warning":
                    QMessageBox.warning(
                        parent,  # type: ignore
                        "Internal Error",
                        str(e),
                        QMessageBox.StandardButton.Yes,
                        QMessageBox.StandardButton.No,
                    )
                else:
                    QMessageBox.critical(parent, "Internal Error", str(e))  # type: ignore

        return wrapper

    return _popup_exception_message


def reconnect_slot(signal, new_slot, old_slot=None) -> None:
    if old_slot is not None:
        signal.disconnect(old_slot)
    else:
        signal.disconnect()
    signal.connect(new_slot)


def sleep_nonblock_window(msec: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(msec, loop.quit)
    loop.exec()


def find_mainwindow_instance() -> QMainWindow:
    # Find the (open) QMainWindow in application
    app: QApplication = QApplication.instance()  # type: ignore
    if app is None:
        raise RuntimeError("Application instance is not found.")
    for widget in app.topLevelWidgets():
        if isinstance(widget, QMainWindow):
            return widget
    raise RuntimeError("Mainwindow instance is not found.")
