from dataclasses import dataclass

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMainWindow, QMenu, QToolBar

from pyautolab.core import qt


@dataclass
class _MenuBar:
    file: QMenu
    run: QMenu
    tool: QMenu
    plugin: QMenu
    help: QMenu


class MainWindow(QMainWindow):
    workspace: qt.widgets.Workspace
    toolbar: QToolBar
    menubar: _MenuBar
    instance: QMainWindow

    def __init__(self) -> None:
        super().__init__()
        self.ui = MainWindowUI()
        MainWindow.instance = self
        self.ui.setup_ui(self)

        self._setup()

    def _setup(self) -> None:
        self.setWindowTitle("pyAutoLab")

        # status bar
        self.ui.statusbar.add_status(qt.widgets.MemoryStatus(), self.ui.statusbar.Align.LEFT)
        self.ui.statusbar.add_status(qt.widgets.CPUStatus(), self.ui.statusbar.Align.LEFT)

        # Window size
        width = self.size().width()
        height = self.size().height()
        self.setMinimumWidth(width if 300 < width else 400)
        self.setMinimumHeight(height if 300 < height else 400)


class MainWindowUI:
    def setup_ui(self, win: MainWindow) -> None:
        # member
        self.statusbar = qt.widgets.StatusBar(win)
        MainWindow.toolbar = QToolBar(win)
        MainWindow.workspace = qt.widgets.Workspace()

        main_menu = win.menuBar()
        MainWindow.menubar = _MenuBar(
            main_menu.addMenu("&File"),
            main_menu.addMenu("&Run"),
            main_menu.addMenu("&Tool"),
            main_menu.addMenu("&Plugin"),
            main_menu.addMenu("&Help"),
        )

        # Setup UI
        MainWindow.toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        MainWindow.toolbar.setMovable(False)
        MainWindow.workspace.setStyleSheet(
            """
            .QTabWidget::pane {
                border-radius: 0;
                border-bottom: none;
                border-left: none;
                border-right: none;
            }
            .QTabWidget > QTabBar::tab {
                height: 20px;
            }
            """
        )

        # Layout
        win.addToolBar(MainWindow.toolbar)
        win.setCentralWidget(MainWindow.workspace)
