from pathlib import Path
from typing import Literal

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialogButtonBox

from pyautolab.app.main_window import MainWindow
from pyautolab.core import qt


def create_window_timer(
    timeout=None, enable_count: bool = False, enable_clock: bool = False, timer_type: Qt.TimerType | None = None
):
    return qt.helper.timer(MainWindow.instance, timeout, enable_count, enable_clock, timer_type)


def alert(
    severity: Literal["error", "info", "warning"], *, text: str, buttons: QDialogButtonBox.StandardButton | None = None
) -> QDialogButtonBox.StandardButton:
    alert = qt.widgets.Alert(severity, text=text, parent=MainWindow.instance, buttons=buttons)
    return alert.open()


def show_save_dialog(
    title: str | None = None, default_path: str | Path | None = None, filter: str | None = None
) -> Path | None:
    return qt.helper.show_save_dialog(title, default_path, filter)
