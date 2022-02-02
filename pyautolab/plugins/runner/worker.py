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
    def __init__(self, data_description: dict[str, str], save_file: str) -> None:
        super().__init__()
        self._child_recv_conn, self.parent_send_conn = mp.Pipe(duplex=False)
        self._data_description = data_description
        self.stop_event = mp.Event()
        self._save_file_path = self._rename_sequence_num(save_file)

    def _rename_sequence_num(self, file_path: str) -> str:
        save_file = Path(file_path)
        save_file_name = save_file.name
        if save_file.exists():
            compile_path = re.compile(r"\)[0-9]+\(")
            match = compile_path.search(save_file_name[::-1])
            if match is None:
                extensions = "".join(save_file.suffixes)
                save_file_path_no_suffixes = file_path[: -len(extensions)]
                return self._rename_sequence_num(f"{save_file_path_no_suffixes}_(1){extensions}")
            match_text = match.group()
            match_text_remove_brackets = match_text[1:-1]
            increment = int(match_text_remove_brackets[::-1]) + 1
            text_replace = compile_path.sub(f"){str(increment)[::-1]}(", file_path[::-1], 1)
            return self._rename_sequence_num(text_replace[::-1])
        return file_path

    def start(self) -> None:
        with open(self._save_file_path, "w", encoding="utf-8-sig", newline="") as f:
            header = [f"{name}[{unit}]" for name, unit in self._data_description.items()]
            f.write(",".join(header) + "\n")
            fieldnames = [name for name, _ in self._data_description.items()]
            writer = csv.DictWriter(f, fieldnames)
            while not self.stop_event.is_set():
                if self._child_recv_conn.poll():
                    writer.writerow(self._child_recv_conn.recv())
