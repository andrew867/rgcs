"""P33 — statistical and methods appendices.

Assembles the statistical/methods appendix from the T6 statistical-firewall
phases (null models, multiple-comparison control, holdout policy,
circularity audit, replication). Every appendix entry must reference a
declared null model; an appendix that reports a result with no null is
refused.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field


class AppendixError(RuntimeError):
    """Raised on an appendix entry with no null model."""


@dataclass(frozen=True)
class AppendixEntry:
    section: str
    method: str
    null_model: str
    correction: str

    def __post_init__(self) -> None:
        if not self.null_model:
            raise AppendixError(
                f"refused: appendix section {self.section!r} reports a method "
                f"with no null model; without a null (proven to have power) a "
                f"result is not interpretable.")


def _has(name: str) -> bool:
    try:
        importlib.import_module(f"r15.{name}")
        return True
    except Exception:
        return False


def build_appendix() -> list:
    """The methods appendix, drawn from the T6 phases that exist."""
    entries = []
    if _has("nulls"):
        entries.append(AppendixEntry(
            "Null models", "permutation / surrogate null with power on "
            "planted data", "registered per effect (P21)", "n/a"))
    if _has("multiple_testing"):
        entries.append(AppendixEntry(
            "Multiple comparisons", "Bonferroni / Holm / Benjamini-Hochberg "
            "and alpha-spending sequential analysis (P23)",
            "family-wise / FDR null", "FWER + FDR"))
    if _has("holdouts"):
        entries.append(AppendixEntry(
            "Holdout policy", "sealed, one-shot holdout scoring (P20)",
            "holdout null", "pre-committed"))
    if _has("circularity"):
        entries.append(AppendixEntry(
            "Leakage audit", "train/test, double-dipping, target and temporal "
            "leakage detectors (P22)", "clean-pipeline null", "n/a"))
    return entries


def refuse_appendix_without_null(section: str = "") -> None:
    raise AppendixError(
        f"refused: appendix section {section!r} needs a declared null model.")


def appendices_report() -> dict:
    return {
        "what_this_is": "the R15 statistical and methods appendices generator",
        "claim_class": "SOFTWARE_IMPLEMENTED",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "STATISTICAL_METHODS_APPENDICES_ASSEMBLED",
        "what_this_does_not_say": (
            "It assembles the methods appendix from the statistical-firewall "
            "phases; it performs no test on physical data."),
    }
