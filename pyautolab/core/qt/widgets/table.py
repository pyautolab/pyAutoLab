from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal  # type: ignore
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QTableView


class ListTableModel(QAbstractTableModel):
    def __init__(self, li):
        super().__init__()
        self._list = li
        self._header_index = 0

    @property
    def header_index(self):
        return self._header_index

    @header_index.setter
    def header_index(self, index):
        self._header_index = index
        self.layoutChanged.emit()  # type: ignore

    @property
    def list_2d(self):
        return self._list

    @list_2d.setter
    def list_2d(self, li):
        self._list = li
        self.layoutChanged.emit()  # type: ignore

    def data(self, index, role):
        """Cell content."""
        if role == Qt.ItemDataRole.DisplayRole:
            return self._list[index.row()][index.column()]
        elif role == Qt.ItemDataRole.BackgroundRole:
            if self._is_header(index.row()):
                return QColor(Qt.GlobalColor.darkGreen)
            return None
        elif role == Qt.ItemDataRole.ForegroundRole:
            if self._is_header(index.row()):
                return QColor(Qt.GlobalColor.white)
            return None
        return None

    def rowCount(self, index):
        """List column number."""
        return len(self._list)

    def columnCount(self, index):
        """List column number."""
        return len(self._list[0])

    def headerData(self, section, orientation, role):
        """Set header data."""
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Vertical:
            return f"{section+1}(Header)" if self._is_header(section) else section + 1
        else:
            return section + 1

    def flags(self, index):
        """Set editable flag."""
        if self._is_lower_header(index.row()):
            return Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def _is_header(self, row_index):
        return self._header_index == row_index

    def _is_lower_header(self, row_index):
        return row_index <= self._header_index

    def set_list(self, li):
        self._list = li
        self.layoutChanged.emit()  # type: ignore


class ListTableView(QTableView):
    selected = Signal(QModelIndex)

    def __init__(self, li=[[""] * 5] * 5):
        super().__init__()
        self.setModel(ListTableModel(li))
        self.setSortingEnabled(False)
        self.setShortcutEnabled(False)
        self.setCornerButtonEnabled(False)

    def selected_area(self):
        indexes = self.selectedIndexes()
        if len(indexes) == 0:
            return None
        rows = [index.row() + 1 for index in indexes]
        columns = [index.column() + 1 for index in indexes]
        return min(rows), max(rows), min(columns), max(columns)
