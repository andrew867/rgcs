"""Application settings via QSettings (layout persistence, units, paths)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

ORG = "RGCS"
APP = "rgcs_desktop"


class AppSettings:
    def __init__(self):
        self._qs = QSettings(ORG, APP)

    # layout ------------------------------------------------------------
    def save_layout(self, geometry: bytes, state: bytes) -> None:
        self._qs.setValue("main/geometry", geometry)
        self._qs.setValue("main/state", state)

    def layout(self) -> tuple[object, object]:
        return (self._qs.value("main/geometry"),
                self._qs.value("main/state"))

    # preferences ---------------------------------------------------------
    @property
    def frequency_unit(self) -> str:
        return str(self._qs.value("units/frequency", "Hz"))

    @frequency_unit.setter
    def frequency_unit(self, value: str) -> None:
        self._qs.setValue("units/frequency", value)

    @property
    def default_workspace_dir(self) -> str:
        return str(self._qs.value("paths/workspaces",
                                  str(Path.home() / "rgcs_workspaces")))

    @default_workspace_dir.setter
    def default_workspace_dir(self, value: str) -> None:
        self._qs.setValue("paths/workspaces", value)

    @property
    def last_workspace(self) -> str | None:
        v = self._qs.value("paths/last_workspace")
        return str(v) if v else None

    @last_workspace.setter
    def last_workspace(self, value: str) -> None:
        self._qs.setValue("paths/last_workspace", value)

    # first-run wizard ----------------------------------------------------
    @property
    def first_run_done(self) -> bool:
        return self._qs.value("app/first_run_done", False, type=bool)

    @first_run_done.setter
    def first_run_done(self, value: bool) -> None:
        self._qs.setValue("app/first_run_done", bool(value))
