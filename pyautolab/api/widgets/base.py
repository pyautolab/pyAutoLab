from qtpy.QtWidgets import QDialog

from pyautolab.app.main_window import MainWindow


class Manager(QDialog):
    def __init__(self) -> None:
        super().__init__(parent=MainWindow.instance)
