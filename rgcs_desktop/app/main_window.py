"""Main window: sidebar, tabbed workspace, inspector, jobs dock,
command palette, persistent layout (QSettings)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QDockWidget, QFileDialog, QInputDialog,
                               QMainWindow, QMessageBox, QTabWidget,
                               QTreeWidget, QTreeWidgetItem)

from rgcs_desktop.app.command_palette import CommandPalette
from rgcs_desktop.app.context import AppContext
from rgcs_desktop.app.inspector import InspectorDock
from rgcs_desktop.app.jobs_panel import JobsPanel
from rgcs_desktop.viewers.avoided_crossing import AvoidedCrossingPanel
from rgcs_desktop.viewers.evidence_ledger_panel import EvidenceLedgerPanel
from rgcs_desktop.viewers.coherence_analyzer import CoherenceAnalyzerPanel
from rgcs_desktop.viewers.comparison_view import ComparisonPanel
from rgcs_desktop.viewers.experiment_builder import ExperimentBuilderPanel
from rgcs_desktop.viewers.model_editor import ModelEditorPanel
from rgcs_desktop.viewers.pulse_designer import PulseDesignerPanel
from rgcs_desktop.viewers.report_panel import ReportPanel
from rgcs_desktop.viewers.results_browser import ResultsBrowserPanel
from rgcs_desktop.viewers.settings_panel import SettingsPanel
from rgcs_desktop.viewers.source_library import SourceLibraryPanel
from rgcs_desktop.viewers.specimen_editor import SpecimenEditorPanel
from rgcs_desktop.viewers.spectrum_panel import SpectrumPanel
from rgcs_desktop.viewers.workspace_browser import WorkspaceBrowserPanel

PANEL_CLASSES = [
    WorkspaceBrowserPanel, SourceLibraryPanel, SpecimenEditorPanel,
    ModelEditorPanel, SpectrumPanel, AvoidedCrossingPanel,
    CoherenceAnalyzerPanel, PulseDesignerPanel, ExperimentBuilderPanel,
    ResultsBrowserPanel, ComparisonPanel, ReportPanel, SettingsPanel,
    EvidenceLedgerPanel,
]

SIDEBAR_SECTIONS = ["Workspaces", "Specimens", "Models", "Experiments",
                    "Sources", "Results"]


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RGCS v2 — Research Workbench")
        self.resize(1440, 900)
        self.context = context or AppContext()
        self.context.workspace_changed.connect(self._workspace_changed)

        # central tabbed workspace
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.setMovable(True)
        self.tabs.currentChanged.connect(self._update_inspector)
        self.setCentralWidget(self.tabs)

        # left sidebar
        self.sidebar = QTreeWidget()
        self.sidebar.setHeaderLabel("Workspace")
        self.sidebar.itemActivated.connect(self._sidebar_activated)
        left_dock = QDockWidget("Navigator", self)
        left_dock.setObjectName("navigatorDock")
        left_dock.setWidget(self.sidebar)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)

        # right inspector
        self.inspector = InspectorDock()
        right_dock = QDockWidget("Inspector", self)
        right_dock.setObjectName("inspectorDock")
        right_dock.setWidget(self.inspector)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_dock)

        # bottom jobs/log dock
        self.jobs_panel = JobsPanel(self.context.job_manager)
        bottom_dock = QDockWidget("Jobs / Logs / Warnings", self)
        bottom_dock.setObjectName("jobsDock")
        bottom_dock.setWidget(self.jobs_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea,
                           bottom_dock)

        # panels
        self.panels: dict[str, object] = {}
        for cls in PANEL_CLASSES:
            panel = cls(self.context)
            panel.inspector_changed.connect(self._update_inspector)
            panel.status_message.connect(self.jobs_panel.log)
            self.panels[cls.TITLE] = panel
            self.tabs.addTab(panel, cls.TITLE)

        # command palette + actions
        self._actions = self._build_actions()
        palette_action = QAction("Command palette", self)
        palette_action.setShortcut(QKeySequence("Ctrl+K"))
        palette_action.triggered.connect(self.show_command_palette)
        self.addAction(palette_action)

        # job queue pump
        self._job_timer = QTimer(self)
        self._job_timer.setInterval(150)
        self._job_timer.timeout.connect(self.context.job_manager.poll)
        self._job_timer.start()

        self._restore_layout()
        self._refresh_sidebar()
        self._update_inspector()

    # -- actions / palette -------------------------------------------------
    def _build_actions(self) -> dict:
        actions: dict = {}
        for title in self.panels:
            actions[f"Open panel: {title}"] = (
                lambda t=title: self.open_panel(t))
        actions["Workspace: create…"] = self._create_workspace_dialog
        actions["Workspace: open…"] = self._open_workspace_dialog
        actions["Report: generate markdown"] = (
            lambda: self.panels["Report / export"].generate())
        actions["Export: reproducibility bundle"] = (
            lambda: self.panels["Report / export"].export())
        actions["Spectrum: compute"] = (
            lambda: self.panels["Compact-mode spectrum"].compute())
        actions["Jobs: run trivial demo job"] = (
            lambda: self.context.job_manager.submit(
                "trivial", {"steps": 5}, name="demo job"))
        return actions

    def command_names(self) -> list[str]:
        return sorted(self._actions)

    def run_command(self, name: str) -> None:
        self._actions[name]()

    def show_command_palette(self) -> None:
        CommandPalette(self._actions, self).exec()

    def open_panel(self, title: str) -> None:
        panel = self.panels[title]
        self.tabs.setCurrentWidget(panel)

    # -- workspace ------------------------------------------------------
    def _create_workspace_dialog(self) -> None:
        root = QFileDialog.getExistingDirectory(self, "Workspace directory")
        if not root:
            return
        name, ok = QInputDialog.getText(self, "Workspace name", "Name:")
        if ok and name:
            self.context.create_workspace(Path(root) / name, name)

    def _open_workspace_dialog(self) -> None:
        root = QFileDialog.getExistingDirectory(self, "Open workspace")
        if not root:
            return
        from rgcs_desktop.workspaces import Workspace, WorkspaceError
        try:
            self.context.open_workspace(root)
        except WorkspaceError as exc:
            # QA-D-05: surface corruption and offer a backup restore
            # instead of crashing.
            n_backups = len(Workspace.list_backups(root))
            if n_backups == 0:
                QMessageBox.critical(self, "Workspace error", str(exc))
                return
            ans = QMessageBox.question(
                self, "Workspace damaged",
                f"{exc}\n\n{n_backups} backup(s) exist for this "
                f"workspace. Restore the newest intact backup?\n"
                f"(The damaged file is kept as workspace.db.corrupt-*.)")
            if ans != QMessageBox.StandardButton.Yes:
                return
            try:
                Workspace.restore_latest_backup(root).close()
                self.context.open_workspace(root)
            except WorkspaceError as exc2:
                QMessageBox.critical(self, "Restore failed", str(exc2))

    def _workspace_changed(self) -> None:
        for panel in self.panels.values():
            panel.refresh()
        self._refresh_sidebar()

    def _refresh_sidebar(self) -> None:
        self.sidebar.clear()
        ws = self.context.workspace
        for section in SIDEBAR_SECTIONS:
            item = QTreeWidgetItem([section])
            self.sidebar.addTopLevelItem(item)
            if ws is None:
                continue
            if section == "Workspaces":
                item.addChild(QTreeWidgetItem([f"{ws.name} ({ws.root})"]))
            else:
                kind = section.lower().rstrip("s")  # Specimens -> specimen
                for o in ws.list_objects(kind):
                    child = QTreeWidgetItem([f"{o['name']}"])
                    child.setData(0, Qt.ItemDataRole.UserRole,
                                  (kind, o["object_id"]))
                    item.addChild(child)
        self.sidebar.expandAll()

    def _sidebar_activated(self, item: QTreeWidgetItem, _col: int) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        mapping = {"specimen": "Specimen editor", "model": "Models",
                   "experiment": "Experiment builder", "source": "Sources",
                   "result": "Results"}
        if data is not None:
            kind, _oid = data
            if kind in mapping:
                self.open_panel(mapping[kind])
        elif item.text(0) in ("Workspaces",):
            self.open_panel("Workspace")

    # -- inspector -----------------------------------------------------------
    def _update_inspector(self, *_args) -> None:
        panel = self.tabs.currentWidget()
        if panel is not None and hasattr(panel, "inspector_info"):
            self.inspector.show_info(panel.inspector_info())

    # -- layout persistence ---------------------------------------------------
    def _restore_layout(self) -> None:
        geometry, state = self.context.settings.layout()
        if geometry is not None:
            self.restoreGeometry(geometry)
        if state is not None:
            self.restoreState(state)

    def closeEvent(self, event) -> None:
        self.context.settings.save_layout(bytes(self.saveGeometry()),
                                          bytes(self.saveState()))
        self._job_timer.stop()
        self.context.shutdown()
        super().closeEvent(event)
