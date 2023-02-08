import csv
import multiprocessing as mp
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Callable

from qtpy.QtCore import QObject, Qt, Signal  # type: ignore

from pyautolab import api
from pyautolab.core.utils.conf import RunConfiguration


class DataReadWorker(QObject):
    sig_read = Signal(dict)
    sig_stopped = Signal()

    def __init__(self, parent_recv_conn: Connection):
        super().__init__()
        self._parent_recv_conn = parent_recv_conn

    def start(self) -> None:
        self._timer_read_data = api.qt.timer(self, timeout=self._on_timer_timeout)
        self.sig_stopped.connect(self._stop)
        self._timer_read_data.start(10)

    def _on_timer_timeout(self) -> None:
        if self._parent_recv_conn.poll(0):
            data = self._parent_recv_conn.recv()
            self.sig_read.emit(data)

    def _stop(self) -> None:
        self._timer_read_data.stop()


class SaveWorker:
    def __init__(self, data_info: dict[str, str], save_file_path: Path) -> None:
        super().__init__()
        self._child_recv_conn, self.parent_send_conn = mp.Pipe(duplex=False)
        self._data_info = data_info
        self.stop_event = mp.Event()
        self._save_file_path = save_file_path

    def start(self) -> None:
        with self._save_file_path.open("w", encoding="utf-8-sig", newline="") as f:
            header = [f"{name}[{unit}]" for name, unit in self._data_info.items()]
            f.write(",".join(header) + "\n")
            writer = csv.DictWriter(f, self._data_info.keys())
            while not self.stop_event.is_set():
                if self._child_recv_conn.poll():
                    writer.writerow(self._child_recv_conn.recv())


class Runner:
    def __init__(self, device_tabs: set[api.DeviceTab], save_path: Path) -> None:
        # Timer
        self._measure_timer = api.qt.timer(enable_count=False, enable_clock=True, timer_type=Qt.TimerType.PreciseTimer)

        # get_control_object
        self._measurers: set[Callable] = set()
        self._controllers: set[api.Controller] = set()
        for tab in device_tabs:
            tab.setup_settings()
            if controller := tab.get_controller():
                self._controllers.add(controller)
            if hasattr(tab.device, "measure"):
                self._measurers.add(tab.device.measure)  # type: ignore

        # multiprocessing
        self.parent_recv_conn, self.child_send_conn = mp.Pipe(duplex=False)
        self.stop_event = mp.Event()
        self.data_descriptions = {"Time": "sec"}
        for tab in device_tabs:
            if parameters := tab.get_parameters():
                self.data_descriptions.update(parameters)

        self._save_worker = SaveWorker(self.data_descriptions, save_path)
        self._save_process = mp.Process(target=self._save_worker.start)
        self._save_process.daemon = True

    def start(self) -> None:
        self._save_process.start()
        self._measure_timer.timeout.connect(self._measure)  # type: ignore

        for device_controller in self._controllers:
            device_controller.start()
        self._measure_timer.start(int(RunConfiguration().get("measuringInterval")))

    def _measure(self) -> None:
        measurement_time = round(self._measure_timer.time, 2)
        measurements = {"Time": measurement_time}
        for measurer in self._measurers:
            measurements.update(measurer())
        self.child_send_conn.send(measurements)
        self._save_worker.parent_send_conn.send(measurements)
        if self.stop_event.is_set():
            self.stop()

    def stop(self) -> None:
        self._measure_timer.stop()
        for device_controller in self._controllers:
            device_controller.stop()
        self._save_worker.stop_event.set()
        self._save_process.join()
        self._controllers.clear()
        self._measurers.clear()
