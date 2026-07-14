"""Panel base class: tab title, inspector protocol, workspace access."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget


class Panel(QWidget):
    """Base for all workbench tabs.

    * ``TITLE``: tab caption.
    * :meth:`inspector_info`: dict rendered by the right-hand inspector
      (keys: properties, classification, units, provenance).
    * ``inspector_changed``: emitted when the inspector should refresh.
    """

    TITLE = "Panel"
    inspector_changed = Signal()
    status_message = Signal(str)

    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context  # AppContext (workspace, job manager, settings)

    def inspector_info(self) -> dict[str, Any]:
        return {"properties": {}, "classification": "",
                "units": "", "provenance": ""}

    def refresh(self) -> None:
        """Called when the workspace contents changed."""
