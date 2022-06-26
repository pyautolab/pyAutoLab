from __future__ import annotations

import csv
import multiprocessing as mp
import re
from multiprocessing.connection import Connection
from pathlib import Path

from qtpy.QtCore import QObject, Signal  # type: ignore

from pyautolab import api


class DataReadWorker(QObject):
    sig_read = Signal(dict)
    sig_stopped = Signal()

    def __init__(self, parent_recv_conn: Connection):
        super().__init__()
        self._parent_recv_conn = parent_recv_conn

    def start(self) -> None:
        self._timer_read_data = api.qt_helpers.create_timer(self, timeout=self._on_timer_timeout)
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
        self._save_file_path = self._rename_sequence_num(save_file_path)

    @staticmethod
    def _rename_sequence_num(save_file_path: Path) -> Path:
        if save_file_path.exists():
            pattern_sequence = re.compile(r"\)[0-9]+\(_")
            match = pattern_sequence.match(save_file_path.stem[::-1])
            if match is None:
                new_file_path = Path(f"{save_file_path.with_suffix('')}_(1){save_file_path.suffix}")
                return SaveWorker._rename_sequence_num(new_file_path)

            increment = int(match.group().replace("(", "").replace(")", "").replace("_", "")[::-1]) + 1
            new_file_name = pattern_sequence.sub(f"){str(increment)[::-1]}(_", save_file_path.stem[::-1], 1)[::-1]
            return SaveWorker._rename_sequence_num(save_file_path.parent / f"{new_file_name}{save_file_path.suffix}")
        return save_file_path

    def start(self) -> None:
        with self._save_file_path.open("w", encoding="utf-8-sig", newline="") as f:
            header = [f"{name}[{unit}]" for name, unit in self._data_info.items()]
            f.write(",".join(header) + "\n")
            writer = csv.DictWriter(f, self._data_info.keys())
            while not self.stop_event.is_set():
                if self._child_recv_conn.poll():
                    writer.writerow(self._child_recv_conn.recv())
