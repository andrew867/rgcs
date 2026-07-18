"""First-run workspace wizard (v4.5, P02).

Shown once, on the first launch with no prior workspace. It creates a
per-user workspace in the user's Documents (never a hardcoded personal
path) and, optionally, seeds a demo workspace by generating the Master
Evidence Workbook into it so a new visitor has something to open
immediately. It states the claim boundary plainly: nothing physical is
validated.

The wizard is intentionally headless-constructible (no exec) so it can
be smoke-tested offscreen.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox,
                               QLabel, QLineEdit, QPushButton, QVBoxLayout)


def default_workspace_dir() -> Path:
    """User's Documents\\RGCS Workspace — no hardcoded personal path."""
    import os
    prof = os.environ.get("USERPROFILE")
    base = Path(prof) / "Documents" if prof else Path.home()
    return base / "RGCS Workspace"


class FirstRunWizard(QDialog):
    def __init__(self, parent=None,
                 default_dir: Path | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to RGCS Workbench")
        self._chosen = default_dir or default_workspace_dir()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "RGCS Workbench keeps your data in a local workspace.\n"
            "No account, no network, no telemetry. This software shows "
            "arithmetic, models, and simulations only — it does not "
            "assert that any physical result has been validated."))
        layout.addWidget(QLabel("Workspace location:"))
        self.path_edit = QLineEdit(str(self._chosen))
        layout.addWidget(self.path_edit)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        layout.addWidget(browse)
        self.demo_check = QCheckBox(
            "Seed a demo workspace (generate the Master Evidence "
            "Workbook so I have something to open)")
        self.demo_check.setChecked(True)
        layout.addWidget(self.demo_check)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self) -> None:  # pragma: no cover (interactive)
        from PySide6.QtWidgets import QFileDialog
        d = QFileDialog.getExistingDirectory(
            self, "Choose workspace folder", str(self._chosen.parent))
        if d:
            self.path_edit.setText(str(Path(d) / "RGCS Workspace"))

    @property
    def workspace_path(self) -> Path:
        return Path(self.path_edit.text().strip() or str(self._chosen))

    @property
    def seed_demo(self) -> bool:
        return self.demo_check.isChecked()


def apply_first_run(context, root: Path, seed_demo: bool) -> Path:
    """Create the workspace the wizard chose and optionally seed the demo
    workbook. Pure of any dialog, so it is unit-testable and reusable by
    the headless self-test. Returns the workspace root."""
    root.mkdir(parents=True, exist_ok=True)
    context.create_workspace(root, root.name)
    if seed_demo:
        _seed_demo(root)
    return root


def run_first_run(context, parent=None) -> bool:
    """Show the wizard and apply the result. Returns True if a workspace
    was created. Records that the wizard has run either way so it does
    not reappear."""
    wiz = FirstRunWizard(parent)
    accepted = wiz.exec() == QDialog.Accepted
    context.settings.first_run_done = True
    if not accepted:
        return False
    apply_first_run(context, wiz.workspace_path, wiz.seed_demo)
    return True


def first_run_selftest(root: Path, seed_demo: bool = True) -> dict:
    """Headless equivalent of accepting the wizard at ``root``: create the
    workspace + optional demo seed, then report what exists. Used by the
    packaged regression test to verify wizard creation / demo / workbook
    without a GUI event loop. Never touches ``--first-run`` as a path."""
    from rgcs_desktop.app.context import AppContext
    context = AppContext()
    apply_first_run(context, root, seed_demo)
    wb = root / "RGCS_Master_Evidence_Workbook.xlsx"
    result = {
        "workspace_root": str(root),
        "workspace_db_exists": (root / "workspace.db").exists(),
        "workbook_seeded": wb.exists() and wb.stat().st_size > 0,
        "workspace_name": context.workspace.name
        if context.workspace else None,
    }
    context.shutdown()
    return result


def _seed_demo(root: Path) -> None:
    """Generate the public Master Evidence Workbook into the workspace so
    a first-time visitor has a concrete artifact to open. Best-effort:
    a missing openpyxl must not break first launch."""
    try:
        from rgcs_workbench.workbook import generate
        generate(include_private=False).save(
            root / "RGCS_Master_Evidence_Workbook.xlsx")
    except Exception:  # noqa: BLE001  (demo seed is optional)
        pass
