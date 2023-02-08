"""
pyautolab base configuration management
This file only deals with non-GUI configuration features
"""
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from pyautolab.core.utils.system import get_pyautolab_data_folder_path

_USER_SETTINGS_FILE_NAME = "user_settings"
with resources.path("pyautolab", "default.json") as path:
    _DEFAULT_CONF_FILE_PATH = path


@dataclass(unsafe_hash=True, frozen=True)
class ConfProps:
    title: str
    description: str
    type: str
    default: str | bool | int
    minimum: int | None
    maximum: int | None
    enum: list[str | int] | None


class AbstractConf(ABC):
    def __init__(self, id: str, default_conf_file: Path | None = None) -> None:
        self._save_file = get_pyautolab_data_folder_path() / (id + ".json")

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

    def exists(self) -> bool:
        return self._save_file.exists()

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
        super().__init__(default_conf_file=_DEFAULT_CONF_FILE_PATH, id=_USER_SETTINGS_FILE_NAME)
        self._configs: dict[str, list[ConfProps]] = {}
        self._load_default_conf()

    def _load_default_conf(self) -> None:
        default_groups: dict[str, dict[str, dict]] = self.read_json(self._default_conf_file)["configuration"]
        for group, dict_configs in default_groups.items():
            self._configs[group] = [
                ConfProps(
                    title,
                    dict_config["description"],
                    dict_config["type"],
                    dict_config["default"],
                    dict_config.get("minimum"),
                    dict_config.get("maximum"),
                    dict_config.get("enum"),
                )
                for title, dict_config in dict_configs.items()
            ]

    def add_conf(self, conf: ConfProps, group: str) -> None:
        configs = self._configs.get(group)
        if configs is None:
            self._configs[group] = [conf]
        else:
            configs.append(conf)

    def _get_current_settings(self) -> dict[str, Any]:
        default_settings = {conf.title: conf.default for configs in self._configs.values() for conf in configs}
        user_settings = self.read_json(self._save_file)
        default_settings.update(user_settings)
        return default_settings

    def get_all_props(self) -> dict[str, list[ConfProps]]:
        return self._configs


class RunConfiguration(AbstractConf):
    def __init__(self) -> None:
        super().__init__(id="user_run_conf", default_conf_file=_DEFAULT_CONF_FILE_PATH)

    def _get_current_settings(self) -> dict[str, Any]:
        default_conf = self.read_json(self._default_conf_file)["runConfiguration"]
        user_conf = self.read_json(self._save_file)
        default_conf.update(user_conf)
        return default_conf
