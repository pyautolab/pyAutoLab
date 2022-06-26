import sys
from multiprocessing import freeze_support

from qtpy.QtCore import Qt  # type: ignore
from qtpy.QtWidgets import QApplication

from pyautolab.app.mainwindow import MainWindow


def main():
    freeze_support()

    app = QApplication(sys.argv)
    app.setApplicationName("pyAutoLab")
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)  # type: ignore
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
