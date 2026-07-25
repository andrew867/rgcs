"""P32 — figure and evidence-package generator."""

from __future__ import annotations

import pytest

from r15 import figures as F


def test_default_package_builds_with_provenance_and_hashes():
    pkg = F.default_package()
    assert len(pkg.figures) >= 3
    assert all(fig.provenance for fig in pkg.figures)
    assert pkg.content_hash() == F.default_package().content_hash()


def test_figure_without_provenance_is_refused():
    with pytest.raises(F.FigureError):
        F.FigureSpec("Fx", "spectrum", "Synthetic data.", "", "ref")
    with pytest.raises(F.FigureError):
        F.refuse_figure_without_provenance("Fx")


def test_figure_caption_must_state_synthetic():
    with pytest.raises(F.FigureError):
        F.FigureSpec("Fy", "spectrum", "A measured resonance.", "P14", "ref")


def test_report_claims_nothing_measured():
    r = F.figures_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
