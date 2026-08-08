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
        self.last_factory_sync: dict | None = None

    def open_workspace(self, root: str | Path) -> Workspace:
        # Open FIRST: if it fails, the current workspace stays open and
        # usable instead of being left closed-but-referenced (v8.5.2
        # lifecycle fix).
        ws = Workspace.open(root)
        self._swap(ws, root)
        return self.workspace

    def create_workspace(self, root: str | Path, name: str) -> Workspace:
        # An existing workspace folder opens instead of raising
        # "workspace already exists" — first run and reinstalls must
        # never crash because the folder is already there.
        ws = Workspace.open_or_create(root, name)
        self._swap(ws, root)
        return self.workspace

    def close_workspace(self) -> None:
        """Close the current workspace: cancel running jobs, release the
        database, clear the last-workspace pointer."""
        if self.workspace is None:
            return
        for rec in self.job_manager.jobs():
            if not rec.status.terminal:
                self.job_manager.cancel(rec.job_id)
        self.workspace.close()
        self.workspace = None
        self.job_manager.workspace = None
        self.settings.last_workspace = ""
        self.workspace_changed.emit()

    def _swap(self, ws: Workspace, root: str | Path) -> None:
        old = self.workspace
        self.workspace = ws
        self.job_manager.workspace = ws
        if old is not None:
            old.close()
        self.settings.last_workspace = str(root)
        self._sync_factory_content(ws)
        self.workspace_changed.emit()

    def _sync_factory_content(self, ws: Workspace) -> None:
        """Install/refresh factory content (curated sessions). Idempotent
        and best-effort: content sync must never block opening."""
        try:
            from rgcs_desktop.services.factory_content import \
                sync_factory_content
            self.last_factory_sync = sync_factory_content(ws.root)
        except Exception:  # noqa: BLE001 (sync must never block open)
            self.last_factory_sync = None

    def notify_workspace_changed(self) -> None:
        self.workspace_changed.emit()

    def shutdown(self) -> None:
        self.job_manager.shutdown()
        if self.workspace is not None:
            self.workspace.close()
            self.workspace = None
