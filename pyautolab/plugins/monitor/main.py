import qtawesome as qta

from pyautolab import api
from pyautolab.plugins.monitor.widget import CommunicationMonitor


def main() -> None:
    action_open_monitor = api.window.create_window_action(
        "Open communication monitor",
        qta.icon("mdi6.monitor"),
        triggered=lambda: api.window.workspace.add_tab(CommunicationMonitor(), "Communication monitor", True),
    )

    api.window.toolbar.add_action(action_open_monitor)
