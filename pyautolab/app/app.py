import sys
from collections import abc, defaultdict
from enum import Enum, auto
from typing import Literal

from qtpy.QtCore import QEvent, QObject  # type: ignore
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QApplication

from pyautolab.app.main_window import MainWindow
from pyautolab.core import qt
from pyautolab.core.plugin import DeviceStatus, get_plugins
from pyautolab.core.utils.conf import Configuration


class _EventListener(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Show:
            App.actions.execute("window.theme")
            App.actions.execute("window.openWelcomeTab")
        elif event.type() == QEvent.Type.Close:
            for device_status in App.device_statuses:
                if device_status.is_connected:
                    device_status.device.close()
        return super().eventFilter(watched, event)


class _Actions:
    class When(Enum):
        run = auto()
        stop = auto()

    def __init__(self) -> None:
        self._actions: dict[_Actions.When | None, dict[str, QAction]] = defaultdict(dict)
        self._whens: set[_Actions.When | None] = {None, _Actions.When.stop}

    def add(self, command: str, action: QAction, when_name: str | None = None) -> None:
        when = None if when_name is None else App.actions.When[when_name]
        if when not in self._whens:
            action.setEnabled(False)
        self._actions[when][command] = action

    def add_when(self, name: str) -> None:
        when = _Actions.When[name]
        self._whens.add(when)
        for action in self._actions[when].values():
            action.setEnabled(True)
        if when == _Actions.When.run:
            self.remove_when("stop")
        elif when == _Actions.When.stop:
            self.remove_when("run")

    def remove_when(self, name: str) -> None:
        when = _Actions.When[name]
        self._whens.remove(when)
        for action in self._actions[when].values():
            action.setEnabled(False)

    def execute(self, command: str) -> None:
        for actions in self._actions.values():
            if action := actions.get(command):
                action.trigger()
                break
        else:
            raise RuntimeError(f'Could not run command Error: This command "{command}" is not found.')


class App:
    qt_app = QApplication(sys.argv)
    window = MainWindow()

    configurations = Configuration()
    plugins = get_plugins()

    device_statuses: list[DeviceStatus] = []
    actions = _Actions()
    plugin_command_handlers: dict[str, abc.Callable[[], None]] = {}

    def __init__(self) -> None:
        App.qt_app.setApplicationName("pyAutoLab")
        self._listener = _EventListener(App.qt_app)
        App.window.installEventFilter(self._listener)

        for plugin in App.plugins:
            App.device_statuses.extend(plugin.get_device_statuses())
            for conf in plugin.get_configurations():
                App.configurations.add_conf(conf, plugin.name)

    @staticmethod
    def load_plugins() -> None:
        for plugin in App.plugins:
            plugin.load()

        plugin_commands = {command for plugin in App.plugins for command in plugin.get_commands()}
        for command in sorted(plugin_commands, key=lambda command: command.title):
            handler = App.plugin_command_handlers[command.command]
            App.register_action(
                command.command,
                command.title,
                command.icon,
                handler,
                command.icon_color,
                command.menubar,
                command.show_on_toolbar,
                command.when,
            )

    @staticmethod
    def register_action(
        command: str,
        title: str,
        icon: str | None,
        handler: abc.Callable[[], None],
        icon_color: str | None = None,
        menubar: Literal["File", "Run", "Tool", "Plugin", "Help"] | None = None,
        show_on_toolbar=False,
        when: Literal["run", "stop"] | None = None,
        plugin_name: str | None = None,
    ) -> None:
        action = qt.helper.action(App.qt_app, title, icon, icon_color, triggered=handler)
        App.actions.add(command, action, when)
        if show_on_toolbar:
            App.window.toolbar.addAction(action)

        if menubar == "File":
            App.window.menubar.file.addAction(action)
        if menubar == "Help":
            App.window.menubar.help.addAction(action)
        elif menubar == "Run":
            App.window.menubar.run.addAction(action)
        elif menubar == "Tool":
            App.window.menubar.tool.addAction(action)
        elif menubar == "Plugin" and plugin_name is not None:
            menu = App.window.menubar.plugin.addMenu(plugin_name)
            menu.addAction(action)
