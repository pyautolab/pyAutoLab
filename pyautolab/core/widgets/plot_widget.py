from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import QMargins, QPoint, QRect, QSize
from qtpy.QtWidgets import QLayout, QScrollArea, QWidget


@dataclass
class _RealTimeCurve:
    curve: pg.PlotDataItem
    array: np.ndarray
    max: int
    counter: int


class FlowLayout(QLayout):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(QMargins(0, 0, 0, 0))
        self._item_list: list[QWidget] = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item: QWidget):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index: int):
        if index >= 0 and index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index: int):
        if index >= 0 and index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width: int):
        return self._do_layout(QRect(0, 0, width, 0))

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect: QRect, test_only: bool = True):
        x, y = rect.x(), rect.y()
        line_height = 0
        spacing = 5

        for item in self._item_list:
            next_x = x + item.sizeHint().width() + spacing
            if next_x - spacing > rect.right() and line_height > 0:
                x = rect.x()
                y += line_height + spacing
                next_x = x + item.sizeHint().width() + spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class PlotWidget(pg.PlotWidget):
    def __init__(self, parent: QWidget, background: str = "default", plotItem=None, **kargs):
        super().__init__(parent=parent, background=background, plotItem=plotItem, **kargs)
        self._parent = parent

    def mouseMoveEvent(self, ev) -> None:
        return self._parent.mouseMoveEvent(ev)

    def wheelEvent(self, ev) -> None:
        return self._parent.wheelEvent(ev)


class MultiplePlotWidget(QScrollArea):
    def __init__(self, parent: QWidget, antialias: bool = False) -> None:
        super().__init__()
        self._parent = parent
        self._layout = FlowLayout()
        self._plots: dict[str, pg.PlotItem] = {}
        self._curves: dict[str, _RealTimeCurve] = {}

        self.setWidgetResizable(True)
        pg.setConfigOption("antialias", antialias)

        # Layout
        widget = QWidget()
        widget.setLayout(self._layout)
        self.setWidget(widget)

    def create_graph(
        self,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        x_unit: str = "",
        y_unit: str = "",
        x_max: int = 100,
        line_width: int = 1,
        is_showgrid: bool = True,
    ) -> None:
        # Initialize PlotWidget
        plot = PlotWidget(parent=self._parent, title=title)
        plot.setLabel("bottom", x_label, units=x_unit)
        plot.setLabel("left", y_label, units=y_unit)
        plot.showGrid(x=is_showgrid, y=is_showgrid)
        plot.setMinimumSize(300, 300)

        plot.enableAutoRange(axis="y", enable=True)
        plot.setXRange(0, x_max)

        # Initialize PlotDataItem
        pen = pg.mkPen(color="r", width=line_width)
        curve = plot.plot(pen=pen, name=title, clear=True)

        self._plots[title] = plot
        array = np.empty(x_max)
        self._curves[title] = _RealTimeCurve(curve, array, x_max, 0)

        # Layout
        self._layout.addWidget(plot)

    def update(self, data: dict[str, float]) -> None:
        for name, num in data.items():
            curve = self._curves.get(name)
            if curve is None:
                continue
            if curve.counter < curve.max:
                curve.array[curve.counter] = num
                curve.curve.setData(curve.array[: curve.counter + 1])
                curve.counter += 1
            else:
                curve.array[:-1] = curve.array[1:]
                curve.array[-1] = num
                curve.curve.setData(curve.array)
