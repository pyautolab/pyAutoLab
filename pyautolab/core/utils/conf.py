"""
pyautolab base configuration management
This file only deals with non-GUI configuration features
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from importlib import resources
from pathlib import Path
from typing import Any

from pyautolab.core.utils.system import get_pyautolab_data_folder_path

_USER_SETTINGS_FILE_NAME = "user_settings.json"
with resources.path("pyautolab", "default.json") as path:
    _DEFAULT_CONF_FILE_PATH = path


class AbstractConf(ABC):
    def __init__(self, save_file: Path, default_conf_file: Path = None) -> None:
        self._save_file = save_file

        if not self._save_file.exists() or not self._save_file.is_file():
            self._touch_json_file(self._save_file)

        if default_conf_file is not None:
            self._default_conf_file = default_conf_file
            if not self._default_conf_file.exists() or not self._default_conf_file.is_file():
                self._touch_json_file(self._default_conf_file)

    def add(self, setting_name: str, setting_value: Any) -> None:
        settings = json.loads(self._save_file.read_bytes())
        settings[setting_name] = setting_value
        self.to_json(self._save_file, settings)

    def get(self, setting_name: str) -> Any:
        return self._get_current_settings().get(setting_name)

    @abstractmethod
    def _get_current_settings(self) -> dict[str, Any]:
        pass

    def clear_user_settings(self) -> None:
        self.to_json(self._save_file, {})

    @staticmethod
    def _touch_json_file(file_path: str | Path) -> None:
        Path(file_path).touch()
        AbstractConf.to_json(file_path, {})

    @staticmethod
    def _get_user_conf_path() -> Path:
        """Return absolute path to the user configuration folder."""

        return get_pyautolab_data_folder_path()

    @staticmethod
    def to_json(file_path: str | Path, data: dict) -> None:
        with Path(file_path).open(mode="w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4, separators=(",", ": "))

    @staticmethod
    def read_json(file_path: str | Path) -> dict:
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            if os.stat(file_path).st_size != 0:
                raise Exception(str(e))
            AbstractConf.to_json(file_path, {})
            return AbstractConf.read_json(file_path)


class Configuration(AbstractConf):
    def __init__(self) -> None:
        super().__init__(
            default_conf_file=_DEFAULT_CONF_FILE_PATH,
            save_file=get_pyautolab_data_folder_path() / _USER_SETTINGS_FILE_NAME,
        )
        self._plugin_conf_files: list[Path] = []

        if self.get("system.defaultFolder") == "":
            user_conf_folder = get_pyautolab_data_folder_path() / "data_saved"
            user_conf_folder.mkdir()
            self.add("system.defaultFolder", str(user_conf_folder))

    def load_conf(self, conf_path: list[Path]) -> None:
        self._plugin_conf_files.extend(conf_path)

    def get_conf_properties(self) -> dict[str, dict[str, dict[str, Any]]]:
        default_conf_properties = self.read_json(self._default_conf_file)["configuration"]

        plugin_conf_properties = {}
        for plugin_conf_file in self._plugin_conf_files:
            plugin_conf = self.read_json(plugin_conf_file)
            configuration = plugin_conf.get("configuration")
            if configuration is None:
                continue
            plugin_conf_properties[plugin_conf["name"]] = configuration
        default_conf_properties.update(plugin_conf_properties)
        return default_conf_properties

    def _get_current_settings(self) -> dict[str, Any]:
        default_settings = {}
        for conf_properties in self.get_conf_properties().values():
            for setting_name, property in conf_properties.items():
                default_settings[setting_name] = property.get("default")

        user_settings = self.read_json(self._save_file)
        default_settings.update(user_settings)
        return default_settings
