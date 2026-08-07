"""Frequency Key Studio (RGCS Sonic Lab): the Design Studio panel.

One top-level tab hosting the studio's pages (New Session, Recipe
Library, Web Corpus) as internal sub-tabs — the same workspace, jobs
dock, and inspector as every other Design Studio panel. Timeline editor
and layer mixer are v1.1 features (PRD) and deliberately absent."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout

from rgcs_desktop.services.sonic_recipes import (USER_NOTE, load_recipes)
from rgcs_desktop.viewers.base import Panel
from rgcs_desktop.viewers.sonic_new_session import NewSessionPage
from rgcs_desktop.viewers.sonic_recipe_library import RecipeLibraryPage
from rgcs_desktop.viewers.sonic_web_corpus import WebCorpusPage


class FrequencyKeyStudioPanel(Panel):
    TITLE = "Frequency Key Studio"

    def __init__(self, context, parent=None):
        super().__init__(context, parent)
        layout = QVBoxLayout(self)
        heading = QLabel("RGCS Frequency Key Studio — Sonic Lab")
        heading.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(heading)

        self.pages = QTabWidget()
        self.new_session = NewSessionPage(context, self._log)
        self.recipe_library = RecipeLibraryPage(context, self._log)
        self.web_corpus = WebCorpusPage(context, self._log)
        self.pages.addTab(self.new_session, "New Session")
        self.pages.addTab(self.recipe_library, "Recipe Library")
        self.pages.addTab(self.web_corpus, "Web Corpus")
        self.pages.currentChanged.connect(
            lambda *_: self.inspector_changed.emit())
        layout.addWidget(self.pages, stretch=1)

    def _log(self, message: str) -> None:
        self.status_message.emit(f"sonic: {message}")
        self.inspector_changed.emit()

    def inspector_info(self):
        session = self.new_session.current_session() or {}
        exports = self.new_session.last_exports
        return {"properties": {
                    "seed recipes": len(load_recipes()),
                    "current session": session.get("session_id", "—"),
                    "session type": session.get("family", "—"),
                    "duration (min)":
                        (session.get("duration_s", 0) or 0) / 60.0,
                    "last render": str(exports.get("wav", "—")),
                },
                "classification": "Model output (rendered audio recipe)",
                "units": "Hz / s / dB",
                "provenance": USER_NOTE + " Claimed uses are recorded "
                              "from sources, not endorsed."}
