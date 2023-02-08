from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Type

from qtpy.QtCore import QObject
from qtpy.QtWidgets import QWidget


class Device(ABC):
    def __init__(self) -> None:
        self.port = ""
        self.baudrate = ""

    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def receive(self) -> str:
        pass

    @abstractmethod
    def send(self, message: str) -> None:
        pass

    @abstractmethod
    def reset_buffer(self) -> None:
        pass


class Controller(QObject):
    _counter = 0
    is_controllable = True

    def __init__(self) -> None:
        super().__init__()
        Controller._counter += 1
        Controller.is_controllable = True

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        Controller._counter -= 1
        if Controller._counter == 0:
            Controller.is_controllable = False


class DeviceTab(QWidget):
    def __init__(self, device: Device) -> None:
        super().__init__()
        self.device = device
        self.device_enable = True

    def get_controller(self) -> Controller | None:
        return None

    def setup_settings(self) -> None:
        return None

    def get_parameters(self) -> dict[str, str] | None:
        return None


@dataclass
class DeviceStatus:
    name: str
    device: Device
    device_properties: dict[str, Any]
    tab: Type[DeviceTab] | None
    is_connected: bool
