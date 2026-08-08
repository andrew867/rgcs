"""Design Studio home: task cards that answer "what do you want to do?"
and route into the guided panels (or Advanced Mode)."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from rgcs_desktop.services.design_studio import WORKFLOWS
from rgcs_desktop.viewers.base import Panel


class TaskCard(QFrame):
    def __init__(self, workflow: dict, parent=None):
        super().__init__(parent)
        self.workflow = workflow
        self.setObjectName("taskCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "QFrame#taskCard { border: 1px solid #999; border-radius: 6px; "
            "padding: 4px; }")
        layout = QVBoxLayout(self)
        self.button = QPushButton(workflow["card"])
        self.button.setObjectName(f"card_{workflow['key']}")
        layout.addWidget(self.button)
        detail = QLabel(f"needs: {workflow['inputs']}\n"
                        f"makes: {workflow['outputs']}")
        detail.setWordWrap(True)
        layout.addWidget(detail)


class DesignStudioHomePanel(Panel):
    TITLE = "Design Studio"

    #: emitted with the target panel title when a card is activated
    navigate = Signal(str)

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        outer = QVBoxLayout(self)
        heading = QLabel("RGCS Design Studio")
        heading.setStyleSheet("font-size: 20px; font-weight: bold;")
        outer.addWidget(heading)
        outer.addWidget(QLabel("What do you want to do?"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        grid = QGridLayout(inner)
        self.cards: list[TaskCard] = []
        for i, wf in enumerate(WORKFLOWS):
            card = TaskCard(wf)
            card.button.clicked.connect(
                lambda _=False, panel=wf["panel"]: self.navigate.emit(panel))
            grid.addWidget(card, i // 2, i % 2)
            self.cards.append(card)
        grid.setRowStretch((len(WORKFLOWS) + 1) // 2, 1)
        scroll.setWidget(inner)
        outer.addWidget(scroll, stretch=1)

        hint = QLabel(
            "Every workflow exports a JSON receipt, a PDF sheet with a "
            "claim boundary, and checksums. Receipts, jobs, and warnings "
            "appear in the dock below.")
        hint.setWordWrap(True)
        outer.addWidget(hint)

    def inspector_info(self):
        return {
            "properties": {
                "workflows": len(WORKFLOWS),
                "golden path": "Crystal Validator -> Certification Sheet "
                               "-> Phryll Generator v2 -> Coil and Pulse "
                               "-> Export Bundle",
            },
            "classification": "Derived (navigation metadata)",
            "units": "n/a",
            "provenance": "rgcs_desktop.services.design_studio.WORKFLOWS",
        }
