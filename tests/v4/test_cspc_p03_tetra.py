"""P03 (A08-A11): 64-tetrahedron ambiguity, constructions, spectra,
matched nulls.

The acceptance matrix requires: the source ambiguity stays explicit,
at least three non-isomorphic families exist, spectra are relabeling
invariant, every special feature is compared with matched nulls, and no
arbitrary labeling creates a preferred 4096 relationship.
"""
from __future__ import annotations

import numpy as np


# --- A08 ambiguity ------------------------------------------------------

def test_source_phrase_stays_underdetermined():
    from cspc.tetra import ambiguity_report
    rep = ambiguity_report()
    assert rep["status"] == "UNDERDETERMINED"
    assert rep["n_readings"] >= 4
    assert "NOT RESOLVED" in rep["resolution"]


def test_cells_reading_is_not_silently_replaced_by_nodes():
    """The matrix forbids swapping 64 tetrahedra for 64 nodes because
    graphs are easier."""
    from cspc.tetra import READINGS, ambiguity_report
    counts = {r.what_64_counts for r in READINGS}
    assert "tetrahedral cells" in counts and "vertices" in counts
    assert "refused" in ambiguity_report()["refusal"].lower()


# --- A09 constructions --------------------------------------------------

def test_at_least_three_non_isomorphic_families():
    from cspc.tetra import build_all, laplacian_spectrum
    built = build_all()
    assert len(built) >= 3
    specs = {k: laplacian_spectrum(cx).tobytes()
             for k, cx in built.items()}
    assert len(set(specs.values())) == len(specs), \
        "families must not be relabelings of one another"


def test_cell_readings_really_have_64_tetrahedra():
    from cspc.tetra import build_all
    built = build_all()
    assert built["TETRA-SUBDIV"].n_cells == 64
    assert built["FULLER-VE-64"].n_cells == 64
    for c in built["TETRA-SUBDIV"].cells:
        assert len(c) == 4 and len(set(c)) == 4


def test_node_readings_have_64_vertices():
    from cspc.tetra import build_all
    built = build_all()
    assert built["CUBIC-4x4x4"].n_vertices == 64
    assert built["HYPERCUBE-Q6"].n_vertices == 64


def test_all_families_are_connected():
    from cspc.tetra import build_all, sync_summary
    for cx in build_all().values():
        assert sync_summary(cx)["connected"]


# --- A10 spectra --------------------------------------------------------

def test_spectra_are_invariant_under_relabeling():
    from cspc.tetra import build_all, laplacian_spectrum, relabel
    for cx in build_all().values():
        for seed in (1, 2, 7):
            assert np.allclose(laplacian_spectrum(cx),
                               laplacian_spectrum(relabel(cx, seed)))


def test_hypercube_fiedler_is_the_known_value():
    """Q6's algebraic connectivity is exactly 2 — an external check
    that the spectral code is correct, not self-consistent."""
    from cspc.tetra import algebraic_connectivity, hypercube_q6
    assert abs(algebraic_connectivity(hypercube_q6()) - 2.0) < 1e-9


def test_sync_summary_carries_the_lattice_firewall():
    from cspc.tetra import build_all, sync_summary
    s = sync_summary(build_all()["CUBIC-4x4x4"])
    assert "not a physical lattice" in s["claim"]


# --- A11 matched nulls --------------------------------------------------

def test_null_preserves_size_and_degree_sequence():
    from cspc.tetra import build_all, matched_null
    cx = build_all()["CUBIC-4x4x4"]
    null = matched_null(cx, seed=3)
    assert null.n_vertices == cx.n_vertices
    assert null.n_edges == cx.n_edges
    assert null.degrees() == cx.degrees()


def test_features_are_reported_against_matched_nulls_two_sided():
    """Regression: a one-sided test reported p=1.0 for every lattice
    and hid that they are unusually POORLY connected."""
    from cspc.tetra import build_all, compare_to_nulls
    for cx in build_all().values():
        r = compare_to_nulls(cx, n_null=25)
        assert "p_value_two_sided" in r
        assert 0.0 < r["p_value_two_sided"] <= 1.0
        assert r["direction"] in (
            "less connected than matched random",
            "more connected than matched random")
        assert "not physical" in r["claim"]


def test_null_comparison_is_deterministic():
    from cspc.tetra import build_all, compare_to_nulls
    cx = build_all()["TETRA-SUBDIV"]
    a = compare_to_nulls(cx, n_null=20, seed=11)
    b = compare_to_nulls(cx, n_null=20, seed=11)
    assert a["p_value_two_sided"] == b["p_value_two_sided"]


# --- the 4096 question --------------------------------------------------

def test_4096_is_just_64_squared_and_not_special():
    """No labeling creates a preferred 4096 relationship: every
    64-element structure has 4096 ordered pairs, structured or not."""
    from cspc.tetra import pair_count_is_not_special
    rep = pair_count_is_not_special()
    assert rep["ordered_pairs"] == 4096
    assert rep["unstructured_set_of_64_also_gives_4096"] is True
    for fam, v in rep["per_family"].items():
        assert v["equals_4096"] is True, fam
    assert "arithmetic" in rep["conclusion"]
    assert rep["evidence_class"] == "DERIVED_ARITHMETIC"
