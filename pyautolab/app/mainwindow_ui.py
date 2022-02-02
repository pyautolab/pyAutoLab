from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMainWindow, QSplitter, QToolBar

from pyautolab.core.widgets.status import StatusBar
from pyautolab.core.widgets.workspace import Workspace


class MainWindowUI:
    def setup_ui(self, win: QMainWindow) -> None:
        # member
        self.statusbar = StatusBar(win)
        self.toolbar = QToolBar(win)
        self.workspace = Workspace()
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.main_menu = win.menuBar()
        self.tool_menu = self.main_menu.addMenu("&Tools")
        self.run_menu = self.main_menu.addMenu("&Run")

        # Setup UI
        self.toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.toolbar.setMovable(False)

        # Layout
        win.addToolBar(self.toolbar)
        self.h_splitter.addWidget(self.workspace)
        win.setCentralWidget(self.h_splitter)
