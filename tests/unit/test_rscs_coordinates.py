"""Unit tests for the 14 RSCS-C.* typed coordinates (construction,
validation, NaN/inf rejection, shape/frame errors, serialization)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs_core.coordinates import (SpatialCoordinate, OrientationFrame,
                                   TimeCoordinate, PhaseCoordinate,
                                   AngularFrequency, Wavevector, ModeIndex,
                                   ModalState, PolarizationState,
                                   SelectionCoordinate, GroupDelay,
                                   Uncertainty, ProvenanceTag, MemoryLattice,
                                   COORDINATE_TYPES)


def test_spatial_coordinate():
    p = SpatialCoordinate((1.0, 2.0, 3.0))
    assert p.registry_id == "RSCS-C.1"
    assert np.allclose(p.vector, [1, 2, 3])
    assert p.to_dict()["frame"] == "crystal_axis"


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_spatial_rejects_nonfinite(bad):
    with pytest.raises(ValueError):
        SpatialCoordinate((1.0, bad, 3.0))


def test_spatial_wrong_shape():
    with pytest.raises(ValueError):
        SpatialCoordinate((1.0, 2.0))


def test_time_coordinate():
    assert TimeCoordinate(1.5).t_s == 1.5
    with pytest.raises(ValueError):
        TimeCoordinate(float("inf"))


def test_phase_wraps():
    assert math.isclose(PhaseCoordinate(0.0).phi_rad, 0.0)
    assert math.isclose(PhaseCoordinate(2 * math.pi + 0.5).phi_rad, 0.5,
                        abs_tol=1e-12)
    assert 0.0 <= PhaseCoordinate(-1.0).phi_rad < 2 * math.pi


def test_frequency_hz_roundtrip():
    a = AngularFrequency.from_hz(4096.0)
    assert math.isclose(a.f_hz, 4096.0, rel_tol=1e-12)


def test_wavevector():
    k = Wavevector((3.0, 4.0, 0.0))
    assert math.isclose(k.magnitude_rad_mm, 5.0)


def test_mode_index():
    m = ModeIndex((1, 2), ("axial", "compact"))
    assert m.indices == (1, 2)
    with pytest.raises(ValueError):
        ModeIndex((1, 2), ("only_one",))


def test_modal_state_occupancy():
    s = ModalState.from_components([1 + 0j, 0 + 1j])
    assert math.isclose(s.total_occupancy, 2.0)
    assert s.n_modes == 2
    assert np.allclose(s.amplitude, [1.0, 1.0])


def test_modal_state_rejects_nonfinite():
    with pytest.raises(ValueError):
        ModalState(np.array([1 + 0j, complex(float("nan"), 0)]))


def test_orientation_frame():
    f = OrientationFrame.identity()
    assert f.registry_id == "RSCS-C.8"
    inv = f.compose(f).inverse()
    assert np.allclose(inv.rotation, np.eye(3))


def test_orientation_rejects_non_orthogonal():
    with pytest.raises(ValueError):
        OrientationFrame(np.array([[1.0, 2.0, 0], [0, 1, 0], [0, 0, 1]]))


def test_polarization():
    assert PolarizationState.sigma_plus().helicity == 1.0
    assert PolarizationState.sigma_minus().helicity == -1.0
    # normalization
    p = PolarizationState((0.0, 0.0, 5.0))
    assert math.isclose(p.helicity, 1.0)


def test_selection():
    s = SelectionCoordinate(2.5, 0.8, "m/s")
    assert s.population == 0.8
    with pytest.raises(ValueError):
        SelectionCoordinate(0.0, 1.5)  # population out of range


def test_group_delay():
    g = GroupDelay([1e-9, 3e-9, 2e-9])
    assert math.isclose(g.imbalance_s, 2e-9)


def test_uncertainty_wraps_v2():
    u = Uncertainty(6310.0, 0.05)
    assert math.isclose(u.sigma, 6310.0 * 0.05)
    # delegates range validation to frozen v2 UncertainValue
    with pytest.raises(ValueError):
        Uncertainty(1.0, 1.5)


def test_provenance_tag():
    t = ProvenanceTag("EP-03-01", "DER").extend_path("write")
    assert t.path == ("write",)
    with pytest.raises(ValueError):
        ProvenanceTag("x", "BOGUS")


def test_memory_lattice_requires_ack():
    with pytest.raises(ValueError):
        MemoryLattice((0, 1), [0.1, 0.2])  # no acknowledge_hypothesis
    m = MemoryLattice((0, 1), [0.1, 0.2], acknowledge_hypothesis=True)
    assert m.claim_class == "HYP"


def test_all_coordinate_ids_present():
    # C.1-14 (Agent 03) + C.16/C.17 (Agent 06); C.15 lives in
    # rscs_core.memory (import-cycle avoidance, see coordinates/__init__)
    expected = {f"RSCS-C.{i}" for i in range(1, 15)} | {"RSCS-C.16",
                                                        "RSCS-C.17"}
    assert set(COORDINATE_TYPES) == expected
    for cid, cls in COORDINATE_TYPES.items():
        assert cls.registry_id == cid
