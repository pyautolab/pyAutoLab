from collections.abc import Callable

from pyautolab.app.app import App


def register_command(command: str, handler: Callable[[], None]):
    App.plugin_command_handlers[command] = handler
