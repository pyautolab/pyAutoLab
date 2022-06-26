"""
pyautolab plugins management.
"""
from __future__ import annotations

import inspect
import json
import pkgutil
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import import_module, machinery
from json import JSONDecodeError
from pathlib import Path
from types import ModuleType
from typing import Any

from qtpy.QtCore import QObject
from qtpy.QtWidgets import QWidget

from pyautolab.core.utils.conf import AbstractConf, Configuration
from pyautolab.core.utils.system import create_logger, get_pyautolab_data_folder_path

# Constants
PLUGIN_CONF_FILE_NAME = "configuration.json"
PLUGIN_PREFIX = "pyautolab_"
FORBIDDEN_SUFFIXES = ["dist-info", "egg.info", "egg-info", "egg-link", "kernels"]
logger = create_logger(__name__)


class Device(ABC):
    def __init__(self) -> None:
        self.port = ""
        self.baudrate = ""

    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def receive(self) -> str:
        pass

    @abstractmethod
    def send(self, message: str) -> None:
        pass

    @abstractmethod
    def reset_buffer(self) -> None:
        pass


class Controller(QObject):
    _counter = 0
    is_controllable = True

    def __init__(self) -> None:
        super().__init__()
        Controller._counter += 1
        Controller.is_controllable = True

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        Controller._counter -= 1
        if Controller._counter == 0:
            Controller.is_controllable = False


class DeviceTab(QWidget):
    def __init__(self, device: Device) -> None:
        super().__init__()
        self.device = device
        self.device_enable = True

    def get_controller(self) -> Controller | None:
        return None

    def setup_settings(self) -> None:
        return None

    def get_parameters(self) -> dict[str, str] | None:
        return None


class PluginConfig(AbstractConf):
    def __init__(self) -> None:
        super().__init__(save_file=get_pyautolab_data_folder_path() / "plugin_conf.json")

    def _get_current_settings(self) -> dict[str, Any]:
        return self.read_json(self._save_file)


@dataclass
class Plugin:
    name: str
    module_name: str
    module: ModuleType
    conf_path: Path
    enable: bool


@dataclass
class DeviceStatus:
    name: str
    device: Device
    device_properties: dict[str, Any]
    tab: DeviceTab | None
    is_connected: bool


def _get_default_plugins() -> list[Plugin]:
    plugins: list[Plugin] = []

    import pyautolab.plugins

    plugin_folder_path = Path(inspect.getfile(pyautolab.plugins)).parent
    for _, module_name, _ in pkgutil.iter_modules([str(plugin_folder_path)]):
        module_spec = machinery.PathFinder.find_spec(module_name, [str(plugin_folder_path)])
        if module_spec is None:
            continue
        protocol = module_spec.loader
        if protocol is None:
            continue
        module_exist = False
        for plugin in plugins:
            if plugin.module_name == module_name:
                module_exist = True
                break
        if module_exist:
            continue
        module = protocol.load_module(module_name)
        plugin_conf_path = Path(inspect.getfile(module)).parent / PLUGIN_CONF_FILE_NAME
        plugins.append(Plugin("", module_name, module, plugin_conf_path, True))
    return plugins


def _append_plugins_path_to_sys_path() -> None:
    # Append plugins path to sys.path
    plugins_path = get_pyautolab_data_folder_path() / "plugins"
    if not plugins_path.exists():
        plugins_path.mkdir()
    for path in plugins_path.iterdir():
        if not path.is_dir():
            continue
        if str(path) in sys.path:
            continue
        sys.path.append(str(path))


def _check_plugins(plugins: list[Plugin]) -> list[Plugin]:
    plugin_conf = PluginConfig()
    plugins_checked = []
    for plugin in plugins:
        if not plugin.conf_path.exists():
            logger.error(f"Failed to load {plugin.module_name}. There is no configuration.json")
            continue
        try:
            plugin_property = json.loads(plugin.conf_path.read_bytes())
        except JSONDecodeError as e:
            logger.error(f"Failed to load {plugin.module_name}. \n{e}")
            continue
        plugin_name: str | None = plugin_property.get("name")
        if plugin_name is None:
            logger.error(f"Failed to load {plugin.module_name}. There is no name property in {plugin.conf_path}.")
            continue
        plugin.name = plugin_name
        plugin_conf_property = plugin_conf.get(plugin_name)
        if plugin_conf_property is not None:
            plugin_enabled = plugin_conf_property.get("enable")
            if plugin_enabled is not None:
                plugin.enable = plugin_enabled
        plugins_checked.append(plugin)
    return plugins_checked


def _get_plugins() -> list[Plugin]:
    plugins = _get_default_plugins()
    _append_plugins_path_to_sys_path()
    # Import user plugins
    for _, module_name, _ in pkgutil.iter_modules():
        if not module_name.startswith(PLUGIN_PREFIX):
            continue
        if any([str(module_name).endswith(s) for s in FORBIDDEN_SUFFIXES]):
            continue
        module_exist = False
        for plugin in plugins:
            if plugin.module_name == module_name:
                module_exist = True
                break
        if module_exist:
            continue
        module = import_module(module_name)
        plugin_conf_path = Path(inspect.getfile(module)).parent / PLUGIN_CONF_FILE_NAME
        plugins.append(Plugin("", module_name, module, plugin_conf_path, True))

    return _check_plugins(plugins)


def _getattr_from_specifier(entry_point_specifier: str) -> type:
    module, attr = entry_point_specifier.split(":")
    entry_module = import_module(module)
    return getattr(entry_module, attr)


def get_device_statuses(plugin: Plugin) -> list[DeviceStatus]:
    device_statuses = []
    devices = json.loads(plugin.conf_path.read_bytes()).get("device")
    if devices is None:
        return device_statuses
    for name, device_properties in devices.items():
        device_class_name = device_properties.get("class")
        if device_class_name is None:
            continue
        device = _getattr_from_specifier(device_class_name)()

        device_tab_name = device_properties.get("tabClass")
        device_tab = None if device_tab_name is None else _getattr_from_specifier(device_tab_name)(device)
        device_statuses.append(
            DeviceStatus(
                name=name,
                device=device,
                tab=device_tab,
                device_properties=device_properties,
                is_connected=False,
            )
        )
    return device_statuses


def load_plugin(plugin: Plugin, settings: Configuration) -> list[DeviceStatus]:
    settings.load_conf([plugin.conf_path])

    # Run plugin entry point
    conf_property = json.loads(plugin.conf_path.read_bytes())
    entry_point_specifier: str | None = conf_property.get("entry_point")
    if entry_point_specifier is not None:
        entry_point = _getattr_from_specifier(entry_point_specifier)
        entry_point()
    return get_device_statuses(plugin)


def load_plugins(settings: Configuration) -> tuple[list[Plugin], list[DeviceStatus]]:
    plugins = _get_plugins()
    device_statuses = []
    for plugin in plugins:
        device_statuses.extend(load_plugin(plugin, settings))

    return plugins, device_statuses


def get_plugin(plugin_name: str) -> Plugin | None:
    plugins = _get_plugins()
    for plugin in plugins:
        if plugin.name == plugin_name:
            return plugin
    return None
