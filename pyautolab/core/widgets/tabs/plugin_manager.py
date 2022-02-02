from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from queue import Queue
from sys import executable as python
from tempfile import TemporaryDirectory
from time import sleep

import qtawesome as qta
from qtpy.QtCore import QObject, QThread, Signal, Slot  # type: ignore
from qtpy.QtWidgets import QFormLayout, QFrame, QLabel, QLineEdit, QMessageBox, QScrollArea, QTextEdit, QWidget
from typing_extensions import Literal

from pyautolab.core.utils.conf import Configuration
from pyautolab.core.utils.plugin_helpers import (
    DeviceStatus,
    Plugin,
    PluginConfig,
    get_device_statuses,
    get_plugin,
    load_plugin,
)
from pyautolab.core.utils.qt_helpers import create_h_box_layout, create_push_button, create_v_box_layout
from pyautolab.core.widgets.status import StatusBar, StatusBarWidget


class _PluginWidget(QFrame):
    def __init__(self, plugin: Plugin, console: QTextEdit, parent: PluginManager) -> None:
        super().__init__(parent=parent)
        self._plugin = plugin
        self._p_btn_uninstall = create_push_button(clicked=self._uninstall, text="Uninstall")
        self._p_btn_state = create_push_button(
            clicked=self._change_state, text="Enable" if plugin.enable else "Disable"
        )
        self._plugin_conf = PluginConfig()
        self._console = console
        self._parent = parent
        self._setup_ui()

    def _setup_ui(self) -> None:
        plugin_property = json.loads(self._plugin.conf_path.read_bytes())
        description = plugin_property.get("description")
        f_layout = QFormLayout(self)
        f_layout.addRow(QLabel(f"<h4>{self._plugin.name}</h4>"))
        if description is not None:
            f_layout.addRow(QLabel(description))
        f_layout.addRow(self._p_btn_state, self._p_btn_uninstall)

    @Slot()  # type: ignore
    def _uninstall(self) -> None:
        plugin_property = self._plugin_conf.get(self._plugin.name)
        if plugin_property is None:
            self._console.setText(f"Cannot uninstall {self._plugin.name}")
            return
        plugin_path = plugin_property.get("plugin_path")
        if plugin_path is None:
            self._console.setText(f"Cannot uninstall {self._plugin.name}")
            return
        self._parent._plugins.remove(self._plugin)

        device_statuses = get_device_statuses(self._plugin)
        for device_status in self._parent._device_statuses:
            for current_device_status in device_statuses:
                if device_status.name == current_device_status.name:
                    self._parent._device_statuses.remove(device_status)

        shutil.rmtree(plugin_path)
        self._console.setText(f"Uninstalled {self._plugin.name} successfully!")
        self.hide()

    def _change_state(self) -> None:
        state: str = self.sender().text()  # type: ignore
        plugin_property = self._plugin_conf.get(self._plugin.name)
        if plugin_property is None:
            plugin_property = {}
        plugin_property["enable"] = state == "Enable"
        self._plugin.enable = state == "Enable"
        self._p_btn_state.setText("Disable" if state == "Enable" else "Enable")


class _InstallWorker(QObject):
    sig_printed = Signal(str)
    sig_succeeded = Signal(str, Path)
    sig_finished = Signal()
    sig_installed = Signal(str)
    sig_launched_messagebox = Signal(str, str)

    def __init__(self, save_plugins_path: Path) -> None:
        super().__init__()
        self._save_plugins_path = save_plugins_path
        self._is_restart = None
        self.queue = Queue()

    def start(self) -> None:
        # Signal
        self.sig_installed.connect(self._install)

    def _pip_install(self, command: str, target: Path) -> None:
        MEI_PASS = getattr(sys, "_MEIPASS", None)
        if MEI_PASS is None:
            pip_command = [python, "-m", "pip", "install"] + command.split() + ["-t", str(target)]
        else:
            root_path = Path(MEI_PASS)
            pip = root_path / "plugin-installer"
            pip_command = [str(pip), "install"] + command.split() + ["-t", str(target)]
        result = subprocess.check_output(pip_command, stderr=subprocess.STDOUT, encoding="utf-8")
        self.sig_printed.emit(result)

    def _get_configuration_file(self, parent: Path) -> Path | None:
        for path in parent.iterdir():
            if not path.is_dir():
                continue
            for file in path.iterdir():
                if file.name == "configuration.json":
                    return file
        return None

    @Slot(str)  # type: ignore
    def _install(self, command: str) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            try:
                self._pip_install(command, temp_dir_path)
            except subprocess.CalledProcessError as e:
                self.sig_printed.emit(str(e))
                self.sig_finished.emit()
                return

            plugin_conf_path = self._get_configuration_file(temp_dir_path)
            if plugin_conf_path is None:
                self.sig_printed.emit("There is not plugin configuration file. \nFailed to install plugin.")
                self.sig_finished.emit()
                return

            plugin_property = json.loads(plugin_conf_path.read_bytes())
            plugin_name: str | None = plugin_property.get("name")
            if plugin_name is None:
                self.sig_printed.emit(f"There is no name property in {plugin_conf_path}. \nFailed to install plugin.")
                self.sig_finished.emit()
                return

            plugin_path = self._save_plugins_path / plugin_name.replace(" ", "-")
            if plugin_path.exists():
                self.sig_launched_messagebox.emit("warning", command)
                is_continue = self.queue.get()
                if not is_continue:
                    self.sig_finished.emit()
                    return
            shutil.rmtree(plugin_path, ignore_errors=True)
            shutil.copytree(temp_dir, plugin_path)
        self.sig_printed.emit(f"\n Installed {plugin_name} successfully!")
        self.sig_succeeded.emit(plugin_name, plugin_path)


