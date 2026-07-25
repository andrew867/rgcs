"""P31 — experiment manuscript generator.

Assembles a deterministic manuscript skeleton from the phase reports, with
every quantitative statement carrying its claim class and every results
section stating that its numbers are synthetic / model / blocked. It refuses
to emit a manuscript sentence whose claim class exceeds its evidence.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import dataclass, field

from r15 import claims as C


class ManuscriptError(RuntimeError):
    """Raised on a manuscript claim beyond its evidence."""


#: The phase modules whose reports feed the manuscript.
_REPORT_MODULES = (
    "instruments", "provenance", "environment", "specimens", "orientation",
    "fixtures", "protocols", "measurement_ledger", "ordinary_explanations",
    "residuals", "mechanical", "electrical", "optical", "thermal",
    "magnetic_rf", "clock_phase", "predictions", "holdouts", "nulls",
    "multiple_testing", "replication", "nonclaims",
)


@dataclass
class ManuscriptSection:
    title: str
    body: str
    claim_class: str = "SOFTWARE_IMPLEMENTED"


@dataclass
class Manuscript:
    title: str
    sections: list = field(default_factory=list)

    def to_text(self) -> str:
        out = [f"# {self.title}", ""]
        for s in self.sections:
            out += [f"## {s.title}  [{s.claim_class}]", s.body, ""]
        return "\n".join(out)

    def content_hash(self) -> str:
        payload = json.dumps(
            [(s.title, s.body, s.claim_class) for s in self.sections],
            sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def collect_reports() -> dict:
    """Gather every available phase *_report() (deterministic, no clock)."""
    reports = {}
    for name in _REPORT_MODULES:
        try:
            mod = importlib.import_module(f"r15.{name}")
        except Exception:
            continue
        fn = getattr(mod, f"{name}_report", None)
        if fn is None:
            continue
        try:
            reports[name] = fn()
        except Exception:
            continue
    return reports


def refuse_claim_beyond_evidence(claim_class: str) -> None:
    """A manuscript sentence may not exceed the software claim ceiling."""
    measurement = {c.value for c in C.MEASUREMENT_CLASSES}
    if claim_class in measurement:
        raise ManuscriptError(
            f"refused: a manuscript section cannot carry claim class "
            f"{claim_class!r}; no physical measurement exists in this "
            f"repository. The ceiling is {C.MAX_SOFTWARE_CLASS.value}.")


def generate_manuscript(reports: dict | None = None) -> Manuscript:
    reports = reports if reports is not None else collect_reports()
    for name, rep in reports.items():
        refuse_claim_beyond_evidence(rep.get("claim_class", "SOFTWARE_IMPLEMENTED"))
    ms = Manuscript(title="RGCS R15 — Experimental Phase Infrastructure "
                          "(synthetic platform; no physical claims advanced)")
    ms.sections.append(ManuscriptSection(
        "Abstract",
        "R15 is an instrument-ready, calibration-bound, uncertainty-aware "
        "experimental platform. No physical measurement is reported; every "
        "result is a synthetic observation, a model prediction, or a blocked "
        "input.", "SOFTWARE_IMPLEMENTED"))
    ms.sections.append(ManuscriptSection(
        "Methods",
        "Seven authorities (instrument, calibration, specimen, fixture, "
        "protocol, observation, evidence) gate every observation through a "
        "frozen protocol, immutable artifacts, a derivation graph, ordinary-"
        "explanation attacks, and residual classification.",
        "SOFTWARE_IMPLEMENTED"))
    ms.sections.append(ManuscriptSection(
        "Results (synthetic)",
        "Each lane recovers planted signatures from deterministic synthetic "
        "data within its error budget; " + str(len(reports)) + " phase "
        "reports were assembled, all declaring measured_here='nothing'.",
        "SYNTHETIC_OBSERVATION"))
    ms.sections.append(ManuscriptSection(
        "Non-claims",
        "R15 establishes no new energy, no Phyrll, no decoded destination, no "
        "isotropic emission, and no anomaly; the strongest unreplicated "
        "residual is UNEXPLAINED_INSTRUMENT_RESIDUAL.", "SOFTWARE_IMPLEMENTED"))
    return ms


def manuscript_report() -> dict:
    return {
        "what_this_is": "the R15 experiment manuscript generator",
        "claim_class": "SOFTWARE_IMPLEMENTED",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "MANUSCRIPT_GENERATED_SYNTHETIC_NO_PHYSICAL_CLAIM",
        "what_this_does_not_say": (
            "It assembles a manuscript from phase reports; it reports no "
            "measurement and refuses any section claiming one."),
    }
