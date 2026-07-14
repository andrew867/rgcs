"""Classification badges, Source-claim banners, uncertainty labels.

Binding requirement: classification badges (Established / Derived /
Hypothesis / Source claim) on every claim-bearing display; source presets
render under Source-claim banners; UncertainValue rendered as interval.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from rgcs_core.uncertainty import UncertainValue

from rgcs_desktop.services.formatting import (CLASSIFICATION_COLORS,
                                              classification_label,
                                              format_uncertain)


class ClassificationBadge(QLabel):
    """Colored pill showing a classification string (label + registry ids)."""

    def __init__(self, classification: str = "Derived", parent=None):
        super().__init__(parent)
        self.setObjectName("classificationBadge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_classification(classification)

    def set_classification(self, classification: str) -> None:
        self._classification = classification
        label = classification_label(classification)
        color = CLASSIFICATION_COLORS[label]
        self.setText(classification)
        self.setToolTip(
            f"Classification per docs/SCIENTIFIC_CLASSIFICATION_POLICY.md: "
            f"{classification}")
        self.setStyleSheet(
            f"QLabel#classificationBadge {{ background: {color}; "
            f"color: white; border-radius: 7px; padding: 2px 8px; "
            f"font-weight: bold; }}")

    @property
    def label(self) -> str:
        return classification_label(self._classification)


class SourceClaimBanner(QLabel):
    """Banner shown above any content taken verbatim from source material."""

    DEFAULT_TEXT = ("SOURCE CLAIM — values below are reproduced from source "
                    "material and are not independently verified "
                    "(docs/SCIENTIFIC_CLASSIFICATION_POLICY.md).")

    def __init__(self, text: str | None = None, parent=None):
        super().__init__(text or self.DEFAULT_TEXT, parent)
        self.setObjectName("sourceClaimBanner")
        self.setWordWrap(True)
        color = CLASSIFICATION_COLORS["Source claim"]
        self.setStyleSheet(
            f"QLabel#sourceClaimBanner {{ background: {color}; color: white; "
            f"padding: 6px 10px; border-radius: 4px; font-weight: bold; }}")


class UncertainValueLabel(QLabel):
    """Renders an UncertainValue as 'mean ± sigma [lo, hi] (1σ)' —
    never a bare point value."""

    def __init__(self, value: UncertainValue | dict | None = None,
                 unit: str = "", parent=None):
        super().__init__(parent)
        self._unit = unit
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        if value is not None:
            self.set_value(value)

    def set_value(self, value: UncertainValue | dict) -> None:
        self.setText(format_uncertain(value, self._unit))
