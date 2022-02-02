import sys
from multiprocessing import freeze_support

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication

# Need to import qtawesome after importing Qt module
from pyautolab.app.mainwindow import MainWindow  # isort:skip


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
