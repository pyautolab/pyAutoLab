from collections.abc import Callable

from qtpy.QtWidgets import QCheckBox, QScrollArea, QStyle, QTabWidget, QWidget

from pyautolab.core.plugin import DeviceTab
from pyautolab.core.qt import helper


class Workspace(QWidget):
    def __init__(self):
        super().__init__()
        self._tab_widget = QTabWidget()
        self._original_tabs: dict[str, QWidget | DeviceTab] = {}
        self._tabs: dict[str, QWidget] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._tab_widget.setMovable(True)
        self._tab_widget.setUsesScrollButtons(True)

        # setup layout
        helper.layout([self._tab_widget], parent=self).setContentsMargins(0, 0, 0, 0)

    @staticmethod
    def _add_scrollbar(tab: QWidget) -> QWidget:
        scroll_area = QScrollArea()
        scroll_area.setWidget(tab)
        scroll_area.setWidgetResizable(True)
        return scroll_area

    def _add_close_button(self, name: str, widget: QWidget, on_closed: Callable[[], None] | None) -> None:
        def close() -> None:
            if on_closed is not None:
                on_closed()
            self.remove_tab(name)

        close_button = helper.tool_button(
            icon=self.style().standardIcon(QStyle.StandardPixmap.SP_TabCloseButton),
            clicked=close,
            parent=self._tab_widget.tabBar(),
        )
        close_button.setStyleSheet("padding: 0; spacing: 0px;")
        self._tab_widget.tabBar().setTabButton(
            self._tab_widget.indexOf(widget),
            self._tab_widget.tabBar().ButtonPosition.RightSide,
            close_button,
        )

    def add_tab(
        self,
        tab: QWidget | DeviceTab,
        name: str,
        enable_remove_button: bool = False,
        on_closed: Callable[[], None] | None = None,
    ) -> None:
        if name in self._tabs:
            self._tab_widget.setCurrentWidget(self._tabs[name])
            return

        self._original_tabs[name] = tab
        if isinstance(tab, DeviceTab):
            tab = self._add_device_status_checkbox(tab)
        tab = self._add_scrollbar(tab)
        self._tab_widget.addTab(tab, name)
        self._tab_widget.setCurrentWidget(tab)
        if enable_remove_button:
            self._add_close_button(name, tab, on_closed)
        self._tabs[name] = tab

    @staticmethod
    def _add_device_status_checkbox(device_tab: DeviceTab) -> QWidget:
        widget_with_checkbox = QWidget()

        check_box = QCheckBox("Enable device")
        check_box.setChecked(True)

        def on_check_box_state_changed(is_checked):
            device_tab.device_enable = is_checked

        check_box.stateChanged.connect(on_check_box_state_changed)  # type: ignore
        helper.layout(
            check_box,
            device_tab,
            parent=widget_with_checkbox,
        ).setContentsMargins(0, 0, 0, 0)
        return widget_with_checkbox

    def remove_tab(self, name: str) -> None:
        index = self._tab_widget.indexOf(self._tabs[name])
        self._tab_widget.removeTab(index)
        tab = self._tabs.pop(name)
        self._original_tabs.pop(name)
        tab.deleteLater()

    def get_tab(self, name: str) -> QWidget | DeviceTab | None:
        return self._original_tabs.get(name)
