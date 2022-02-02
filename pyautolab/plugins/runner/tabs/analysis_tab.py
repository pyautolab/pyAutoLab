from __future__ import annotations

from pathlib import Path

import qtawesome as qta
from qtpy.QtCore import Qt, QThread, Slot  # type: ignore
from qtpy.QtWidgets import QDockWidget, QLineEdit, QMainWindow, QPlainTextEdit, QToolBar, QWidget

from pyautolab import api
from pyautolab.plugins.runner.run_conf import run_conf
from pyautolab.plugins.runner.runner import Runner
from pyautolab.plugins.runner.worker import DataReadWorker


class AnalysisWidget(QMainWindow):
    def __init__(self, tab_title: str) -> None:
        super().__init__()
        self.ui = _SubWindowUi()
        self.ui.setup_ui(self)
        self._save_path = Path(run_conf.get("saveFilePath"))
        self._tab_title = tab_title

        # Action
        self._action_stop = api.qt_helpers.create_action(
            self,
            text="Stop Measurement",
            icon=qta.icon("ph.stop-fill", color="red"),
            triggered=self._stop,
        )
        self._action_close = api.qt_helpers.create_action(
            self, text="Close Current Tab", icon=qta.icon("mdi6.close"), triggered=self._close_tab
        )

        self._runner: Runner
        self._setup_runner()

        # Thread
        self._data_read_thread = QThread()
        self._data_read_worker = DataReadWorker(self._runner.parent_recv_conn)

        self._setup()

    def _setup_runner(self) -> None:
        tabs = set()
        for device_status in api.get_device_statuses():
            device_tab = api.window.workspace.get_device_tab(device_status.name)
            if device_tab is None or not device_tab.isEnabled() or not device_tab.device_enable:
                continue
            tabs.add(device_tab)
        self._runner = Runner(tabs)

    def _setup(self) -> None:
        self.setWindowTitle("Analysis Window")

        # description line edit
        description_text = ", ".join([f"{name}[{unit}]" for name, unit in self._runner.data_descriptions.items()])
        self.ui.line_edit_description.setText(description_text)
        self.ui.line_edit_description.setCursorPosition(0)
        # Signal Slot
        self._data_read_worker.sig_read.connect(self._on_read)

        self.ui.toolbar.addActions((self._action_stop, self._action_close))

        # layout
        graph_states: None | dict = run_conf.get("graphShowStates")
        graph_number_of_plots: None | dict = run_conf.get("graphNumberOfPlots")
        line_width: int = api.get_setting("analysisWindow.graph.lineWidth")
        if run_conf.get("showGraph"):
            self.ui.plot_widgets.show()
            for title, unit in self._runner.data_descriptions.items():
                if title == "Time":
                    continue
                # Graph show states
                graph_state = True if graph_states is None else graph_states.get(title)
                if graph_state is not None and not graph_state:
                    continue

                # Number of plots
                plots = 100 if graph_number_of_plots is None else graph_number_of_plots.get(title)
                if plots is None:
                    plots = 100
                self.ui.plot_widgets.create_graph(
                    title=f"{title}", x_max=plots, y_label=title, y_unit=unit, line_width=line_width
                )

        # thread
        self._data_read_worker.moveToThread(self._data_read_thread)
        self._data_read_thread.started.connect(self._data_read_worker.start)  # type: ignore
        self._data_read_thread.finished.connect(self._data_read_worker.deleteLater)  # type: ignore
        self._data_read_thread.start()

        # settings
        self.ui.console.setMaximumBlockCount(api.get_setting("analysisWindow.console.maximumNumberOfLine"))

        # multiprocessing
        self._runner.start()

    @Slot()  # type: ignore
    def _stop(self) -> None:
        if self._data_read_thread.isFinished():
            return
        self._runner.stop_event.set()
        self._data_read_worker.sig_stopped.emit()
        self._data_read_thread.quit()
        self._data_read_thread.wait()

    @Slot(dict)  # type: ignore
    def _on_read(self, data: dict[str, float]) -> None:
        str_list = [str(value) for value in data.values()]
        self.ui.console.appendPlainText(", ".join(str_list))

        if run_conf.get("showGraph"):
            data.pop("Time")
            self.ui.plot_widgets.update(data)

    @Slot()  # type: ignore
    def _close_tab(self) -> None:
        self._action_stop.trigger()
        api.window.workspace.remove_tab(self._tab_title)


class _SubWindowUi:
    def setup_ui(self, win: QMainWindow) -> None:
        self.line_edit_description = QLineEdit()
        self.console = QPlainTextEdit(win)
        self.toolbar = QToolBar(win)
        self.plot_widgets = api.widgets.MultiplePlotWidget(win, api.get_setting("analysisWindow.graph.antialias"))

        # Setup UI
        self.line_edit_description.setReadOnly(True)
        self.line_edit_description.setContentsMargins(0, 0, 0, 0)
        self.toolbar.setMovable(False)
        win.addToolBar(self.toolbar)
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.console.setUndoRedoEnabled(False)
        self.console.setMinimumWidth(200)
        self.plot_widgets.hide()

        # Setup layout
        # central
        win.setCentralWidget(self.plot_widgets)

        # left dock
        v_layout = api.qt_helpers.create_v_box_layout([self.line_edit_description, self.console])
        v_layout.setContentsMargins(0, 0, 0, 0)

        widget = QWidget()
        widget.setLayout(v_layout)
        left_dock = QDockWidget("Console")
        left_dock.setWidget(widget)
        win.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)
