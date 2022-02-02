from __future__ import annotations

from pathlib import Path

import qtawesome as qta
from qtpy.QtCore import Qt, QTimer, Slot  # type: ignore
from qtpy.QtGui import QFocusEvent, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QRadioButton,
    QSizePolicy,
    QSpinBox,
    QTreeView,
    QWidget,
)
from typing_extensions import Literal

from pyautolab import api
from pyautolab.plugins.runner.run_conf import run_conf


class PathLineEdit(api.widgets.IconLineEdit):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.textChanged.connect(self._inspect_path)
        self._setup()

    def _setup(self) -> None:
        action_ok = api.qt_helpers.create_action(self, "Available file name", qta.icon("fa.check", color="green"))
        action_warning = api.qt_helpers.create_action(
            self, "Existing file name", qta.icon("fa.warning", color="#FFC40C")
        )
        action_error = api.qt_helpers.create_action(
            self, "Unavailable file name", qta.icon("mdi6.close-circle", color="red")
        )
        self.addActions({"ok": action_ok, "warning": action_warning, "error": action_error})
        self._inspect_path(self.text())
        self.show_status_icon()

    def focusInEvent(self, arg__1: QFocusEvent) -> None:
        self.show_status_icon()
        super().focusInEvent(arg__1)

    def focusOutEvent(self, arg__1: QFocusEvent) -> None:
        # Calling asynchronously the 'add_current_text' to avoid crash
        # https://groups.google.com/group/spyderlib/browse_thread/thread/2257abf530e210bd
        if self._get_status(self.text()) == "error":
            QTimer.singleShot(50, lambda: run_conf.get("saveFilePath"))

        return super().focusOutEvent(arg__1)

    def _get_status(self, file_path: str) -> Literal["ok", "warning", "error"]:
        file = Path(file_path)
        if file.is_file():
            return "warning"
        if file.is_dir():
            return "error"
        if file.suffix not in ["", ".csv"]:
            return "error"
        if file.name[0] == "." or file.name[-1] == ".":
            return "error"
        if file.parent.is_dir():
            return "ok"
        return "error"

    @Slot(str)  # type: ignore
    def _inspect_path(self, path: str) -> None:
        """Validate entered path"""
        status = self._get_status(path)
        self.update_status(status)
        if status in ["ok", "warning"]:
            if Path(path).suffix == "":
                path += ".csv"
            run_conf.add("saveFilePath", path)


class RunConfTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._ui = _TabUI()
        self._ui.setup_ui(self)
        self._setup()

    def _setup(self) -> None:
        # Setup slot
        self._ui.group_save_to_file.toggled.connect(self._change_conf_save_to_file)
        self._ui.p_btn_open_file_dialog.clicked.connect(self._open_file_dialog)
        self._ui.spinbox_interval.valueChanged.connect(lambda num: run_conf.add("measuringInterval", num))
        self._ui.radiobutton_continuous.toggled.connect(self._toggle_continuous)
        self._ui.spinbox_number_measuring.valueChanged.connect(lambda num: run_conf.add("numberOfMeasuringTimes", num))
        self._ui.group_graph.toggled.connect(lambda is_checked: run_conf.add("showGraph", is_checked))
        self._ui.graph_value_model.itemChanged.connect(self._change_graph_show_state)
        self._ui.graph_value_model.itemChanged.connect(self._change_graph_number_of_plots)
        self._ui.p_btn_reload_tree_view.pressed.connect(self.update_graph_tree_view)

        # Configuration
        run_conf.add("openFlag", "opened")
        save_file_name = run_conf.get("saveFilePath")
        if save_file_name == "":
            save_file = Path(api.get_setting("system.defaultFolder")) / "temp.csv"
            save_file_name = str(save_file)
            run_conf.add("saveFilePath", save_file_name)

        self._ui.file_path_line.setText(save_file_name)
        self._ui.group_save_to_file.setChecked(run_conf.get("saveToFile"))

        is_checked = self._ui.group_save_to_file.isChecked()
        self._ui.file_path_line.setEnabled(is_checked)
        self._ui.p_btn_open_file_dialog.setEnabled(is_checked)

        self._ui.spinbox_interval.setValue(run_conf.get("measuringInterval"))
        self._ui.radiobutton_continuous.setChecked(run_conf.get("continuous"))
        self._ui.radiobutton_interval.setChecked(not run_conf.get("continuous"))
        self._ui.spinbox_number_measuring.setValue(run_conf.get("numberOfMeasuringTimes"))
        self._ui.group_graph.setChecked(run_conf.get("showGraph"))

        # Setup graph tree view
        self.update_graph_tree_view()

    @Slot()  # type: ignore
    def _open_file_dialog(self) -> None:
        save_path = Path(self._ui.file_path_line.text())
        open_path_name = save_path
        if save_path.is_file() and not save_path.parent.exists():
            open_path_name = run_conf.get("saveFilePath")
        if save_path.is_dir() and not save_path.exists():
            open_path_name = run_conf.get("saveFilePath")
        file_name = QFileDialog.getSaveFileName(self, "Csv File", str(open_path_name), "CSV UTF-8 (*.csv)")[0]
        if file_name == "":
            return
        path = Path(file_name).absolute()
        self._ui.file_path_line.setText(str(path))
        run_conf.add("saveFilePath", str(path))

    @Slot(bool)  # type: ignore
    def _change_conf_save_to_file(self, is_checked) -> None:
        run_conf.add("saveToFile", is_checked)
        if is_checked:
            self._ui.file_path_line.setEnabled(True)
            self._ui.p_btn_open_file_dialog.setEnabled(True)
        else:
            self._ui.file_path_line.setEnabled(False)
            self._ui.p_btn_open_file_dialog.setEnabled(False)

    @Slot(bool)  # type: ignore
    def _toggle_continuous(self, is_checked: bool) -> None:
        run_conf.add("continuous", is_checked)
        self._ui.spinbox_number_measuring.setDisabled(is_checked)

    @staticmethod
    def _change_graph_show_state(item: QStandardItem) -> None:
        measurement = item.text()
        if item.column() != 0:
            return
        parameters_saved = run_conf.get("graphShowStates")
        if parameters_saved is None:
            parameters_saved = {}
        parameters_saved.update({measurement: item.checkState() == Qt.CheckState.Checked})
        run_conf.add("graphShowStates", parameters_saved)

    @staticmethod
    def _change_graph_number_of_plots(item: QStandardItem) -> None:
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
        parameter_saved = run_conf.get("graphNumberOfPlots")
        if parameter_saved is None:
            parameter_saved = {}
        parameters = parameter_saved.update({measurement: number_of_plots})
        run_conf.add("graphNumberOfPlots", parameters)

    def _update_graph_tree_model(self, parameters: dict[str, dict]) -> None:
        self._ui.graph_value_model.clear()
        for name, info in parameters.items():
            name_item, unit_item = QStandardItem(name), QStandardItem(f"[{info.pop('Unit')}]")
            plot_numbers = run_conf.get("graphNumberOfPlots")
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
        for device_statuse in api.get_device_statuses():
            device_tab = api.window.workspace.get_device_tab(device_statuse.name)
            if device_tab is None or not device_tab.isEnabled() or not device_tab.device_enable:
                continue
            _parameters = device_tab.get_parameters()
            if _parameters is None:
                continue
            for name, unit in _parameters.items():
                parameters.update({name: {"Unit": unit, "State": True, "Number": 100}})

        # Marge saved parameters
        show_states_saved = run_conf.get("graphShowStates")
        if show_states_saved is not None:
            for key, value in show_states_saved.items():
                if parameters.get(key) is None:
                    continue
                parameters[key].update({"State": value, "Number": 100})

        number_of_plots_saved = run_conf.get("graphNumberOfPlots")
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
        self.file_path_line = PathLineEdit(win)
        self.p_btn_open_file_dialog = api.qt_helpers.create_push_button(icon=qta.icon("mdi.folder-open-outline"))
        self.spinbox_interval = QSpinBox()
        self.radiobutton_continuous = QRadioButton("Continuous")
        self.radiobutton_interval = QRadioButton("Measuring Interval")
        self.spinbox_number_measuring = QSpinBox()
        self.treeview_graph = QTreeView()
        self.p_btn_reload_tree_view = api.qt_helpers.create_push_button(icon=qta.icon("mdi6.reload"), text="Reload")

        self.group_save_to_file = QGroupBox("Save to File")
        self.group_graph = QGroupBox("Graph")

        self.graph_value_model = QStandardItemModel()

        # Setup
        self.spinbox_interval.setRange(1, 100000)
        self.treeview_graph.setModel(self.graph_value_model)
        self.treeview_graph.setFixedHeight(240)
        self.treeview_graph.setAlternatingRowColors(True)
        self.treeview_graph.setStyleSheet("QHeaderView::section:first {padding-left: 50px;}")

        # Layout
        self.group_save_to_file.setCheckable(True)
        h_layout_save = api.qt_helpers.create_h_box_layout([self.file_path_line, self.p_btn_open_file_dialog])
        self.group_save_to_file.setLayout(h_layout_save)

        group_interval = QGroupBox("Interval")
        f_layout_interval = QFormLayout()
        f_layout_interval.addRow("Measuring Interval", api.qt_helpers.add_unit(self.spinbox_interval, "msec"))
        group_interval.setLayout(f_layout_interval)

        group_number_of_times = QGroupBox("Number of times")
        f_layout = QFormLayout()
        f_layout.addRow(self.radiobutton_continuous)
        f_layout.addRow(self.radiobutton_interval, api.qt_helpers.add_unit(self.spinbox_number_measuring, "times"))
        group_number_of_times.setLayout(f_layout)

        self.group_graph.setCheckable(True)
        self.group_graph.setLayout(
            api.qt_helpers.create_v_box_layout([self.p_btn_reload_tree_view, self.treeview_graph])
        )

        v_layout_setting = api.qt_helpers.create_v_box_layout(
            [self.group_save_to_file, group_interval, group_number_of_times, self.group_graph]
        )

        api.qt_helpers.create_v_box_layout([QLabel("This setting is automatically saved."), v_layout_setting], win)
