import functools
from pathlib import Path
from typing import Literal

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QCursor, QIcon
from qtpy.QtWidgets import QApplication, QComboBox, QFileDialog, QMainWindow, QPushButton, QToolButton, QWidget

from pyautolab.core.qt import widgets
from pyautolab.core.qt.helper.layout import layout


def add_unit(widget: QWidget, text: str) -> QWidget:
    widget_with_label = QWidget()
    layout([widget, text], parent=widget_with_label).setContentsMargins(0, 0, 0, 0)
    return widget_with_label


def combobox(parent: QWidget | None = None) -> QComboBox:
    return widgets.FlexiblePopupCombobox(parent=parent)


def push_button(
    clicked=None,
    fixed_width: int | None = None,
    fixed_height: int | None = None,
    icon: QIcon | None = None,
    text: str = "",
    toggled=None,
    object_name: str | None = None,
):
    button = QPushButton()
    button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    button.setText(text)
    if clicked is not None:
        button.clicked.connect(clicked)  # type: ignore
    if fixed_height is not None:
        button.setFixedHeight(fixed_height)
    if fixed_width is not None:
        button.setFixedWidth(fixed_width)
    if icon is not None:
        button.setIcon(icon)
    if toggled is not None:
        button.toggled.connect(None)  # type: ignore
        button.setCheckable(True)
    if object_name is not None:
        button.setObjectName(object_name)
    return button


def tool_button(
    arrow_type: Qt.ArrowType | None = None,
    fixed_height: int | None = None,
    fixed_width: int | None = None,
    icon: QIcon | None = None,
    icon_size: QSize | None = None,
    is_text_beside_icon: bool = False,
    text: str = "",
    toggled=None,
    triggered=None,
    clicked=None,
    pressed=None,
    released=None,
    object_name: str | None = None,
    parent=None,
):
    button = QToolButton(parent)
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
        button.toggled.connect(toggled)  # type: ignore
        button.setCheckable(True)
    if clicked is not None:
        button.clicked.connect(clicked)  # type: ignore
    if triggered is not None:
        button.triggered.connect(triggered)  # type: ignore
    if pressed is not None:
        button.pressed.connect(pressed)  # type: ignore
    if released is not None:
        button.released.connect(released)  # type: ignore
    if object_name is not None:
        button.setObjectName(object_name)
    return button


def _get_main_win() -> QMainWindow | None:
    app: QApplication = QApplication.instance()  # type: ignore
    if app is None:
        return None
    for widget in app.topLevelWidgets():
        if isinstance(widget, QMainWindow):
            return widget
    return None


def popup_exception(
    exception=Exception,
    severity: Literal["error", "info", "warning"] = "error",
):
    def _popup_exception(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except exception as e:
                widgets.Alert(severity, text=str(e), parent=_get_main_win()).open()

        return wrapper

    return _popup_exception


def show_save_dialog(
    title: str | None = None, default_path: str | Path | None = None, filter: str | None = None
) -> Path | None:
    if isinstance(default_path, Path):
        default_path = str(default_path)
    file_name, _ = QFileDialog.getSaveFileName(_get_main_win(), title, default_path, filter)  # type: ignore
    if file_name == "":
        return None
    return Path(file_name).absolute()
