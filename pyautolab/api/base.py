from typing import Any

from pyautolab.app import App


def get_setting(setting_name: str) -> Any:
    return App.configurations.get(setting_name)
