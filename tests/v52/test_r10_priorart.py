"""S05/S09 — conventional prior art from the supplied academic papers."""

from __future__ import annotations

import pytest

from r10 import priorart as P


def test_both_references_are_conventional_literature():
    for r in P.REFERENCES:
        assert r.evidence_class == "CONVENTIONAL_LITERATURE"
        assert r.doi


def test_a_reference_without_a_doi_is_refused():
    with pytest.raises(P.PriorArtError):
        P.Reference("x", "A", 2020, "t", "v", "",
                    "establishes", "limits")


def test_a_reference_cannot_claim_to_be_a_project_result():
    with pytest.raises(P.PriorArtError):
        P.Reference("x", "A", 2020, "t", "v", "10.1/x",
                    "establishes", "limits",
                    evidence_class="BENCH_MEASUREMENT")


# --- the firefly result is a correction, framed as one ----------------

def test_the_firefly_number_is_presented_as_a_reduction():
    """The paper's result is that the classic figure was too high. The
    interesting number is the size of the old error, not the count."""
    f = P.firefly_photons_per_flash()
    assert f["photons_low"] == 1e8
    assert f["photons_high"] == 1e11
    assert f["old_estimate_high"] == 1e14
    assert "REDUCTION" in f["correction"]


def test_the_correction_is_two_to_six_orders_of_magnitude():
    assert P.FIREFLY_PHOTONS["correction_orders_of_magnitude_low"] == 2
    assert P.FIREFLY_PHOTONS["correction_orders_of_magnitude_high"] == 6
    assert P.FIREFLY_PHOTONS["direction"] == "DOWNWARD"


def test_the_firefly_figure_keeps_its_range_and_limitation():
    f = P.firefly_photons_per_flash()
    assert f["range_decades"] == 3
    assert "substrate turnover" in f["limitation"]


def test_the_old_estimate_is_attributed_and_superseded():
    assert any("Coblentz" in s for s in P.FIREFLY.supersedes)


# --- the tetrahedron paper closes the Q19 caveat ----------------------

def test_the_tetrahedron_prior_art_is_confirmed():
    t = P.confirm_tetrahedron_prior_art()
    assert t["verified"]
    assert t["doi"] == "10.1007/s10231-017-0688-6"
    assert t["novelty"] == "NONE"


def test_confirming_the_citation_does_not_change_the_mathematics():
    t = P.confirm_tetrahedron_prior_art()
    assert "independently derived" in t["relationship"]
    assert "without changing the mathematics" in t["relationship"]


def test_the_paper_does_not_cover_the_hard_regimes():
    """The paper's uniform-interior guarantee is not evidence about the
    non-uniform, shell, or moving cases r10.inverse measured as failing.
    """
    t = P.confirm_tetrahedron_prior_art()
    assert "non-uniform density" in t["what_the_paper_does_not_cover"]
    assert "not evidence about any hidden\nobject" in \
        t["what_the_paper_does_not_cover"] or \
        "not evidence about any hidden object" in \
        t["what_the_paper_does_not_cover"]


def test_inverse_module_now_agrees_that_prior_art_is_verified():
    """The two modules must not disagree about the citation."""
    from r10 import inverse as I
    r = I.inverse_report(seed=7)
    assert r["prior_art"]["verified"] is True
    assert r["prior_art"]["doi"] == P.TETRAHEDRON.doi


# --- claim discipline --------------------------------------------------

def test_a_citation_does_not_authenticate_a_source_claim():
    with pytest.raises(P.PriorArtError) as e:
        P.refuse_lore_promotion("silver_2026_firefly")
    msg = str(e.value)
    assert "does not corroborate" in msg
    assert "shares its vocabulary" in msg


def test_report_claims_no_measurement():
    r = P.prior_art_report()
    assert r["measured_here"] == "nothing"
    assert r["evidence_class"] == "CONVENTIONAL_LITERATURE"
    assert len(r["references"]) == 2


def test_report_notes_both_papers_reduce_a_dramatic_figure():
    r = P.prior_art_report()
    assert "smaller" in r["both_papers_do_the_same_thing"]
