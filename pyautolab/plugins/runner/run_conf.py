from __future__ import annotations

from importlib import resources
from typing import Any

from pyautolab import api


class RunConf(api.utility.AbstractConf):
    def __init__(self) -> None:
        with resources.path("pyautolab.plugins.runner", "default_run_conf.json") as conf_path:
            save_file = self._get_user_conf_path() / "user_run_conf.json"
            super().__init__(default_conf_file=conf_path, save_file=save_file)

    def _get_current_settings(self) -> dict[str, Any]:
        default_conf = self.read_json(self._default_conf_file)
        user_conf = self.read_json(self._save_file)
        default_conf.update(user_conf)
        return default_conf


run_conf = RunConf()
