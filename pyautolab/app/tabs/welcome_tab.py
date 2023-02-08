from qtpy.QtWidgets import QCheckBox, QFormLayout, QLabel, QSizePolicy, QWidget

from pyautolab.app.app import App
from pyautolab.core import qt


class WelcomeTab(QWidget):
    def __init__(self) -> None:
        super().__init__()

        # Widgets
        self._btn_open_device_manager = qt.helper.push_button(
            clicked=lambda: App.actions.execute("window.openDeviceManager"), text="Connect Device..."
        )
        self._btn_open_run_conf = qt.helper.push_button(
            clicked=lambda: App.actions.execute("window.openRunConfiguration"), text="Open Run Configuration..."
        )
        self._btn_start_controlling = qt.helper.push_button(
            clicked=lambda: App.actions.execute("runner.run"), text="Start Controlling Device..."
        )
        self._check_box = QCheckBox("Show welcome page on startup")

        # Setup signal slot
        self._check_box.stateChanged.connect(  # type: ignore
            lambda is_checked: App.configurations.add("workspace.welcomeTab", is_checked)
        )
        self._check_box.setChecked(True)

        # Setup UI
        self._btn_open_device_manager.setFlat(True)
        self._btn_open_run_conf.setFlat(True)
        self._btn_start_controlling.setFlat(True)

        # Setup layout
        self._btn_open_device_manager.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._btn_open_run_conf.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._btn_start_controlling.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        f_layout = QFormLayout()
        f_layout.addRow(QLabel("<h3>Get Started</h3>"))
        f_layout.addRow("1. ", self._btn_open_device_manager)
        f_layout.addRow("2. ", QLabel("Edit the device settings in each device tab."))
        f_layout.addRow("3. ", self._btn_open_run_conf)
        f_layout.addRow("4. ", self._btn_start_controlling)

        qt.helper.layout(
            f_layout,
            self._check_box,
            parent=self,
        )
