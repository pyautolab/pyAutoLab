import qtawesome as qta
from qtpy.QtCore import Qt, Slot  # type: ignore
from qtpy.QtWidgets import QMessageBox, QToolButton

from pyautolab import api
from pyautolab.plugins.runner.run_conf import RunConf
from pyautolab.plugins.runner.tabs.analysis_tab import AnalysisWidget
from pyautolab.plugins.runner.tabs.conf_tab import RunConfTab


@Slot()
def run() -> None:
    if RunConf().get("openFlag") is None:
        result = api.window.show_warning_message(
            "Message",
            "The first time you run, you need to customize Run configuration.",
            QMessageBox.StandardButton.Open,
        )
        if result == QMessageBox.StandardButton.Open:
            open_run_conf_tab()
        return

    tab_name = "Analysis"
    tab_num = 1
    while api.window.workspace.get_tab(f"{tab_name} {tab_num}") is not None:
        tab_num += 1
    tab_title = f"{tab_name} {tab_num}"
    api.window.workspace.add_tab(AnalysisWidget(tab_title), tab_title)


@Slot()
def open_run_conf_tab() -> None:
    run_conf_tab = RunConfTab()
    api.window.workspace.add_tab(run_conf_tab, "Run Configuration", True)


def main() -> None:
    action_run = api.window.create_window_action(
        text="Run",
        enable=True,
        shortcut="F5",
        icon=qta.icon("ph.play", color="green"),
        triggered=run,
    )
    action_open_run_conf_tab = api.window.create_window_action(
        text="Run Configuration",
        icon=qta.icon("fa.cog"),
        triggered=open_run_conf_tab,
    )
    t_btn_open_menu = api.qt_helpers.create_tool_button(icon=qta.icon("ph.play", color="green"))

    # Setup tool button
    # Fix bug the hover state continues even if the cursor is released
    t_btn_open_menu.triggered.connect(lambda: t_btn_open_menu.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, False))
    t_btn_open_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    t_btn_open_menu.addActions([action_run, action_open_run_conf_tab])
    api.window.toolbar.add_widget(t_btn_open_menu)

    # Setup menu bar
    api.window.menubar.add_action_to_run_menu(action_run)
    api.window.menubar.add_action_to_run_menu(action_open_run_conf_tab)
