from __future__ import annotations

from qtpy.QtCore import Qt, Slot  # type: ignore
from qtpy.QtWidgets import QButtonGroup, QDialog, QFormLayout, QFrame, QLabel, QMessageBox, QScrollArea, QWidget
from serial import SerialException

from pyautolab.core.utils.plugin_helpers import DeviceStatus
from pyautolab.core.utils.qt_helpers import create_combobox, create_push_button, create_v_box_layout
from pyautolab.core.widgets.combobox import PortCombobox


class _DeviceWidget(QFrame):
    def __init__(self, device_status: DeviceStatus, parent: QWidget | None = None):
        super().__init__(parent)
        self._device_status = device_status

        self._label_name = QLabel(f"<h4>{self._device_status.name}</h4>")
        self._combobox_port = PortCombobox(parent=self)
        self._combobox_baudrate = create_combobox()
        self._p_btn_connect = create_push_button(fixed_width=100, text="Connect", clicked=self._connect_device)
        self._p_btn_disconnect = create_push_button(
            fixed_width=100, text="Disconnect", clicked=self._disconnect_device
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._label_name.setWordWrap(True)

        # ComboBox of baud rate
        baudrate_property = self._device_status.device_properties.get("baudrate")
        if baudrate_property is None:
            self._combobox_baudrate.setEnabled(False)
        else:
            baudrate_default = baudrate_property.get("default")
            baudrates = baudrate_property.get("enum")
            self._combobox_baudrate.addItems([str(i) for i in baudrates])
            if baudrate_default is not None:
                self._combobox_baudrate.setCurrentText(str(baudrate_default))

        # button
        for btn in [self._p_btn_connect, self._p_btn_disconnect]:
            btn.setDefault(False)
            btn.setAutoDefault(False)
            btn.setCheckable(True)
        btn_group = QButtonGroup(self)
        btn_group.addButton(self._p_btn_connect)
        btn_group.addButton(self._p_btn_disconnect)
        btn_group.setExclusive(True)
        if self._device_status.is_connected:
            self._p_btn_connect.setChecked(True)
        else:
            self._p_btn_disconnect.setChecked(True)

        # UI
        if self._device_status.device.port != "":
            self._combobox_port.addItem(self._device_status.device.port)
            self._combobox_port.setCurrentIndex(0)

        f_layout = QFormLayout(self)
        f_layout.addRow(self._label_name)
        f_layout.addRow("Port     ", self._combobox_port)
        f_layout.addRow("Baud rate", self._combobox_baudrate)
        f_layout.addRow(self._p_btn_connect, self._p_btn_disconnect)

        self.setMaximumWidth(500)

    @Slot()  # type: ignore
    def _connect_device(self):
        try:
            port_info = self._combobox_port.get_select_port_info()
            if port_info is None and self._combobox_port.currentIndex() == -1:
                raise Exception("Port is not selected.")
            else:
                if port_info is not None:
                    self._device_status.device.port = port_info.device
                self._device_status.device.baudrate = self._combobox_baudrate.currentText()
                self._device_status.device.open()
                self._device_status.is_connected = True
        except SerialException as e:
            error_message = str(e)
            self._p_btn_disconnect.setChecked(error_message != "Port is already open.")
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            self._p_btn_disconnect.setChecked(True)
            QMessageBox.critical(self, "Error", str(e))

    @Slot()  # type: ignore
    def _disconnect_device(self):
        try:
            self._device_status.device.close()
        except SerialException as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self._device_status.is_connected = False


class DeviceManager(QDialog):
    def __init__(self, device_statuses: list[DeviceStatus], parent: QWidget):
        super().__init__(parent)
        self._device_statuses = device_statuses
        self._scroll_area = QScrollArea(self)
        self._setup()

    def _setup(self) -> None:
        self.setMaximumSize(350, 500)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setWidgetResizable(True)
        self.setStyleSheet(".QScrollArea {border: none; margin: 0; padding: 0; margin-right: 2px;}")

        # Layout
        dynamic_v_layout = create_v_box_layout([_DeviceWidget(status, self) for status in self._device_statuses])
        dynamic_v_layout.addStretch()

        widget = QWidget()
        widget.setLayout(dynamic_v_layout)
        self._scroll_area.setWidget(widget)
        v_layout = create_v_box_layout([self._scroll_area], self)
        v_layout.setContentsMargins(0, 0, 0, 0)
