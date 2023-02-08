"""Pyautolab plugin manager."""
import inspect
import json
import pkgutil
from dataclasses import dataclass
from importlib import import_module, machinery
from json import JSONDecodeError
from pathlib import Path
from types import ModuleType
from typing import Any, Literal

from pyautolab.core.plugin.device import DeviceStatus
from pyautolab.core.utils.conf import AbstractConf, ConfProps

# Constants
PLUGIN_CONF_FILE_NAME = "configuration.json"
PLUGIN_PREFIX = "pyautolab_"
FORBIDDEN_SUFFIXES = ("dist-info", "egg.info", "egg-info", "egg-link", "kernels")


@dataclass(unsafe_hash=True, frozen=True)
class _Command:
    plugin_name: str
    command: str
    title: str
    icon: str
    icon_color: str | None
    menubar: Literal["Plugin"]
    show_on_toolbar: bool
    when: Literal["run", "stop"] | None


class _Plugin_Exception(Exception):
    """This error raise when a plugin is broken."""


class _PluginConfig(AbstractConf):
    def __init__(self) -> None:
        super().__init__(id="plugin_conf")

    def _get_current_settings(self) -> dict[str, Any]:
        return self.read_json(self._save_file)


class Plugin:
    _user_conf = _PluginConfig()

    def __init__(self, module: ModuleType, module_name: str, internal=False) -> None:
        self.module_name = module_name
        self._internal = internal
        self._conf_path = Path(inspect.getfile(module)).parent / PLUGIN_CONF_FILE_NAME
        self.name: str = self._conf["name"]
        self.description: str | None = self._conf.get("description")

        self.commands = self.get_commands()

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Plugin):
            return False
        return self.module_name == __o.module_name

    def _get_user_conf(self) -> dict:
        conf = Plugin._user_conf.get(self.name)
        if conf is None:
            return {}
        return conf

    @property
    def enable(self) -> bool:
        conf = self._get_user_conf()
        enable = conf.get("enable")
        if enable is None:
            return True
        return enable

    @enable.setter
    def enable(self, enable: bool) -> None:
        conf = self._get_user_conf()
        conf["enable"] = enable
        Plugin._user_conf.add(self.name, enable)

    @property
    def _conf(self) -> dict:
        try:
            return json.loads(self._conf_path.read_bytes())
        except JSONDecodeError as e:
            raise _Plugin_Exception(f"Failed to load {self.module_name}. \n{e}")

    @property
    def is_internal(self) -> bool:
        return self._internal

    def _check(self) -> None:
        if not self._conf_path.exists():
            raise _Plugin_Exception(f"Failed to load {self.module_name}. There is no configuration.json")
        plugin_name = self._conf.get("name")
        if plugin_name is None:
            raise _Plugin_Exception(
                f"Failed to load {self.module_name}. There is no name property in {self._conf_path}."
            )

    @staticmethod
    def _getattr_from_specifier(entry_point_specifier: str) -> type:
        module, attr = entry_point_specifier.split(":")
        entry_module = import_module(module)
        return getattr(entry_module, attr)

    def get_device_statuses(self) -> list[DeviceStatus]:
        if (devices := self._conf.get("device")) is None:
            return []
        device_statuses = []
        for name, device_conf in devices.items():
            device_class_name = device_conf.get("class")
            if device_class_name is None:
                continue
            device = Plugin._getattr_from_specifier(device_class_name)()
            device_tab_name = device_conf.get("tabClass")

            device_statuses.append(
                DeviceStatus(
                    name,
                    device,
                    tab=None if device_tab_name is None else Plugin._getattr_from_specifier(device_tab_name),
                    device_properties=device_conf,
                    is_connected=False,
                )
            )
        return device_statuses

    def get_commands(self) -> list[_Command]:
        command_infos = self._conf.get("commands")
        if command_infos is None:
            return []
        return [
            _Command(
                self.name,
                info["command"],
                info["title"],
                info["icon"],
                info.get("iconColor"),
                "Plugin",
                info.get("showOnToolbar", False),
                info.get("when"),
            )
            for info in command_infos
        ]

    def get_configurations(self) -> list[ConfProps]:
        configs: dict[str, dict] | None = json.loads(self._conf_path.read_text()).get("configuration")
        if configs is None:
            return []
        return [
            ConfProps(
                title,
                dict_config["description"],
                dict_config["type"],
                dict_config["default"],
                dict_config.get("minimum"),
                dict_config.get("maximum"),
                dict_config.get("enum"),
            )
            for title, dict_config in configs.items()
        ]

    def load(self) -> None:
        entry_point_specifier = self._conf.get("entry_point")
        if entry_point_specifier is not None:
            entry_point = Plugin._getattr_from_specifier(entry_point_specifier)
            entry_point()


def _get_default_plugins() -> list[Plugin]:
    import pyautolab.plugins

    plugins: list[Plugin] = []
    plugin_folder_path = Path(inspect.getfile(pyautolab.plugins)).parent
    for _, module_name, _ in pkgutil.iter_modules([str(plugin_folder_path)]):
        module_spec = machinery.PathFinder.find_spec(module_name, [str(plugin_folder_path)])
        if module_spec and (protocol := module_spec.loader):
            module = protocol.load_module(module_name)
            if (plugin := Plugin(module, module_name, True)) not in plugins:
                plugins.append(plugin)
    return plugins


def _get_third_party_plugins() -> list[Plugin]:
    plugins: list[Plugin] = []
    # Import user plugins
    for _, module_name, _ in pkgutil.iter_modules():
        if not module_name.startswith(PLUGIN_PREFIX):
            continue
        if any(module_name.endswith(s) for s in FORBIDDEN_SUFFIXES):
            continue

        module = import_module(module_name)
        if (plugin := Plugin(module, module_name)) not in plugins:
            plugins.append(plugin)
    return plugins


def get_plugins() -> tuple[Plugin]:
    return tuple(_get_default_plugins() + _get_third_party_plugins())
