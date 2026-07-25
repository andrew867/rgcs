"""P32 — figure and evidence-package generator.

Builds deterministic figure *descriptors* (not rendered images) for the
evidence package. Every figure must name its data provenance (which phase /
artifact produced its data) and carry a caption stating the data are
synthetic; a figure without provenance is refused.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


class FigureError(RuntimeError):
    """Raised on a figure with no data provenance."""


@dataclass(frozen=True)
class FigureSpec:
    figure_id: str
    kind: str            # e.g. "spectrum", "sweep", "residual_hist"
    caption: str
    provenance: str      # phase id / artifact hash the data came from
    data_ref: str        # a synthetic-data reference or content hash

    def __post_init__(self) -> None:
        if not self.provenance:
            raise FigureError(
                f"refused: figure {self.figure_id!r} has no data provenance; "
                f"a figure with no traceable source is not evidence.")
        if "synthetic" not in self.caption.lower():
            raise FigureError(
                f"refused: figure {self.figure_id!r} caption must state the "
                f"data are synthetic (no physical measurement exists).")


@dataclass
class EvidencePackage:
    package_id: str
    figures: list = field(default_factory=list)

    def add(self, fig: FigureSpec) -> None:
        self.figures.append(fig)

    def manifest(self) -> dict:
        return {
            "package_id": self.package_id,
            "figures": [
                {"figure_id": f.figure_id, "kind": f.kind,
                 "provenance": f.provenance, "data_ref": f.data_ref}
                for f in self.figures],
        }

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.manifest(), sort_keys=True).encode("utf-8")
        ).hexdigest()


def refuse_figure_without_provenance(figure_id: str = "") -> None:
    raise FigureError(
        f"refused: figure {figure_id!r} needs data provenance (a phase id or "
        f"artifact hash); an unsourced figure is not evidence.")


def default_package() -> EvidencePackage:
    pkg = EvidencePackage(package_id="R15_EVIDENCE_PACKAGE")
    pkg.add(FigureSpec("F1", "spectrum",
                       "Synthetic BVD impedance sweep with planted resonance.",
                       "P14", "synthetic:electrical:seed0"))
    pkg.add(FigureSpec("F2", "residual_hist",
                       "Synthetic residual histogram within the error budget.",
                       "P12", "synthetic:residual:seed0"))
    pkg.add(FigureSpec("F3", "sweep",
                       "Synthetic mode-tracker trajectory across a sweep.",
                       "P29", "synthetic:tracker:seed1"))
    return pkg


def figures_report() -> dict:
    return {
        "what_this_is": "the R15 figure and evidence-package generator",
        "claim_class": "SOFTWARE_IMPLEMENTED",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "EVIDENCE_PACKAGE_SYNTHETIC_WITH_PROVENANCE",
        "what_this_does_not_say": (
            "It builds figure descriptors from synthetic data with "
            "provenance; no figure depicts a physical measurement."),
    }
