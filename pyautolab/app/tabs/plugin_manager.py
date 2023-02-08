from qtpy.QtWidgets import QFormLayout, QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from pyautolab.core.plugin import Plugin
from pyautolab.core.qt import helper


class _PluginWidget(QFrame):
    def __init__(self, plugin: Plugin) -> None:
        super().__init__()
        self._plugin = plugin
        self._p_btn_state = helper.push_button(
            clicked=self._change_state, text="Disable" if plugin.enable else "Enable"
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        f_layout = QFormLayout(self)
        f_layout.addRow(QLabel(f"<h4>{self._plugin.name}</h4>"))
        if self._plugin.name is not None:
            f_layout.addRow(QLabel(self._plugin.description))
        f_layout.addRow(self._p_btn_state)

    def _change_state(self) -> None:
        state: str = self.sender().text()  # type: ignore
        self._plugin.enable = state == "Enable"
        self._p_btn_state.setText("Disable" if state == "Enable" else "Enable")


class PluginManager(QWidget):
    def __init__(self, plugins: tuple[Plugin]) -> None:
        super().__init__()
        self._ui = _UI()
        self._ui.setup_ui(self)

        plugin_widgets = [_PluginWidget(plugin) for plugin in plugins if not plugin.is_internal]
        for plugin_widget in plugin_widgets:
            self._ui.dynamic_layout.addWidget(plugin_widget)
        self._ui.dynamic_layout.addStretch()


class _UI:
    def setup_ui(self, parent: PluginManager) -> None:
        # Widgets
        self.dynamic_layout = QVBoxLayout()
        scroll_area = QScrollArea(parent)

        # Setup Widgets
        scroll_area.setWidgetResizable(True)

        # Layout
        widget = QWidget()
        widget.setLayout(self.dynamic_layout)
        scroll_area.setWidget(widget)
        v_layout = QVBoxLayout(parent)
        v_layout.addWidget(scroll_area)
