"""AppContext: shared state handed to every panel (workspace, jobs, settings)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from rgcs_desktop.jobs import JobManager
from rgcs_desktop.settings import AppSettings
from rgcs_desktop.workspaces import Workspace


class AppContext(QObject):
    workspace_changed = Signal()

    def __init__(self, workspace: Workspace | None = None, parent=None):
        super().__init__(parent)
        self.settings = AppSettings()
        self.workspace: Workspace | None = workspace
        self.job_manager = JobManager(workspace)

    def open_workspace(self, root: str | Path) -> Workspace:
        if self.workspace is not None:
            self.workspace.close()
        self.workspace = Workspace.open(root)
        self.job_manager.workspace = self.workspace
        self.settings.last_workspace = str(root)
        self.workspace_changed.emit()
        return self.workspace

    def create_workspace(self, root: str | Path, name: str) -> Workspace:
        if self.workspace is not None:
            self.workspace.close()
        self.workspace = Workspace.create(root, name)
        self.job_manager.workspace = self.workspace
        self.settings.last_workspace = str(root)
        self.workspace_changed.emit()
        return self.workspace

    def notify_workspace_changed(self) -> None:
        self.workspace_changed.emit()

    def shutdown(self) -> None:
        self.job_manager.shutdown()
        if self.workspace is not None:
            self.workspace.close()
            self.workspace = None
