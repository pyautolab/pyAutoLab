from __future__ import annotations

import multiprocessing as mp
from pathlib import Path
from typing import Callable

from qtpy.QtCore import Qt  # type: ignore

from pyautolab import api
from pyautolab.plugins.runner.run_conf import RunConf
from pyautolab.plugins.runner.worker import SaveWorker


class Runner:
    def __init__(self, device_tabs: set[api.DeviceTab]) -> None:
        # Timer
        self._measure_timer = api.qt_helpers.create_timer(
            None, enable_count=False, enable_clock=True, timer_type=Qt.TimerType.PreciseTimer
        )

        # get_control_object
        self._measurers: set[Callable] = set()
        self._controllers: set[api.Controller] = set()
        for tab in device_tabs:
            tab.setup_settings()
            controller = tab.get_controller()
            if controller is not None:
                self._controllers.add(controller)
            if hasattr(tab.device, "measure"):
                self._measurers.add(tab.device.measure)  # type: ignore

        # multiprocessing
        self.parent_recv_conn, self.child_send_conn = mp.Pipe(duplex=False)
        self.stop_event = mp.Event()
        self.data_descriptions = {"Time": "sec"}
        for tab in device_tabs:
            parameters = tab.get_parameters()
            if parameters is None:
                continue
            self.data_descriptions.update(parameters)

        self._save_worker = SaveWorker(self.data_descriptions, Path(RunConf().get("saveFilePath")))
        self._save_process = mp.Process(target=self._save_worker.start)
        self._save_process.daemon = True

    def start(self) -> None:
        self._save_process.start()
        self._measure_timer.timeout.connect(self._measure)  # type: ignore
        run_settings = RunConf()

        for device_controller in self._controllers:
            device_controller.start()
        self._measure_timer.start(int(run_settings.get("measuringInterval")))

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
