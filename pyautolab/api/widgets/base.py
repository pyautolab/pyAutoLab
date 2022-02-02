from qtpy.QtWidgets import QDialog

from pyautolab.core.utils.qt_helpers import find_mainwindow_instance

_main_window = find_mainwindow_instance()


class Manager(QDialog):
    def __init__(self) -> None:
        super().__init__(parent=_main_window)