class PluginManager(QWidget):
    def __init__(
        self,
        status_bar: StatusBar,
        save_path: Path,
        plugins: list[Plugin],
        device_statuses: list[DeviceStatus],
        settings: Configuration,
    ) -> None:
        super().__init__()
        self._ui = _UI()
        self._status_bar = status_bar
        self._ui.setup_ui(self)

        self._save_plugins_path = save_path
        self._plugin_conf = PluginConfig()
        self._plugins = plugins
        self._device_statuses = device_statuses
        self._settings = settings

        # Thread
        self._install_thread = QThread()
        self._install_worker = _InstallWorker(save_path)

        self._setup()

    def __del__(self):
        self._install_thread.quit()
        self._install_thread.wait()
        sleep(1)

    def _setup(self) -> None:
        # Signal
        self._ui.lineedit_plugin.returnPressed.connect(self._start_install)
        self._install_worker.sig_printed.connect(self._ui.console.append)
        self._install_worker.sig_launched_messagebox.connect(self._launch_messagebox)
        self._install_worker.sig_succeeded.connect(self._load_new_plugin)
        self._install_worker.sig_finished.connect(self._finish_installation)

        for plugin_widget in self._create_plugin_widgets():
            self._ui.dynamic_v_layout.addWidget(plugin_widget)
        self._ui.dynamic_v_layout.addStretch()

        # Thread
        self._install_worker.moveToThread(self._install_thread)
        self._install_thread.started.connect(self._install_worker.start)
        self._install_thread.finished.connect(self._install_worker.deleteLater)
        self._install_thread.start()

    def _create_plugin_widgets(self) -> list[_PluginWidget]:
        plugin_widgets = []
        for plugin in self._plugins:
            if "pyautolab" not in plugin.module_name:
                continue
            plugin_widgets.append(_PluginWidget(plugin, self._ui.console, self))
        return plugin_widgets

    def _refresh_plugin_widgets(self) -> None:
        plugin_widgets = self._create_plugin_widgets()
        self._ui.dynamic_v_layout = create_v_box_layout(plugin_widgets)
        widget = QWidget()
        widget.setLayout(self._ui.dynamic_v_layout)
        self._ui.scrollarea.setWidget(widget)

    @Slot()  # type: ignore
    def _start_install(self) -> None:
        self._status_bar.add_status(self._ui.spinner, self._status_bar.Align.LEFT)
        self._ui.console.clear()
        self._ui.console.append("Installing...")
        command = self._ui.lineedit_plugin.text()
        self._install_worker.sig_installed.emit(command)

    @Slot()  # type: ignore
    def _finish_installation(self) -> None:
        self._status_bar.remove_status(self._ui.spinner)

    @Slot(str, str)  # type: ignore
    def _launch_messagebox(self, message_type: Literal["warning"], command: str) -> None:
        if message_type == "warning":
            result = QMessageBox.warning(
                self,
                f"{command} is already installed.",
                "Do you want to continue the installation?",
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.Cancel,
            )
            is_continue = True
            if result == QMessageBox.StandardButton.Cancel:
                self._ui.console.append("The installation has been canceled.")
                is_continue = False
            self._install_worker.queue.put(is_continue)

    @Slot(str)  # type: ignore
    def _load_new_plugin(self, plugin_name: str, plugin_path: Path) -> None:
        plugin_conf_property: dict | None = self._plugin_conf.get(plugin_name)
        if plugin_conf_property is None:
            plugin_conf_property = {}
        plugin_conf_property["plugin_path"] = str(plugin_path)
        self._plugin_conf.add(plugin_name, plugin_conf_property)

        for plugin in self._plugins:
            if plugin.name == plugin_name:
                self._plugins.remove(plugin)

        new_plugin = get_plugin(plugin_name)
        if new_plugin is not None:
            self._plugins.append(new_plugin)
            device_statuses = load_plugin(new_plugin, self._settings)
            for device_status in self._device_statuses:
                for new_device_status in device_statuses:
                    if device_status.name == new_device_status.name:
                        self._device_statuses.remove(device_status)
            self._device_statuses.extend(device_statuses)
        self._refresh_plugin_widgets()
        self._finish_installation()


class _UI:
    def setup_ui(self, parent: PluginManager) -> None:
        # Widgets
        self.lineedit_plugin = QLineEdit()
        self.console = QTextEdit()
        self.scrollarea = QScrollArea(parent)
        self.dynamic_v_layout = create_v_box_layout([])
        self.spinner = StatusBarWidget("Install plugin", "install plugin")

        # Setup Widgets
        self.console.setReadOnly(True)
        self.console.setUndoRedoEnabled(False)
        self.console.setMinimumHeight(100)
        self.scrollarea.setWidgetResizable(True)
        self.spinner.update_icon(qta.icon("fa5s.spinner", animation=qta.Spin(self.spinner)))

        # Layout
        widget = QWidget()
        widget.setLayout(self.dynamic_v_layout)
        self.scrollarea.setWidget(widget)
        h_layout = create_h_box_layout([QLabel("pip install"), self.lineedit_plugin])
        create_v_box_layout([h_layout, self.console, self.scrollarea], parent)
