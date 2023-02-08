import re

from qtpy.QtCore import Qt, Slot  # type: ignore
from qtpy.QtGui import QMouseEvent
from qtpy.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pyautolab.core.qt import helper
from pyautolab.core.utils.conf import Configuration, ConfProps


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
        group: str,
        # name: str,
        # setting_property: dict[str, Any],
        props: ConfProps,
        settings: Configuration,
    ):
        super().__init__(parent=parent)
        self.dynamic_widget: QWidget
        self._props = props
        self._group = group
        self._settings = settings
        self._setup_ui()

    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setContentsMargins(0, 0, 0, 0)

        setting_value = self._settings.get(self._props.title)

        # Enum ComboBox
        if self._props.enum is not None:
            self.dynamic_widget = helper.combobox(self)
            self.dynamic_widget.addItems([str(item) for item in self._props.enum])
            self.dynamic_widget.setCurrentText(setting_value)
            self.dynamic_widget.currentTextChanged.connect(self._write_setting)  # type: ignore
        # Bool CheckBox
        elif self._props.type == "boolean":
            self.dynamic_widget = QCheckBox(self._props.description)
            self.dynamic_widget.setChecked(setting_value)
            self.dynamic_widget.stateChanged.connect(self._write_setting)  # type: ignore
        # Number SpinBox
        elif self._props.type in ("number", "integer"):
            self.dynamic_widget = QDoubleSpinBox(self) if self._props.type == "number" else QSpinBox(self)
            self.dynamic_widget.setFixedWidth(150)
            if self._props.minimum is not None:
                self.dynamic_widget.setMinimum(self._props.minimum)
            if self._props.maximum is not None:
                self.dynamic_widget.setMaximum(self._props.maximum)
            self.dynamic_widget.setValue(setting_value)
            self.dynamic_widget.valueChanged.connect(self._write_setting)  # type: ignore
        # String LineEdit
        elif self._props.type == "string":
            self.dynamic_widget = QLineEdit(self)
            self.dynamic_widget.setFixedWidth(300)
            self.dynamic_widget.setText(setting_value)
            self.dynamic_widget.textChanged.connect(self._write_setting)  # type: ignore

        setting_name = self._create_name_description()
        v_layout = QVBoxLayout(self)
        v_layout.addWidget(_SettingLabel(setting_name, self))
        if self._props.type != "boolean":
            v_layout.addWidget(_SettingLabel(self._props.description, self))
        v_layout.addWidget(self.dynamic_widget)

    def _create_name_description(self) -> str:
        result = " > ".join(list(self._props.title.split(".")[:-1]))
        setting_name = re.sub(r"(\w)([A-Z])", r"\1 \2", self._props.title.split(".")[-1])
        return f"{result} > <strong>{setting_name[0].upper()+setting_name[1:]}</strong>"

    def _write_setting(self, setting_value):
        self._settings.add(self._props.title, setting_value)

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
        self._searchbar.textChanged.connect(self._update)  # type: ignore
        self._searchbar.setPlaceholderText("Search settings")

        for widget in self._create_setting_widgets(""):
            self._dynamic_v_layout.addWidget(widget)
        self._dynamic_v_layout.addStretch()

        widget = QWidget()
        widget.setLayout(self._dynamic_v_layout)
        self._scroll_area.setWidget(widget)
        helper.layout(
            [self._searchbar],
            self._scroll_area,
            parent=self,
        )

    def _create_setting_widgets(self, searcher: str) -> list[_SettingWidget]:
        setting_widgets = []
        for group, configs in self._settings.get_all_props().items():
            if self._is_showable(searcher, [group]):
                title_widget = _TitleWidget(self._scroll_area, group)
                setting_widgets.append(title_widget)
            for props in configs:
                if self._is_showable(searcher, [group, props.title, props.description]):
                    setting_widgets.append(_SettingWidget(self._scroll_area, group, props, self._settings))
        return setting_widgets

    @staticmethod
    def _is_showable(searcher: str, search_list: list[str]) -> bool:
        return any(searcher.lower() in sentence.lower() for sentence in search_list)

    @Slot()
    def _update(self) -> None:
        widget = QWidget()
        self.dynamic_v_layout = helper.layout(
            *self._create_setting_widgets(self._searchbar.text()),
            None,
            parent=widget,
        )
        self._scroll_area.setWidget(widget)
