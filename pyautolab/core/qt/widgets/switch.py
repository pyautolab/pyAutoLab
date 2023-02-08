from qtpy.QtCore import Property, QEasingCurve, QPropertyAnimation, QSize  # type: ignore
from qtpy.QtGui import QMouseEvent
from qtpy.QtWidgets import QAbstractButton, QFrame, QToolButton, QWidget


class Thumb(QToolButton):
    def __init__(self, parent: QWidget, outline_width: int):
        super().__init__(parent)
        self.__position = 0.0
        self.__thumb_margin = parent.rect().height() / 6
        self._parent = parent
        self._outline_width = outline_width

        self._track_animation = QPropertyAnimation(self, b"_position")
        self._track_animation.setStartValue(0.0)
        self._track_animation.setEndValue(1.0)
        self._track_animation.setDuration(200)

        self._margin_animation = QPropertyAnimation(self, b"_thumb_margin")
        self._margin_animation.setDuration(80)

        self.setCheckable(True)

    @Property(float)  # type: ignore
    def _thumb_margin(self) -> float:  # type: ignore
        return self.__thumb_margin

    @_thumb_margin.setter
    def _thumb_margin(self, margin: float) -> None:
        self.__thumb_margin = margin
        self.update()

    def _compute_geometry(self) -> tuple[int, int, int, int]:
        r = (self._parent.rect().height() - 2 * self.outline_width - 2 * self._thumb_margin) / 2
        operating_line_length = self._parent.rect().width() - 2 * self.outline_width - 2 * self._thumb_margin - 2 * r
        x = self.outline_width + self._thumb_margin + self._position * operating_line_length
        y = self._parent.rect().height() / 2 - r
        width = height = r * 2
        return x, y, width, height

    @Property(float)  # type: ignore
    def _position(self) -> float:  # type: ignore
        return self.__position

    @_position.setter
    def _position(self, pos: float) -> None:
        self.__position = pos
        self.update()

    @property
    def outline_width(self) -> int:
        return self._outline_width

    @outline_width.setter
    def outline_width(self, width: int) -> None:
        self._outline_width = width

    def resize(self) -> None:
        self._margin_animation.stop()
        self._thumb_margin = self._parent.rect().height() / (6 if not self.isChecked() else 15)

    def expand(self) -> None:
        self._margin_animation.stop()
        self._margin_animation.setEndValue(0)
        self._margin_animation.start()

    def restore(self) -> None:
        margin = self._parent.rect().height() / (6 if not self.isChecked() else 15)

        self._margin_animation.stop()
        self._margin_animation.setEndValue(margin)
        self._margin_animation.start()

    def move_forward(self, is_change_margin=False) -> None:
        if not self.isChecked():
            self._track_animation.setDirection(QPropertyAnimation.Direction.Forward)
            self._track_animation.setEasingCurve(QEasingCurve.Type.OutBack)
            self._track_animation.start()
            self.setChecked(True)

        if is_change_margin:
            margin = self._parent.rect().height() / 15
            self._margin_animation.stop()
            self._margin_animation.setEndValue(margin)
            self._margin_animation.start()

    def move_backward(self, is_change_margin=False) -> None:
        if self.isChecked():
            self._track_animation.setDirection(QPropertyAnimation.Direction.Backward)
            self._track_animation.setEasingCurve(QEasingCurve.Type.InBack)
            self._track_animation.start()
            self.setChecked(False)

        if is_change_margin:
            margin = self._parent.rect().height() / 6
            self._margin_animation.stop()
            self._margin_animation.setEndValue(margin)
            self._margin_animation.start()

    def update(self) -> None:
        super().setGeometry(*self._compute_geometry())
        radius = self.geometry().width() / 2 - 0.01
        self.setStyleSheet(f"border-radius: {radius}px")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        event.ignore()


class Track(QFrame):
    def __init__(self, parent: QWidget, outline_width: int) -> None:
        super().__init__(parent)
        self._parent = parent
        self._outline_width = outline_width

    def update(self) -> None:
        self.setGeometry(self._parent.rect())
        radius = self.rect().height() / 2 - 0.01
        self.setStyleSheet(f"border-radius: {radius}px; border-style: solid; border-width: {self._outline_width}px")


class Switch(QAbstractButton):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            """
    Switch[checked=false] > Thumb {
        background: #79747E;
    }
    Switch[checked=true] > Thumb {
        background: #FFFFFF;
    }
    Switch[checked=false] > Track {
        background: #E7E0EC;
        border-color: #79747E;
    }
    Switch[checked=true] > Track {
        background: #6750A4;
        border-color: #6750A4;
    }
    """
        )
        self._outline_width = 2
        self._track = Track(self, self._outline_width)
        self._thumb = Thumb(self, self._outline_width)

        self._start_mouse_x, self._old_mouse_x = 0.0, 0.0
        self._is_pressed = False

        self.toggled.connect(lambda checked: self._forward() if checked else self._backward())  # type: ignore
        self.setCheckable(True)
        self.setChecked(False)

    def _forward(self) -> None:
        self._track.update()
        self._thumb.move_forward(is_change_margin=not self._is_pressed)

    def _backward(self) -> None:
        self._track.update()
        self._thumb.move_backward(is_change_margin=not self._is_pressed)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._is_pressed = True
        self._old_mouse_x = self._start_mouse_x = event.position().x()
        self._thumb.expand()
        return super().mousePressEvent(event)

    def _is_mouse_pos_checked(self, x: float) -> bool:
        return self.rect().width() / 2 <= x

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._is_pressed = False

        if self._thumb.isChecked() != self.isChecked():
            return self.toggle()

        self._thumb.restore()
        if self._start_mouse_x < 0:
            return None
        return super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.underMouse():
            return super().mouseMoveEvent(event)
        current_mouse_x = event.position().x()

        was_mouse_pos_checked = self._is_mouse_pos_checked(self._old_mouse_x)
        is_mouse_pos_checked = self._is_mouse_pos_checked(current_mouse_x)
        if not was_mouse_pos_checked and is_mouse_pos_checked:
            self._forward()
            self._start_mouse_x = -1
        elif was_mouse_pos_checked and not is_mouse_pos_checked:
            self._backward()
            self._start_mouse_x = -1
        self._old_mouse_x = current_mouse_x
        return super().mouseMoveEvent(event)

    def resizeEvent(self, event) -> None:
        self._thumb.resize()
        self._track.update()
        return super().resizeEvent(event)

    def sizeHint(self) -> QSize:
        """Override QWidget.sizeHint() to set initial size."""
        return QSize(50, 30)

    def paintEvent(self, event) -> None:
        pass
