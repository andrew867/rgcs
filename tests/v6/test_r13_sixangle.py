"""P23 — the six-angle ring: planar sampling, aliasing, and the refusal
to read planar uniformity as three-dimensional isotropy."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import sixangle as SA


def test_ring_is_six_detectors_at_sixty_degrees():
    ring = SA.AngleRing()
    assert ring.n == 6
    assert ring.spacing_deg == 60.0
    assert list(ring.angles_deg()) == [0.0, 60.0, 120.0, 180.0, 240.0, 300.0]


def test_a_ring_needs_at_least_three_detectors():
    with pytest.raises(SA.SixAngleError):
        SA.AngleRing(n=2)


def test_constant_pattern_is_highly_uniform():
    # POWER: a flat planar source reads CV ~ 0 and is called uniform.
    ring = SA.AngleRing()
    samples = ring.sample_pattern(lambda th: 1.0)
    u = SA.planar_uniformity(samples)
    assert u["coefficient_of_variation"] == pytest.approx(0.0, abs=1e-12)
    assert u["uniform"] is True


def test_dipole_pattern_is_non_uniform():
    # POWER (the other way): a cos(theta) dipole sums to zero around the
    # ring, so its coefficient of variation is unbounded -- not uniform.
    ring = SA.AngleRing()
    samples = ring.sample_pattern(lambda th: math.cos(th))
    u = SA.planar_uniformity(samples)
    assert not math.isfinite(u["coefficient_of_variation"])
    assert u["uniform"] is False


def test_order_six_harmonic_aliases_to_order_zero():
    # Six samples resolve only orders 0..3; an order-6 harmonic folds to 0.
    assert SA.resolvable_orders() == (0, 1, 2, 3)
    assert SA.aliased_order(6) == 0
    assert SA.aliased_order(12) == 0
    # and it is empirically indistinguishable from uniform on the ring:
    ring = SA.AngleRing()
    samples = ring.sample_pattern(lambda th: math.cos(6.0 * th))
    assert np.allclose(samples, samples[0])
    assert SA.planar_uniformity(samples)["uniform"] is True


def test_refuse_planar_uniformity_as_isotropy_always_raises():
    ring = SA.AngleRing()
    uniform = ring.sample_pattern(lambda th: 1.0)
    with pytest.raises(SA.SixAngleError):
        SA.refuse_planar_uniformity_as_isotropy(uniform)
    with pytest.raises(SA.SixAngleError):
        SA.refuse_planar_uniformity_as_isotropy()


def test_refuse_ring_as_measured_raises():
    ring = SA.AngleRing()
    samples = ring.sample_pattern(lambda th: 1.0 + 0.1 * math.cos(th))
    with pytest.raises(SA.SixAngleError):
        SA.refuse_ring_as_measured(samples)


def test_report_verdict_and_out_of_plane_disclaimer():
    r = SA.sixangle_report()
    assert r["verdict"] == "SIX_ANGLE_RING_PLANAR_NOT_ISOTROPIC"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "ANALYTIC_MODEL"
    disclaimer = r["what_this_does_not_say"].lower()
    assert "out-of-plane" in disclaimer
    assert "isotrop" in disclaimer
    assert r["order_6_aliases_to"] == 0
