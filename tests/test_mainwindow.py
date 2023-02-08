import pytest
from qtpy.QtCore import QTimer

from pyautolab.app.main_window import MainWindow


@pytest.fixture()
def mainwindow(qtbot) -> MainWindow:
    win = MainWindow()
    qtbot.add_widget(win)
    win.show()
    return win


def test_mainwindow_init(mainwindow: MainWindow) -> None:
    """Ensure the mainwindow opens without error."""
    QTimer.singleShot(2000, mainwindow.close)
