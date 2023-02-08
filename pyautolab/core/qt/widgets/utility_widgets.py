from qtpy.QtCore import Qt, Slot  # type: ignore
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QHBoxLayout, QLineEdit, QSlider, QSpinBox, QWidget


class IntSlider(QWidget):
    """THe IntSlider class provides controller with a handle which can be pulled back
    and forth to change the **integer**.
    """

    def __init__(self):
        super().__init__()
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._spinbox = QSpinBox()

        # setup signal
        self._slider.valueChanged.connect(self._value_changed)  # type: ignore
        self._spinbox.valueChanged.connect(self._value_changed)  # type: ignore

        # setup layout
        h_layout = QHBoxLayout(self)
        h_layout.addWidget(self._slider)
        h_layout.addWidget(self._spinbox)

    @property
    def current_value(self) -> int:
        return self._spinbox.value()

    @property
    def range(self) -> tuple[int, int]:
        return self._slider.minimum(), self._slider.maximum()

    @range.setter
    def range(self, numbers: tuple[int, int]) -> None:
        self._slider.setRange(*numbers)
        self._spinbox.setRange(*numbers)

    @Slot(int)
    def _value_changed(self, value: int) -> None:
        sender = self.sender()
        if sender is self._slider:
            self._spinbox.blockSignals(True)
            self._spinbox.setValue(value)
            self._spinbox.blockSignals(False)
        elif sender is self._spinbox:
            self._slider.blockSignals(True)
            self._slider.setValue(value)
            self._slider.blockSignals(False)

    def update_current_value(self, num: int) -> None:
        """Update current number of this widget. This method changes the display of the gui.

        Parameters
        ----------
        num : int
            Integer.
        """
        self._spinbox.setValue(num)


class IconLineEdit(QLineEdit):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self._status: str = ""
        self._actions: dict[str, QAction] = {}
        self._refresh()
        self._icon_visible = False

    def _refresh(self) -> None:
        """After an application style change, the paintEvent updates the custom defined stylesheet."""
        self.update()

    def hide_status_icon(self) -> None:
        self._icon_visible = False
        self._update_action()

    def show_status_icon(self) -> None:
        self._icon_visible = True
        self._update_action()

    def update_status(self, value: str) -> None:
        """Update the status and set_status to update the icons to display."""
        self._status = value
        self._update_action()

    def addActions(self, actions: dict[str, QAction]) -> None:
        self._actions.update(actions)
        return super().addActions(list(actions.values()))

    def addAction(self, status_name: str, action: QAction) -> None:
        self._actions.update({status_name: action})
        return super().addAction(action)

    def removeAction(self, status: str) -> None:
        self._actions.pop(status)
        return super().removeAction(self._actions[status])

    def _update_action(self) -> None:
        # Reset actions
        for action in self._actions.values():
            super().removeAction(action)
        if self._icon_visible:
            super().addAction(self._actions[self._status], self.ActionPosition.TrailingPosition)
