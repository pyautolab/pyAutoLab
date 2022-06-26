import qtawesome as qta
from qtpy.QtCore import Slot  # type: ignore
from qtpy.QtGui import QCloseEvent
from qtpy.QtWidgets import QApplication, QCheckBox, QFormLayout, QLabel, QMainWindow, QSizePolicy, QWidget

from pyautolab.app.mainwindow_ui import MainWindowUI
from pyautolab.core.utils.conf import Configuration
from pyautolab.core.utils.plugin_helpers import load_plugins
from pyautolab.core.utils.qt_helpers import create_action, create_push_button, create_v_box_layout
from pyautolab.core.utils.system import get_pyautolab_data_folder_path
from pyautolab.core.widgets.device_manager import DeviceManager
from pyautolab.core.widgets.status import CPUStatus, MemoryStatus
from pyautolab.core.widgets.tabs.plugin_manager import PluginManager
from pyautolab.core.widgets.tabs.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = MainWindowUI()
        self.ui.setup_ui(self)

        self.settings = Configuration()
        self._setup_theme()

        # action
        self.action_open_device_manager = create_action(
            self,
            text="Open Device Manager",
            icon=qta.icon("msc.debug-disconnect"),
            triggered=self.open_device_manager,
        )
        self.action_open_settings_tab = create_action(
            self,
            text="Preferences...",
            icon=qta.icon("fa.cog"),
            triggered=self._open_settings_tab,
        )
        self.action_open_plugin_manager = create_action(
            self, text="Open Plugin Manager", icon=qta.icon("msc.extensions"), triggered=self._open_plugin_manager
        )

        self._setup()

        # plugins
        self.plugins, self.device_statuses = load_plugins(self.settings)
        # Add device tab
        for device_status in self.device_statuses:
            if device_status.tab is None:
                continue
            self.ui.workspace.add_device_tab(device_status.tab, device_status.name)

    def _setup(self) -> None:
        self.setWindowTitle("pyAutoLab")
        # menubar
        main_menu = self.menuBar()
        tool_menu = main_menu.addMenu("&Tools")
        tool_menu.addAction(self.action_open_settings_tab)
        tool_menu.addAction(self.action_open_device_manager)

        # toolbar
        self.ui.toolbar.addActions(
            [self.action_open_device_manager, self.action_open_settings_tab, self.action_open_plugin_manager]
        )
        self.ui.toolbar.addSeparator()

        # status bar
        self.ui.statusbar.add_status(MemoryStatus(), self.ui.statusbar.Align.LEFT)
        self.ui.statusbar.add_status(CPUStatus(), self.ui.statusbar.Align.LEFT)

        # Add default tab
        self.ui.workspace.set_welcome_tab(WelcomeTab(self))

        # window size
        width = self.size().width()
        height = self.size().height()
        self.setMinimumWidth(width if 300 < width else 400)
        self.setMinimumHeight(height if 300 < height else 400)

    def _setup_theme(self) -> None:
        import pyqtgraph as pg
        import qdarktheme

        theme = self.settings.get("system.theme")
        if theme == "auto":
            import darkdetect

            try:
                theme = darkdetect.theme()
                if theme is None:
                    theme = "dark"
            except FileNotFoundError:
                theme = "dark"
            theme = theme.lower()

        app: QApplication = QApplication.instance()  # type: ignore
        app.setStyleSheet(qdarktheme.load_stylesheet(theme))
        app.setPalette(qdarktheme.load_palette(theme))
        pg.setConfigOption("background", "k" if theme == "dark" else "w")

    @Slot()
    def open_device_manager(self) -> None:
        DeviceManager(self.device_statuses, self).exec()
        for device_status in self.device_statuses:
            if device_status.is_connected:
                self.ui.workspace.enable_tab(device_status.name)
            else:
                self.ui.workspace.disable_tab(device_status.name)

    @Slot()
    def _open_settings_tab(self) -> None:
        settings_tab = SettingsTab(self, self.settings)
        self.ui.workspace.add_tab(settings_tab, "Settings", True)

    @Slot()
    def _open_plugin_manager(self) -> None:
        plugin_folder_path = get_pyautolab_data_folder_path() / "plugins"
        if not plugin_folder_path.exists():
            plugin_folder_path.mkdir()
        plugin_tab = PluginManager(
            self.ui.statusbar, plugin_folder_path, self.plugins, self.device_statuses, self.settings
        )
        self.ui.workspace.add_tab(plugin_tab, "Plugin Manager", True)

    def closeEvent(self, event: QCloseEvent) -> None:
        for device_status in self.device_statuses:
            if device_status.is_connected:
                device_status.device.close()
        return super().closeEvent(event)


class WelcomeTab(QWidget):
    def __init__(self, win: MainWindow) -> None:
        super().__init__()
        from pyautolab.plugins.runner.main import open_run_conf_tab, run

        # Widgets
        self._btn_open_device_manager = create_push_button(clicked=win.open_device_manager, text="Connect Device...")
        self._btn_open_run_conf = create_push_button(clicked=open_run_conf_tab, text="Open Run Configuration...")
        self._btn_start_controlling = create_push_button(clicked=run, text="Start Controlling Device...")
        self._check_box = QCheckBox("Show welcome page on startup")

        # Setup signal slot
        self._check_box.stateChanged.connect(  # type: ignore
            lambda is_checked: win.settings.add("workspace.welcomeTab", is_checked)
        )
        self._check_box.setChecked(True)

        # Setup UI
        self._btn_open_device_manager.setFlat(True)
        self._btn_open_run_conf.setFlat(True)
        self._btn_start_controlling.setFlat(True)
        for btn in {self._btn_open_device_manager, self._btn_open_run_conf, self._btn_start_controlling}:
            btn.setStyleSheet("padding-left: 1px; padding-right: 1px;")

        # Setup layout
        self._btn_open_device_manager.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._btn_open_run_conf.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._btn_start_controlling.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        f_layout = QFormLayout()
        f_layout.addRow(QLabel("<h3>Get Started</h3>"))
        f_layout.addRow("1. ", self._btn_open_device_manager)
        f_layout.addRow("2. ", QLabel("Edit the device settings in each device tab."))
        f_layout.addRow("3. ", self._btn_open_run_conf)
        f_layout.addRow("4. ", self._btn_start_controlling)

        create_v_box_layout([f_layout, self._check_box], self)
