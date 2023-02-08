from qtpy.QtWidgets import QHBoxLayout, QLabel, QLayout, QVBoxLayout, QWidget


def _append_content(
    layout: QVBoxLayout | QHBoxLayout,
    content: QWidget | QLayout | str | None | tuple[None, int],
) -> None:
    if isinstance(content, QWidget):
        layout.addWidget(content)
    elif isinstance(content, str):
        layout.addWidget(QLabel(content))
    elif content is None:
        layout.addStretch()
    elif isinstance(content, tuple):
        layout.addStretch(content[1])
    else:
        layout.addLayout(content)


def _create_v_layout(
    *contents: QWidget | QLayout | str | None | tuple[None, int],
    parent: QWidget | None = None,
) -> QVBoxLayout:
    layout = QVBoxLayout() if parent is None else QVBoxLayout(parent)
    for content in contents:
        _append_content(layout, content)
    return layout


def _create_h_layout(
    *contents: QWidget | QLayout | str | None | tuple[None, int],
    parent: QWidget | None = None,
) -> QHBoxLayout:
    layout = QHBoxLayout() if parent is None else QHBoxLayout(parent)
    for content in contents:
        _append_content(layout, content)
    return layout


def layout(
    *contents: QWidget
    | QLayout
    | str
    | None
    | tuple[None, int]
    | list[QWidget | QLayout | str | None | tuple[None, int]],
    parent: QWidget | None = None,
) -> QVBoxLayout | QHBoxLayout:
    if len(contents) == 1 and isinstance(contents[0], list):
        return _create_h_layout(*contents[0], parent=parent)

    layout = QVBoxLayout() if parent is None else QVBoxLayout(parent)
    stock: list[QWidget | QLayout | str | None | tuple[None, int]] = []
    for content in contents:
        if isinstance(content, list):
            if len(stock) == 1:
                _append_content(layout, stock[0])
            if len(stock) > 1:
                layout.addLayout(_create_v_layout(*stock))
            stock.clear()
            layout.addLayout(_create_h_layout(*content))
            continue
        stock.append(content)

    if len(stock) == 1:
        _append_content(layout, stock[0])
    if len(stock) > 1:
        layout.addLayout(_create_v_layout(*stock))
    return layout
