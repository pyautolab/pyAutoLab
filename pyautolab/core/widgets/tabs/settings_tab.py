from __future__ import annotations

import re
from typing import Any

from qtpy.QtCore import Qt, Slot  # type: ignore
from qtpy.QtGui import QMouseEvent
from qtpy.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pyautolab.core.utils.conf import Configuration
from pyautolab.core.utils.qt_helpers import create_combobox


class _SettingLabel(QLabel):
    def __init__(self, text: str, parent: QWidget):
        super().__init__(parent=parent)
        self.setWordWrap(True)
        self.setText(text)


class _TitleWidget(QLabel):
    def __init__(self, parent: QWidget, setting_title: str):
        super().__init__(parent=parent)
        self.setWordWrap(True)
        self.setText(f"<h1><strong>{setting_title}</strong></h1>")


class _SettingWidget(QFrame):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        name: str,
        setting_property: dict[str, Any],
        settings: Configuration,
    ):
        super().__init__(parent=parent)
        self.dynamic_widget: QWidget
        self._setting_name = name
        self._setting_title = title
        self._settings = settings
        self._setup_ui(setting_property)

    def _setup_ui(self, setting_property: dict[str, Any]):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setContentsMargins(0, 0, 0, 0)

        setting_value = self._settings.get(self._setting_name)

        # Enum ComboBox
        if setting_property.get("enum") is not None:
            self.dynamic_widget = create_combobox(self)
            self.dynamic_widget.addItems([str(item) for item in setting_property["enum"]])
            self.dynamic_widget.setCurrentText(setting_value)
            self.dynamic_widget.currentTextChanged.connect(self._write_setting)
        # Bool CheckBox
        elif setting_property["type"] == "boolean":
            self.dynamic_widget = QCheckBox(setting_property["description"])
            self.dynamic_widget.setChecked(setting_value)
            self.dynamic_widget.stateChanged.connect(self._write_setting)
        # Number SpinBox
        elif setting_property["type"] in ("number", "integer"):
            self.dynamic_widget = QDoubleSpinBox(self) if setting_property["type"] == "number" else QSpinBox(self)
            self.dynamic_widget.setFixedWidth(150)
            if setting_property.get("minimum") is not None:
                self.dynamic_widget.setMinimum(setting_property["minimum"])
            if setting_property.get("maximum") is not None:
                self.dynamic_widget.setMaximum(setting_property["maximum"])
            self.dynamic_widget.setValue(setting_value)
            self.dynamic_widget.valueChanged.connect(self._write_setting)
        # String LineEdit
        elif setting_property["type"] == "string":
            self.dynamic_widget = QLineEdit(self)
            self.dynamic_widget.setFixedWidth(300)
            self.dynamic_widget.setText(setting_value)
            self.dynamic_widget.textChanged.connect(self._write_setting)

        setting_name = self._create_name_description()
        v_layout = QVBoxLayout(self)
        v_layout.addWidget(_SettingLabel(setting_name, self))
        if setting_property["type"] != "boolean":
            v_layout.addWidget(_SettingLabel(setting_property["description"], self))
        v_layout.addWidget(self.dynamic_widget)

    def _create_name_description(self) -> str:
        result = " > ".join(list(self._setting_name.split(".")[:-1]))
        setting_name = re.sub(r"(\w)([A-Z])", r"\1 \2", self._setting_name.split(".")[-1])
        return f"{result} > <strong>{setting_name[0].upper()+setting_name[1:]}</strong>"

    def _write_setting(self, setting_value):
        self._settings.add(self._setting_name, setting_value)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.dynamic_widget.setFocus()
        return super().mousePressEvent(event)


class SettingsTab(QWidget):
    def __init__(self, parent: QWidget, settings: Configuration):
        super().__init__(parent=parent)
        self._settings = settings
        self._searchbar = QLineEdit()
        self._dynamic_v_layout = QVBoxLayout()
        self._scroll_area = QScrollArea(self)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setWidgetResizable(True)
        self._searchbar.textChanged.connect(self._update)
        self._searchbar.setPlaceholderText("Search settings")

        h_layout = QHBoxLayout()
        h_layout.addWidget(self._searchbar)

        for widget in self._create_setting_widgets(""):
            self._dynamic_v_layout.addWidget(widget)
        self._dynamic_v_layout.addStretch()

        widget = QWidget()
        widget.setLayout(self._dynamic_v_layout)
        self._scroll_area.setWidget(widget)
        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self._scroll_area)
        self.setLayout(v_layout)

    def _create_setting_widgets(self, searcher: str) -> list[_SettingWidget]:
        setting_widgets = []
        for title, setting_properties in self._settings.get_conf_properties().items():
            if self._is_showable(searcher, [title]):
                title_widget = _TitleWidget(self._scroll_area, title)
                setting_widgets.append(title_widget)
            for name, setting_property in setting_properties.items():
                if self._is_showable(searcher, [title, name, setting_property["description"]]):
                    widget = _SettingWidget(
                        parent=self._scroll_area,
                        title=title,
                        name=name,
                        setting_property=setting_property,
                        settings=self._settings,
                    )
                    setting_widgets.append(widget)
        return setting_widgets

    @staticmethod
    def _is_showable(searcher: str, search_list: list[str]) -> bool:
        return any(searcher.lower() in sentence.lower() for sentence in search_list)

    @Slot()  # type: ignore
    def _update(self) -> None:
        self.dynamic_v_layout = QVBoxLayout()
        for widget in self._create_setting_widgets(self._searchbar.text()):
            self.dynamic_v_layout.addWidget(widget)
        self.dynamic_v_layout.addStretch()
        widget = QWidget()
        widget.setLayout(self.dynamic_v_layout)
        self._scroll_area.setWidget(widget)
