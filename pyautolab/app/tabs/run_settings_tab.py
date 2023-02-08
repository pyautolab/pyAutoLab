import qtawesome as qta
from qtpy.QtCore import Qt, Slot  # type: ignore
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QFormLayout, QGroupBox, QRadioButton, QSpinBox, QTreeView, QWidget

from pyautolab.app.app import App
from pyautolab.app.main_window import MainWindow
from pyautolab.core import qt
from pyautolab.core.plugin import DeviceTab
from pyautolab.core.utils.conf import RunConfiguration


class RunConfTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._ui = _TabUI()
        self._conf = RunConfiguration()
        self._ui.setup_ui(self)
        self._setup()

    def _setup(self) -> None:
        # Setup slot
        self._ui.spinbox_interval.valueChanged.connect(lambda num: self._conf.add("measuringInterval", num))
        self._ui.radiobutton_continuous.toggled.connect(self._toggle_continuous)
        self._ui.spinbox_number_measuring.valueChanged.connect(
            lambda num: self._conf.add("numberOfMeasuringTimes", num)
        )
        self._ui.group_graph.toggled.connect(lambda is_checked: self._conf.add("showGraph", is_checked))
        self._ui.graph_value_model.itemChanged.connect(self._change_graph_show_state)
        self._ui.graph_value_model.itemChanged.connect(self._change_graph_number_of_plots)
        self._ui.p_btn_reload_tree_view.pressed.connect(self.update_graph_tree_view)

        # Configuration
        self._ui.spinbox_interval.setValue(self._conf.get("measuringInterval"))
        self._ui.radiobutton_continuous.setChecked(self._conf.get("continuous"))
        self._ui.radiobutton_interval.setChecked(not self._conf.get("continuous"))
        self._ui.spinbox_number_measuring.setValue(self._conf.get("numberOfMeasuringTimes"))
        self._ui.group_graph.setChecked(self._conf.get("showGraph"))

        # Setup graph tree view
        self.update_graph_tree_view()

    @Slot(bool)  # type: ignore
    def _toggle_continuous(self, is_checked: bool) -> None:
        self._conf.add("continuous", is_checked)
        self._ui.spinbox_number_measuring.setDisabled(is_checked)

    def _change_graph_show_state(self, item: QStandardItem) -> None:
        measurement = item.text()
        if item.column() != 0:
            return
        parameters_saved = self._conf.get("graphShowStates")
        if parameters_saved is None:
            parameters_saved = {}
        parameters_saved.update({measurement: item.checkState() == Qt.CheckState.Checked})
        self._conf.add("graphShowStates", parameters_saved)

    def _change_graph_number_of_plots(self, item: QStandardItem) -> None:
        number_of_plots = item.text()
        if item.column() != 2:
            return
        try:
            number_of_plots = int(number_of_plots)
        except ValueError:
            number_of_plots = 100
            item.setText(str(number_of_plots))
            return
        measurement = item.model().item(item.row(), 0).text()
        parameter_saved = self._conf.get("graphNumberOfPlots")
        if parameter_saved is None:
            parameter_saved = {}
        parameters = parameter_saved.update({measurement: number_of_plots})
        self._conf.add("graphNumberOfPlots", parameters)

    def _update_graph_tree_model(self, parameters: dict[str, dict]) -> None:
        self._ui.graph_value_model.clear()
        for name, info in parameters.items():
            name_item, unit_item = QStandardItem(name), QStandardItem(f"[{info.pop('Unit')}]")
            plot_numbers = self._conf.get("graphNumberOfPlots")
            plots = 100 if plot_numbers is None else plot_numbers.get("name")
            if plots is None:
                plots = 100
            plots_item = QStandardItem(plots)
            name_item.setCheckable(True)
            name_item.setCheckState(Qt.CheckState.Checked if info["State"] else Qt.CheckState.Unchecked)
            name_item.setEditable(False)
            unit_item.setEditable(False)
            plots_item.setText(str(plots))
            self._ui.graph_value_model.invisibleRootItem().appendRow([name_item, unit_item, plots_item])
        headers = ["Parameter", "Unit", "Number of plot"]
        self._ui.graph_value_model.setHorizontalHeaderLabels(headers)

        for i in range(len(headers)):
            self._ui.treeview_graph.resizeColumnToContents(i)

    @Slot()
    def update_graph_tree_view(self) -> None:
        parameters: dict[str, dict] = {}
        for device_status in App.device_statuses:
            device_tab = MainWindow.workspace.get_tab(device_status.name)
            if not isinstance(device_tab, DeviceTab) or not device_tab.device_enable:
                continue
            _parameters = device_tab.get_parameters()
            if _parameters is None:
                continue
            for name, unit in _parameters.items():
                parameters.update({name: {"Unit": unit, "State": True, "Number": 100}})

        # Marge saved parameters
        show_states_saved = self._conf.get("graphShowStates")
        if show_states_saved is not None:
            for key, value in show_states_saved.items():
                if parameters.get(key) is None:
                    continue
                parameters[key].update({"State": value, "Number": 100})

        number_of_plots_saved = self._conf.get("graphNumberOfPlots")
        if number_of_plots_saved is not None:
            for key, value in number_of_plots_saved.items():
                if parameters.get(key) is None:
                    continue
                parameters[key]["Number"] = value
                if parameters[key].get("State") is None:
                    parameters[key]["State"] = True

        self._update_graph_tree_model(parameters)


class _TabUI:
    def setup_ui(self, win: QWidget) -> None:
        # Attribute
        self.spinbox_interval = QSpinBox()
        self.radiobutton_continuous = QRadioButton("Continuous")
        self.radiobutton_interval = QRadioButton("Measuring Interval")
        self.spinbox_number_measuring = QSpinBox()
        self.treeview_graph = QTreeView()
        self.p_btn_reload_tree_view = qt.helper.push_button(icon=qta.icon("mdi6.reload"), text="Reload")

        self.group_graph = QGroupBox("Graph")

        self.graph_value_model = QStandardItemModel()

        # Setup
        self.spinbox_interval.setRange(1, 100000)
        self.treeview_graph.setModel(self.graph_value_model)
        self.treeview_graph.setFixedHeight(240)
        self.treeview_graph.setAlternatingRowColors(True)
        self.treeview_graph.setStyleSheet("QHeaderView::section:first {padding-left: 50px;}")

        # Layout
        group_interval = QGroupBox("Interval")
        f_layout_interval = QFormLayout()
        f_layout_interval.addRow("Measuring Interval", qt.helper.add_unit(self.spinbox_interval, "msec"))
        group_interval.setLayout(f_layout_interval)

        group_number_of_times = QGroupBox("Number of times")
        f_layout = QFormLayout()
        f_layout.addRow(self.radiobutton_continuous)
        f_layout.addRow(self.radiobutton_interval, qt.helper.add_unit(self.spinbox_number_measuring, "times"))
        group_number_of_times.setLayout(f_layout)

        self.group_graph.setCheckable(True)
        qt.helper.layout(self.p_btn_reload_tree_view, self.treeview_graph, parent=self.group_graph)

        qt.helper.layout(
            "This setting is automatically saved.",
            group_interval,
            group_number_of_times,
            self.group_graph,
            parent=win,
        )
