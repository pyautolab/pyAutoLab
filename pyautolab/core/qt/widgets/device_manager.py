from qtpy.QtCore import Slot  # type: ignore
from qtpy.QtWidgets import QDialog, QFrame, QScrollArea, QWidget

from pyautolab.core.plugin import DeviceStatus
from pyautolab.core.qt import helper, widgets
from pyautolab.core.qt.widgets import PortCombobox, Switch


class _DeviceWidget(QFrame):
    def __init__(self, device_status: DeviceStatus, parent: QWidget):
        super().__init__(parent)
        self._device_status = device_status

        self._combobox_port = PortCombobox(parent=self)
        self._combobox_baudrate = helper.combobox()
        self._switch = Switch()

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.Panel)

        # ComboBox of baud rate
        baudrate_property = self._device_status.device_properties.get("baudrate")
        if baudrate_property is None:
            self._combobox_baudrate.setEnabled(False)
        else:
            baudrate_default = baudrate_property.get("default")
            baudrates = baudrate_property.get("enum")
            self._combobox_baudrate.addItems([str(i) for i in baudrates])
            if baudrate_default := baudrate_property.get("default"):
                self._combobox_baudrate.setCurrentText(str(baudrate_default))

        self._switch.setChecked(self._device_status.is_connected)
        self._switch.toggled.connect(lambda check: self._connect() if check else self._disconnect())  # type: ignore

        # UI
        if self._device_status.device.port != "":
            self._combobox_port.addItem(self._device_status.device.port)
            self._combobox_port.setCurrentIndex(0)

        helper.layout(
            [f"<h4>{self._device_status.name}</h4>", None, self._switch],
            ["Port", None, self._combobox_port],
            ["Baud rate", None, self._combobox_baudrate],
            parent=self,
        )

    @Slot()
    def _connect(self):
        try:
            port_info = self._combobox_port.get_select_port_info()
            if port_info is None and self._combobox_port.currentIndex() == -1:
                raise Exception("Port is not selected.")

            if port_info is not None:
                self._device_status.device.port = port_info.device
            self._device_status.device.baudrate = self._combobox_baudrate.currentText()
            self._device_status.device.open()
            self._device_status.is_connected = True
        except Exception as e:
            self._switch.toggle()
            widgets.Alert("error", text=str(e), parent=self).open()

    @Slot()
    def _disconnect(self):
        try:
            self._device_status.device.close()
        except Exception as e:
            widgets.Alert("error", text=str(e), parent=self).open()
        finally:
            self._device_status.is_connected = False


class DeviceManager(QDialog):
    def __init__(self, device_statuses: list[DeviceStatus], parent: QWidget):
        super().__init__(parent)
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)

        # Layout
        widget = QWidget()
        helper.layout(
            *[_DeviceWidget(status, self) for status in device_statuses],
            None,
            parent=widget,
        )
        self._scroll_area.setWidget(widget)
        helper.layout(self._scroll_area, parent=self).setContentsMargins(0, 0, 0, 0)
