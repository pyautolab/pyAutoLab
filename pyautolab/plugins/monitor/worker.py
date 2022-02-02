from __future__ import annotations

from qtpy.QtCore import QObject, Signal  # type: ignore

from pyautolab.core.utils.plugin_helpers import DeviceStatus
from pyautolab.core.utils.qt_helpers import create_timer


class DataReadWorker(QObject):
    sig_read = Signal(str)
    sig_stopped = Signal()

    def __init__(self, device_status: DeviceStatus):
        super().__init__()
        self._device_status = device_status

    def start(self) -> None:
        self._timer_read_data = create_timer(self, timeout=self._read)
        self.sig_stopped.connect(self._stop)
        self._timer_read_data.start(10)

    def _read(self) -> None:
        try:
            message = self._device_status.device.receive()
        except Exception:
            self.sig_read.emit("")
            return
        if message == "":
            return
        self.sig_read.emit(message)

    def _stop(self) -> None:
        self._timer_read_data.stop()
