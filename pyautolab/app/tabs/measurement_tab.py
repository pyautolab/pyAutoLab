from pathlib import Path

from qtpy.QtCore import Qt, QThread, Slot  # type: ignore
from qtpy.QtWidgets import QDockWidget, QLineEdit, QMainWindow, QPlainTextEdit, QWidget

from pyautolab.app.app import App
from pyautolab.app.main_window import MainWindow
from pyautolab.app.runner import DataReadWorker, Runner
from pyautolab.core import qt
from pyautolab.core.plugin import DeviceTab
from pyautolab.core.utils.conf import RunConfiguration


class MeasurementTab(QMainWindow):
    def __init__(self, save_path: Path) -> None:
        super().__init__()
        self.ui = _SubWindowUi()
        self._conf = RunConfiguration()
        self.ui.setup_ui(self)
        self._runner = self._create_runner(save_path)

        # Thread
        self._data_read_thread = QThread()
        self._data_read_worker = DataReadWorker(self._runner.parent_recv_conn)

        self._setup()

    def _create_runner(self, save_path: Path) -> Runner:
        tabs = set()
        for device_status in App.device_statuses:
            tab = MainWindow.workspace.get_tab(device_status.name)
            if isinstance(tab, DeviceTab) and tab.device_enable:
                tabs.add(tab)
        return Runner(tabs, save_path)

    def _setup(self) -> None:
        # description line edit
        description_text = ", ".join([f"{name}[{unit}]" for name, unit in self._runner.data_descriptions.items()])
        self.ui.line_edit_description.setText(description_text)
        self.ui.line_edit_description.setCursorPosition(0)
        # Signal Slot
        self._data_read_worker.sig_read.connect(self._on_read)

        # layout
        graph_states: None | dict = self._conf.get("graphShowStates")
        graph_number_of_plots: None | dict = self._conf.get("graphNumberOfPlots")
        line_width: int = App.configurations.get("runner.graph.lineWidth")
        if self._conf.get("showGraph"):
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
        self.ui.console.setMaximumBlockCount(App.configurations.get("runner.console.maximumNumberOfLine"))

        # multiprocessing
        self._runner.start()

    @Slot()
    def stop(self) -> None:
        if self._data_read_thread.isFinished():
            return
        self._runner.stop_event.set()
        self._data_read_worker.sig_stopped.emit()
        self._data_read_thread.quit()
        self._data_read_thread.wait()

    @Slot(dict)
    def _on_read(self, data: dict[str, float]) -> None:
        str_list = [str(value) for value in data.values()]
        self.ui.console.appendPlainText(", ".join(str_list))

        if self._conf.get("showGraph"):
            data.pop("Time")
            self.ui.plot_widgets.update(data)


class _SubWindowUi:
    def setup_ui(self, win: QMainWindow) -> None:
        self.line_edit_description = QLineEdit()
        self.console = QPlainTextEdit(win)
        self.plot_widgets = qt.widgets.MultiplePlotWidget(
            win, App.configurations.get("runner.graph.antialias")
        )

        # Setup UI
        self.line_edit_description.setReadOnly(True)
        self.line_edit_description.setContentsMargins(0, 0, 0, 0)
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.console.setUndoRedoEnabled(False)
        self.console.setMinimumWidth(200)
        self.plot_widgets.hide()

        # Setup layout
        win.setCentralWidget(self.plot_widgets)

        widget = QWidget()
        qt.helper.layout(self.line_edit_description, self.console, parent=widget).setContentsMargins(0, 0, 0, 0)

        left_dock = QDockWidget("Console")
        left_dock.setWidget(widget)
        win.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)
