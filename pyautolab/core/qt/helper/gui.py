import qtawesome as qta
from qtpy.QtCore import QEventLoop, QObject, Qt, QTimer
from qtpy.QtGui import QAction, QIcon, QKeySequence
from qtpy.QtWidgets import QApplication, QStyle

from pyautolab.core.qt.widgets.timer import AutoLabTimer

STANDARD_PIXMAP_NAMES = sorted(attr for attr in dir(QStyle.StandardPixmap) if attr.startswith("SP_"))


def _icon(id: str, color: str | None = None) -> QIcon:
    if hasattr(QStyle.StandardPixmap, id):
        return QApplication.instance().style().standardIcon(getattr(QStyle.StandardPixmap, id))  # type: ignore
    return qta.icon(id, color=color)


def action(
    parent: QObject,
    text: str = "",
    icon: QIcon | str | None = None,
    icon_color: str | None = None,
    toggled=None,
    triggered=None,
    name: str | None = None,
    shortcut: str | None = None,
    is_checked: bool = False,
    is_checkable: bool = False,
    enable: bool = True,
    menu_role: QAction.MenuRole | None = None,
) -> QAction:
    action = QAction(parent)
    action.setText(text)
    if triggered is not None:
        action.triggered.connect(triggered)  # type: ignore
    if toggled is not None:
        action.toggled.connect(toggled)  # type: ignore
        action.setCheckable(True)
    if icon is not None:
        if isinstance(icon, str):
            action.setIcon(_icon(icon, icon_color))
        else:
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


def timer(
    parent: QObject | None = None,
    timeout=None,
    enable_count: bool = False,
    enable_clock: bool = False,
    timer_type: Qt.TimerType | None = None,
):
    timer = AutoLabTimer(parent, enable_count, enable_clock)
    if timeout is not None:
        timer.timeout.connect(timeout)  # type: ignore
    if timer_type is not None:
        timer.setTimerType(timer_type)
    return timer


def sleep_non_block_window(msec: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(msec, loop.quit)
    loop.exec()
