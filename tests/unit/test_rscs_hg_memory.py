"""Unit tests for the Hydrogenuine (HG) memory bridge (RSCS-C.15,
RSCS-O.14/15/16). Engineering data structure; NHT/HAL interpretation excluded.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs_core.coordinates import (SpatialCoordinate, OrientationFrame,
                                   TimeCoordinate, PhaseCoordinate, ModalState,
                                   Uncertainty, ProvenanceTag)
from rscs_core.memory import (HydrogenuineRecord, hg_store, hg_replay,
                              hg_update)
from rscs_core.registry import classification_of


def _rot_z(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0],
                     [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def _consistent_record(deg=90.0):
    frame = OrientationFrame(_rot_z(deg), 1, "world")
    ego = SpatialCoordinate((1.0, 0.0, 0.0), "ego")
    allo_vec = frame.rotation @ ego.vector
    allo = SpatialCoordinate(tuple(float(v) for v in allo_vec), "world")
    return frame, ego, allo


def test_record_construction():
    frame, ego, allo = _consistent_record()
    rec = HydrogenuineRecord(
        allocentric=allo, egocentric=ego, frame=frame,
        event_time=TimeCoordinate(1.0),
        predicted=ModalState.from_components([1 + 0j]))
    assert rec.registry_id == "RSCS-C.15"
    assert not rec.is_observed
    d = rec.to_dict()
    assert d["rscs_id"] == "RSCS-C.15" and d["observed"] is None


def test_record_is_eng_not_evidence():
    # the record's store operator is ENG, never EST/DER
    assert classification_of(hg_store).label == "ENG"
    assert classification_of(hg_replay).label == "ENG"
    assert classification_of(hg_update).label == "ENG"


def test_frame_consistency():
    frame, ego, allo = _consistent_record(45.0)
    rec = HydrogenuineRecord(
        allocentric=allo, egocentric=ego, frame=frame,
        event_time=TimeCoordinate(0.0),
        predicted=ModalState.from_components([1 + 0j]))
    assert rec.frame_consistent()


def test_store_requires_frame_consistency():
    frame, ego, _ = _consistent_record()
    bad_allo = SpatialCoordinate((9.0, 9.0, 9.0), "world")
    with pytest.raises(ValueError):
        hg_store(bad_allo, ego, frame, TimeCoordinate(0.0),
                 ModalState.from_components([1 + 0j]))
    # explicit opt-out stores an unreconciled record
    rec = hg_store(bad_allo, ego, frame, TimeCoordinate(0.0),
                   ModalState.from_components([1 + 0j]),
                   require_consistent=False)
    assert not rec.frame_consistent()


def test_update_records_observation():
    frame, ego, allo = _consistent_record()
    rec = hg_store(allo, ego, frame, TimeCoordinate(0.0),
                   ModalState.from_components([1 + 0j]),
                   uncertainty=Uncertainty(2.0, 0.1))
    obs = ModalState.from_components([0.8 + 0j])
    up = hg_update(rec, obs, Uncertainty(1.0, 0.05))
    assert up.is_observed
    assert np.allclose(up.observed.amplitudes, [0.8 + 0j])
    assert up.uncertainty.sigma < rec.uncertainty.sigma  # calibration shrank
    assert up.provenance.path[-1] == "update"


def test_store_carries_provenance_and_phase():
    frame, ego, allo = _consistent_record()
    prov = ProvenanceTag("SRC-3-07", "HYP", ("nht",))
    rec = hg_store(allo, ego, frame, TimeCoordinate(0.0),
                   ModalState.from_components([1 + 0j]),
                   phase=PhaseCoordinate(1.23), provenance=prov)
    assert rec.phase.phi_rad == pytest.approx(1.23)
    assert rec.provenance.source_id == "SRC-3-07"


def test_type_errors():
    frame, ego, allo = _consistent_record()
    with pytest.raises(TypeError):
        HydrogenuineRecord(allocentric=(1, 2, 3), egocentric=ego, frame=frame,
                           event_time=TimeCoordinate(0.0),
                           predicted=ModalState.from_components([1 + 0j]))
