from typing import Literal

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QDialogButtonBox, QLabel, QScrollArea, QSizePolicy, QStyle, QWidget

from pyautolab.core.qt import helper


class _AlertUI:
    def setup_ui(self, parent: QWidget) -> None:
        self.frame = QScrollArea(parent)
        self.icon_label = QLabel()
        self.text_label = QLabel()
        self.button_box = QDialogButtonBox()

        # Setting widgets
        parent.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        parent.setFixedWidth(200)
        parent.setMaximumHeight(500)
        parent.setWindowModality(Qt.WindowModality.WindowModal)
        self.frame.setWidgetResizable(True)
        self.button_box.setOrientation(Qt.Orientation.Vertical)
        self.button_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)

        # Layout
        self.widget = QWidget()
        helper.layout(
            self.icon_label,
            self.text_label,
            self.button_box,
            parent=self.widget,
        )

        self.frame.setWidget(self.widget)
        helper.layout(self.frame, parent=parent).setContentsMargins(1, 1, 0, 0)


class Alert(QDialog):
    def __init__(
        self,
        severity: Literal["error", "info", "warning"],
        *,
        text: str,
        parent: QWidget | None,
        buttons: QDialogButtonBox.StandardButton | None = None,
    ):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self._ui = _AlertUI()
        self._result: QDialogButtonBox.StandardButton | None = None

        self._ui.setup_ui(self)
        self._setup_alert_message(severity, text, buttons)
        self._connect_button_signal()

    def _setup_alert_message(
        self,
        severity: Literal["error", "info", "warning"],
        text: str,
        buttons: QDialogButtonBox.StandardButton | None,
    ) -> None:
        self._ui.text_label.setText(text)

        match severity:
            case "error":
                pixmap_id = QStyle.StandardPixmap.SP_MessageBoxCritical
                default_buttons = QDialogButtonBox.StandardButton.Ok
            case "info":
                pixmap_id = QStyle.StandardPixmap.SP_MessageBoxInformation
                default_buttons = QDialogButtonBox.StandardButton.Ok
            case "warning":
                pixmap_id = QStyle.StandardPixmap.SP_MessageBoxWarning
                default_buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            case _:
                raise ValueError(f"Invalid severity name: {severity}")

        icon = self.style().standardIcon(pixmap_id)
        self._ui.icon_label.setPixmap(icon.pixmap(50, 50))

        if buttons is None:
            buttons = default_buttons
        self._ui.button_box.setStandardButtons(buttons)

        self._adjust_size()

    def _adjust_size(self) -> None:
        self._ui.button_box.adjustSize()
        self._ui.widget.adjustSize()
        self.adjustSize()
        # To remove a vertical scrollbar,
        # add the height of vertical scrollbar if dialog height is lower than its maximum height.
        self.setFixedSize(self.size().width(), self.size().height() + self._ui.frame.verticalScrollBar().height())

    def _on_button_pressed(self) -> None:
        for standard_button in self._ui.button_box.standardButtons():
            button = self._ui.button_box.button(standard_button)
            if self.sender() == button:
                button_role = self._ui.button_box.buttonRole(button)
                if button_role == QDialogButtonBox.ButtonRole.AcceptRole:
                    self.done(QDialog.DialogCode.Accepted)
                self._result = standard_button
                self.done(QDialog.DialogCode.Rejected)
                break

    def _connect_button_signal(self) -> None:
        for button in self._ui.button_box.buttons():
            button.pressed.connect(self._on_button_pressed)  # type: ignore

    def open(self) -> QDialogButtonBox.StandardButton:
        super().exec()
        if self._result is None:
            self._result = QDialogButtonBox.StandardButton.Cancel
        return self._result
