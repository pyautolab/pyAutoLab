import pyqtgraph as pg
import qdarktheme
from qtpy.QtWidgets import QDialogButtonBox

from pyautolab.app import App, tabs
from pyautolab.core import qt
from pyautolab.core.utils.conf import RunConfiguration


def _setup_theme() -> None:
    theme = App.configurations.get("system.theme")
    qdarktheme.setup_theme(theme, additional_qss="QAbstractScrollArea:!window {border: none;}")
    pg.setConfigOption("background", "k" if theme == "dark" else "w")


def _open_welcome_tab() -> None:
    if App.configurations.get("workspace.welcomeTab"):
        App.window.workspace.add_tab(tabs.WelcomeTab(), "Welcome", True)


def _open_device_manager() -> None:
    qt.widgets.DeviceManager(App.device_statuses, App.window).exec()
    for device_status in App.device_statuses:
        if device_status.tab is None:
            continue
        if device_status.is_connected:
            App.window.workspace.add_tab(device_status.tab(device_status.device), device_status.name)
        elif App.window.workspace.get_tab(device_status.name):
            App.window.workspace.remove_tab(device_status.name)


def _run() -> None:
    if not RunConfiguration().exists():
        result = qt.widgets.Alert(
            "warning", text="At initial startup, the Run configuration must be set.", parent=App.window
        )
        if result == QDialogButtonBox.StandardButton.Open:
            App.actions.execute("open.runConfTab")
        return

    if save_path := qt.helper.show_save_dialog(filter="CSV UTF-8 (*.csv)"):
        App.actions.add_when("run")
        App.window.workspace.add_tab(
            tabs.MeasurementTab(save_path), "Measurement", True, lambda: App.actions.execute("runner.stop")
        )


def _stop() -> None:
    if tab := App.window.workspace.get_tab("Measurement"):
        App.actions.add_when("stop")
        tab.stop()  # type: ignore


def register_default_commands() -> None:
    App.register_action("window.theme", "Setup Theme", None, _setup_theme)
    App.register_action("window.openWelcomeTab", "Welcome...", None, _open_welcome_tab, menubar="Help")
    App.register_action(
        "window.openDeviceManager",
        "Devices...",
        "msc.debug-disconnect",
        _open_device_manager,
        menubar="File",
        show_on_toolbar=True,
        when="stop",
    )
    App.register_action(
        "window.openPreferences",
        "Preferences...",
        "fa.cog",
        lambda: App.window.workspace.add_tab(tabs.SettingsTab(App.window, App.configurations), "Settings", True),
        menubar="File",
    )
    App.register_action(
        "window.openPluginManager",
        "Plugins...",
        "msc.extensions",
        lambda: App.window.workspace.add_tab(tabs.PluginManager(App.plugins), "Plugin Manager", True),
        menubar="File",
    )
    App.register_action(
        "runner.run",
        "Run",
        "ph.play",
        _run,
        icon_color="green",
        menubar="Run",
        show_on_toolbar=True,
        when="stop",
    )
    App.register_action(
        "runner.stop",
        "Stop",
        "ph.stop",
        _stop,
        icon_color="red",
        show_on_toolbar=True,
        menubar="Run",
        when="run",
    )
    App.register_action(
        "window.openRunConfiguration",
        "Run Configuration...",
        "fa.cog",
        lambda: App.window.workspace.add_tab(tabs.RunConfTab(), "Run Configuration", True),
        menubar="Run",
    )
    App.register_action(
        "monitor.openCommunicationMonitor",
        "Communication monitor...",
        "mdi6.monitor",
        lambda: App.window.workspace.add_tab(tabs.CommunicationMonitor(), "Communication monitor", True),
        menubar="Tool",
    )
