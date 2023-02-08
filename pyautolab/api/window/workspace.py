from collections.abc import Callable

from qtpy.QtWidgets import QWidget

from pyautolab.app.main_window import MainWindow
from pyautolab.core.plugin.device import DeviceTab


def add_tab(
    tab: QWidget,
    name: str,
    enable_remove_button: bool = False,
    on_closed: Callable[[], None] | None = None,
) -> None:
    MainWindow.workspace.add_tab(tab, name, enable_remove_button, on_closed)


def get_tab(name: str) -> QWidget | DeviceTab | None:
    return MainWindow.workspace.get_tab(name)
