import platform
from typing import Iterable

from qtpy.QtCore import QAbstractListModel, QEvent, QModelIndex, QObject, Qt
from qtpy.QtGui import QKeyEvent
from qtpy.QtWidgets import QComboBox, QStyledItemDelegate, QWidget
from serial.tools.list_ports_common import ListPortInfo

from pyautolab.core.utils.system import search_ports


class CheckListModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self._check_dict = {}

    def data(self, index, role):
        """Cell content."""
        text, check = list(self._check_dict.items())[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return text
        elif role == Qt.ItemDataRole.CheckStateRole:
            return check
        return None

    def rowCount(self, index):
        """Dictionary row number."""
        return len(self._check_dict)

    def columnCount(self, index):
        """Dictionary column number."""
        return 1

    def flags(self, index):
        """Set editable flag."""
        return Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled

    def setData(self, index, value, role):
        """Cell content change"""
        if role != Qt.ItemDataRole.CheckStateRole:
            return None
        key = list(self._check_dict.keys())[index.row()]
        self._check_dict[key] = Qt.CheckState.Checked if value == Qt.CheckState.Checked else Qt.CheckState.Unchecked
        return True

    def set_texts(self, items: Iterable[str]):
        self._check_dict = {item: Qt.CheckState.Checked for item in items}

    def get_checked_texts(self) -> list[str]:
        return [text for text, check in self._check_dict.items() if check == Qt.CheckState.Checked]


class CheckCombobox(QComboBox):
    def __init__(self):
        super().__init__()
        self._model = CheckListModel()
        self.setModel(self._model)

    def set_texts(self, texts: Iterable[str]):
        self._model.set_texts(texts)
        self._model.layoutChanged.emit()  # type: ignore

    def get_checked_texts(self) -> list[str]:
        return self._model.get_checked_texts()


class FlexiblePopupCombobox(QComboBox):
    class _MouseWheelGuard(QObject):
        def eventFilter(self, watched: QObject, event: QEvent) -> bool:
            if platform.system() == "Darwin":
                if event.type() == QEvent.Type.Wheel and not watched.hasFocus():
                    event.ignore()
                    return True
                return False
            elif platform.system() == "Windows":
                if event.type() == QEvent.Type.Wheel:
                    event.ignore()
                    return True
                return False
            return super().eventFilter(watched, event)

    def __init__(self, parent: QWidget | None = None, enable_auto_wheel_focus: bool = True) -> None:
        super().__init__(parent=parent)
        delegate = QStyledItemDelegate(parent)
        if enable_auto_wheel_focus:
            self.installEventFilter(self._MouseWheelGuard(self))
        self.setItemDelegate(delegate)

    def showPopup(self) -> None:
        width = self.view().sizeHintForColumn(0) + 20
        self.view().setMinimumWidth(width)
        super().showPopup()


class PortCombobox(FlexiblePopupCombobox):
    class _KeyEventGuard(QObject):
        def __init__(self, parent: QComboBox) -> None:
            super().__init__(parent=parent)
            self._combobox = parent

        def eventFilter(self, watched: QObject, event: QEvent) -> bool:
            if type(event) is QKeyEvent:
                if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                    self._combobox.view().pressed.emit(self._combobox.view().currentIndex())  # type: ignore
                    event.ignore()
                    return True
                return False
            return super().eventFilter(watched, event)

    def __init__(self, filter: str | None = None, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self._port_infos = []
        self.filter = "" if filter is None else filter
        self._port_selected = None

        self.setPlaceholderText("Select Port")
        self.view().pressed.connect(self._handle_item_pressed)  # type: ignore
        self.view().installEventFilter(self._KeyEventGuard(self))

    def get_select_port_info(self) -> ListPortInfo | None:
        return self._port_selected

    def showPopup(self) -> None:
        self._port_infos.clear()
        current_text = self.currentText()
        self.clear()
        self._port_infos = search_ports(self.filter)
        for port in self._port_infos:
            description = port.device
            if port.manufacturer is not None:
                description += f"  |  {port.manufacturer}"
            self.addItem(description)
            if current_text != "" and current_text in description:
                self.setCurrentText(description)

        if len(self._port_infos) == 0:
            self._port_selected = None

        port_selected = self._port_selected
        if port_selected is not None:
            if port_selected.manufacturer is None:
                self.setCurrentText(f"{port_selected.device}")
            else:
                self.setCurrentText(f"{port_selected.device}  |  {port_selected.manufacturer}")
        super().showPopup()

    def _handle_item_pressed(self, index: QModelIndex) -> None:
        self._port_selected = self._port_infos[index.row()]
