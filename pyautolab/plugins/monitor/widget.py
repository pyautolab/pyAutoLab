from time import sleep

import qtawesome as qta
from qtpy.QtCore import QThread, Slot  # type: ignore
from qtpy.QtWidgets import QLineEdit, QPlainTextEdit, QWidget

from pyautolab import api
from pyautolab.core.utils.qt_helpers import create_push_button
from pyautolab.plugins.monitor.worker import DataReadWorker


class CommunicationMonitor(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent=parent)
        self._ui = _MonitorUI()
        self._ui._setup_ui(self)

        self._device_statuses_connected = []
        self._current_device_status: api.utility.DeviceStatus

        self._data_read_thread: QThread
        self._data_read_worker: DataReadWorker

        self._setup()

    def __del__(self):
        self._stop()
        sleep(1)

    def _setup(self) -> None:
        # Setup Signal
        self._ui.p_btn_refresh.clicked.connect(self._refresh_device_status)
        self._ui.p_btn_send.clicked.connect(self._send_message)
        self._ui.combobox_devices.currentIndexChanged.connect(self._change_current_device)
        self._ui.line_edit_send.returnPressed.connect(self._send_message)
        self._ui.p_btn_clear.clicked.connect(self._ui.console.clear)

        self._ui.p_btn_refresh.click()

    @Slot()  # type: ignore
    def _send_message(self) -> None:
        message = self._ui.line_edit_send.text()
        self._ui.line_edit_send.clear()
        self._current_device_status.device.send(message)

    @Slot(int)  # type: ignore
    def _change_current_device(self, index: int) -> None:
        self._current_device_status = self._device_statuses_connected[index]
        if len(self._device_statuses_connected) == 0:
            return
        self._start()

    @Slot()  # type: ignore
    def _refresh_device_status(self) -> None:
        self._ui.combobox_devices.clear()
        self._device_statuses_connected.clear()

        for device_status in api.get_device_statuses():
            if not device_status.is_connected:
                continue
            self._device_statuses_connected.append(device_status)
        if len(self._device_statuses_connected) == 0:
            self._ui.combobox_devices.addItems([])
            self._ui.p_btn_send.setEnabled(False)
            self._ui.line_edit_send.setEnabled(False)
            self._stop()
        else:
            self._current_device_status = self._device_statuses_connected[0]
            self._ui.combobox_devices.addItems(
                [device_status.name for device_status in self._device_statuses_connected]
            )
            self._ui.p_btn_send.setEnabled(True)
            self._ui.line_edit_send.setEnabled(True)
            self._start()

    def _stop(self) -> None:
        if getattr(self, "_data_read_thread", None) is None:
            return
        if self._data_read_thread.isRunning():
            self._data_read_worker.sig_stopped.emit()
            self._data_read_thread.quit()
            self._data_read_thread.wait()

    @Slot()  # type: ignore
    def _start(self) -> None:
        if getattr(self, "_data_read_thread", None) is not None and self._data_read_thread.isRunning():
            self._stop()
        self._data_read_thread = QThread()
        self._data_read_worker = DataReadWorker(self._current_device_status)
        self._data_read_worker.moveToThread(self._data_read_thread)
        self._data_read_thread.started.connect(self._data_read_worker.start)
        self._data_read_thread.finished.connect(self._data_read_worker.deleteLater)
        self._data_read_worker.sig_read.connect(self._read)
        self._data_read_thread.start()

    @Slot(str)  # type: ignore
    def _read(self, message: str) -> None:
        if message == "":
            self._refresh_device_status()
            return
        self._ui.console.appendPlainText(message)


class _MonitorUI:
    def _setup_ui(self, win: QWidget) -> None:
        # member
        self.combobox_devices = api.qt_helpers.create_combobox(win)
        self.console = QPlainTextEdit()
        self.line_edit_send = QLineEdit()
        self.p_btn_refresh = create_push_button(fixed_width=50, icon=qta.icon("mdi6.refresh"))
        self.p_btn_send = create_push_button(fixed_width=50, icon=qta.icon("mdi6.send"))
        self.p_btn_clear = create_push_button(text="Clear Output")

        # setup ui
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.console.setUndoRedoEnabled(False)

        # layout
        h_layout_send = api.qt_helpers.create_h_box_layout([self.line_edit_send, self.p_btn_send])
        h_layout_device = api.qt_helpers.create_h_box_layout([self.combobox_devices, self.p_btn_refresh])
        api.qt_helpers.create_v_box_layout([h_layout_device, self.console, h_layout_send, self.p_btn_clear], win)
