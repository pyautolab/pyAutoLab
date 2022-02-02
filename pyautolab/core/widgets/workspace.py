from __future__ import annotations

from qtpy.QtCore import Slot  # type: ignore
from qtpy.QtWidgets import QCheckBox, QHBoxLayout, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from pyautolab.core.utils.plugin_helpers import DeviceTab


class Workspace(QWidget):
    def __init__(self):
        super().__init__()
        self._tab_widget = QTabWidget()
        self._tabs: dict[str, QWidget] = {}
        self._device_tabs = {}
        self._setup_ui()

        # trigger
        self._tab_widget.tabCloseRequested.connect(self._remove_tab)

    def _setup_ui(self) -> None:
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.setUsesScrollButtons(True)

        # setup layout
        h_layout = QHBoxLayout(self)
        h_layout.addWidget(self._tab_widget)
        h_layout.setContentsMargins(0, 0, 0, 0)

    def set_welcome_tab(self, tab: QWidget) -> None:
        self._tab_widget.insertTab(0, tab, "Welcome")
        self._tabs["Welcome"] = tab
        self._tab_widget.setCurrentIndex(0)
        self._tab_widget.adjustSize()

    @staticmethod
    def _add_scrollbar(tab: QWidget) -> QWidget:
        scrollarea = QScrollArea()
        scrollarea.setObjectName("PyAutoLabTabWidget")
        scrollarea.setWidget(tab)
        scrollarea.setWidgetResizable(True)
        scrollarea.setStyleSheet("#PyAutoLabTabWidget{border: none;}")
        return scrollarea

    def add_tab(self, tab: QWidget, name: str, enable_remove_button: bool = False) -> None:
        if name in self._tabs:
            self._tab_widget.setCurrentWidget(self._tabs[name])
            return
        widget_with_scroll = self._add_scrollbar(tab)
        self._tab_widget.addTab(widget_with_scroll, name)
        self._tab_widget.setCurrentWidget(widget_with_scroll)
        self._tabs[name] = widget_with_scroll
        if not enable_remove_button:
            tab_index = self._tab_widget.indexOf(widget_with_scroll)
            self._remove_tab_button(tab_index)

    @staticmethod
    def _add_device_status_checkbox(device_tab: DeviceTab) -> QWidget:
        widget_with_checkbox = QWidget()

        check_box = QCheckBox("Enable device")
        check_box.setChecked(True)

        @Slot(bool)  # type: ignore
        def on_check_box_state_changed(is_checked):
            device_tab.device_enable = is_checked

        check_box.stateChanged.connect(on_check_box_state_changed)
        v_layout = QVBoxLayout()
        v_layout.addWidget(check_box)
        v_layout.addWidget(device_tab)
        widget_with_checkbox.setLayout(v_layout)
        v_layout.setContentsMargins(0, 0, 0, 0)
        return widget_with_checkbox

    def add_device_tab(self, device_tab: DeviceTab, device_name: str) -> None:
        widget_with_checkbox = self._add_device_status_checkbox(device_tab)

        self.add_tab(widget_with_checkbox, device_name)
        self.disable_tab(device_name)
        self._device_tabs[device_name] = device_tab

    def remove_tab(self, name: str) -> None:
        tab_index = self._tab_widget.indexOf(self._tabs[name])
        self._remove_tab(tab_index)

    def _remove_tab(self, index: int) -> None:
        widget = self._tab_widget.widget(index)
        self._tab_widget.removeTab(index)
        name = [name for name, tab in self._tabs.items() if tab is widget][0]
        self._tabs.pop(name)

    def enable_tab(self, name: str) -> None:
        widget = self._tabs[name]
        self._tab_widget.addTab(widget, name)
        tab_index = self._tab_widget.indexOf(self._tabs[name])
        if self._device_tabs.get(name):
            self._remove_tab_button(tab_index)
        widget.setEnabled(True)

    def disable_tab(self, name: str) -> None:
        tab_index = self._tab_widget.indexOf(self._tabs[name])
        if tab_index == -1:
            return
        self._tab_widget.removeTab(tab_index)
        self._tabs[name].setEnabled(False)

    def get_tab(self, name: str) -> QWidget | None:
        return self._tabs.get(name)

    def get_device_tab(self, name: str) -> DeviceTab | None:
        return self._device_tabs.get(name)

    def _remove_tab_button(self, tab_index: int) -> None:
        right = self._tab_widget.tabBar().ButtonPosition.RightSide
        left = self._tab_widget.tabBar().ButtonPosition.LeftSide
        self._tab_widget.tabBar().setTabButton(tab_index, right, None)  # type: ignore
        self._tab_widget.tabBar().setTabButton(tab_index, left, None)  # type: ignore
