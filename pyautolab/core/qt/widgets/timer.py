from time import perf_counter

from qtpy.QtCore import QObject, QTimer, QTimerEvent


class AutoLabTimer(QTimer):
    """This timer remembers the number of timeouts and execution time of this timer. You can check the `counter`
    property for checking the current count property and the `time` property for checking the current execution time.
    The count and time resets when the timer stops.

    Parameters
    ----------
    QObject : QObject
        Parent of this timer., by default None.
    """

    def __init__(self, parent: QObject | None = None, enable_count: bool = False, enable_clock: bool = False) -> None:
        super().__init__(parent=parent)
        self._counter = 0
        self._time = 0
        self._start_time = 0
        self._enable_count = enable_count
        self._enable_clock = enable_clock

    @property
    def counter(self) -> int:
        return self._counter

    @property
    def time(self) -> float:
        return self._time

    def start(self, msec: int) -> None:
        """Override Qt method to set the starting time[sec]. This start time is used to measure the time since the
        timer started.

        Parameters
        ----------
        msec : int
            Timeout interval of milliseconds.
        """
        super().start(msec)
        if self._enable_clock:
            self._start_time = perf_counter()

    def stop(self) -> None:
        """Override Qt method to reset attribute."""
        super().stop()
        self._counter = 0
        self._time = 0
        self._start_time = 0

    def timerEvent(self, event: QTimerEvent) -> None:
        """Override Qt method to update parameter"""
        if self._enable_count:
            self._counter += 1
        if self._enable_clock:
            self._time = perf_counter() - self._start_time
        super().timerEvent(event)
