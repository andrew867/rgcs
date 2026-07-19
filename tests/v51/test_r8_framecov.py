"""R8-D-002 / R8-D-005 — covariance-aware frame chain."""

from __future__ import annotations

import pytest

from r6.mailbox import FRAME_CHAIN, FrameGraph, FrameTransform


def _chain(n_links: int | None = None, sigma: float = 2.0) -> FrameGraph:
    g = FrameGraph(root="SOLAR_SYSTEM_BARYCENTER_DYNAMICAL_ROOT")
    pairs = list(zip(FRAME_CHAIN, FRAME_CHAIN[1:]))
    for a, b in pairs[:n_links] if n_links else pairs:
        g.add(FrameTransform(a, b, 0.0, "TT", "DE440", (0.0, 0.0, 0.0),
                             (1.0, 0.0, 0.0, 0.0), sigma))
    return g


# --- the documented reference case ------------------------------------

def test_nine_link_two_metre_case():
    """The case recorded in the correction register: 9 links at 2 m."""
    g = _chain()
    assert len(g.transforms) == 9
    assert g.total_uncertainty_m(0.0) == pytest.approx(6.0)
    assert g.total_uncertainty_m(1.0) == pytest.approx(18.0)
    assert g.worst_case_uncertainty_m() == pytest.approx(18.0)


def test_quadrature_understates_a_correlated_chain_threefold():
    g = _chain()
    assert (g.worst_case_uncertainty_m()
            / g.total_uncertainty_m(0.0)) == pytest.approx(3.0)


# --- correlation regimes ----------------------------------------------

def test_independent_is_quadrature():
    g = _chain()
    quad = sum(t.position_uncertainty_m ** 2
               for t in g.transforms) ** 0.5
    assert g.total_uncertainty_m(0.0) == pytest.approx(quad)


def test_fully_correlated_is_linear():
    g = _chain()
    lin = sum(t.position_uncertainty_m for t in g.transforms)
    assert g.total_uncertainty_m(1.0) == pytest.approx(lin)


def test_mixed_correlation_lies_between():
    g = _chain()
    lo, mid, hi = (g.total_uncertainty_m(r) for r in (0.0, 0.5, 1.0))
    assert lo < mid < hi


def test_uncertainty_is_monotonic_in_correlation():
    g = _chain()
    vals = [g.total_uncertainty_m(r)
            for r in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    assert all(a < b for a, b in zip(vals, vals[1:]))


# --- the PSD refusal (R8-D-005) ---------------------------------------

def test_non_psd_correlation_is_refused_not_clamped():
    """The dangerous bug: rho below -1/(n-1) previously returned 0.0 m,
    reporting PERFECT knowledge for an impossible input."""
    g = _chain()                      # 9 links -> bound is -0.125
    with pytest.raises(ValueError) as e:
        g.total_uncertainty_m(-0.5)
    assert "positive semidefinite" in str(e.value)


def test_psd_boundary_is_accepted():
    g = _chain()
    assert g.total_uncertainty_m(-1.0 / 8) == pytest.approx(0.0, abs=1e-9)


def test_psd_bound_scales_with_chain_length():
    """Two links tolerate rho = -1; nine do not."""
    two = _chain(2)
    assert two.total_uncertainty_m(-1.0) == pytest.approx(0.0, abs=1e-9)
    with pytest.raises(ValueError):
        _chain(9).total_uncertainty_m(-1.0)


def test_correlation_outside_unit_interval_refused():
    g = _chain()
    for bad in (-1.5, 1.5):
        with pytest.raises(ValueError):
            g.total_uncertainty_m(bad)


# --- structural ---------------------------------------------------------

def test_longer_chain_is_never_more_certain():
    short, long = _chain(3), _chain(9)
    assert long.total_uncertainty_m(0.0) >= short.total_uncertainty_m(0.0)


def test_empty_chain_is_zero():
    g = FrameGraph(root="SUN_CENTER_VISUAL_ROOT")
    assert g.total_uncertainty_m(0.0) == 0.0


def test_shared_ephemeris_motivates_positive_correlation():
    """Every link here declares DE440; that shared dependence is
    exactly why quadrature is the wrong default."""
    g = _chain()
    assert len({t.ephemeris_id for t in g.transforms}) == 1
    assert g.total_uncertainty_m(0.5) > g.total_uncertainty_m(0.0)


def test_units_are_metres_throughout():
    g = _chain(sigma=1000.0)
    assert g.total_uncertainty_m(0.0) == pytest.approx(3000.0)
