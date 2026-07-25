"""P10 -- ITRS/ITRF, epoch, plate motion: focused, negative, round-trip."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from cwatlas import frames as F

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "cwatlas" / "schemas" / "frame_epoch.schema.json"
)


def test_realizations_are_named_and_preserved():
    assert set(F.ITRF_REALIZATIONS) >= {"ITRF2008", "ITRF2014", "ITRF2020"}
    assert F.get_realization("ITRF2020").reference_epoch == 2015.0


def test_unknown_realization_fails_safe():
    with pytest.raises(F.FrameError):
        F.get_realization("ITRF1066")


def test_epoch_is_mandatory_on_a_point():
    with pytest.raises(TypeError):
        F.EpochStampedPoint(1.0, 2.0, 3.0, "ITRF2020")  # missing epoch


def test_a_point_at_t1_differs_from_t2_by_the_modelled_drift():
    # ~2.5 cm/yr eastward synthetic velocity.
    model = F.PlateMotionModel("SYNTH-PLATE", (0.025, -0.010, 0.005))
    p1 = F.EpochStampedPoint(6378137.0, 0.0, 0.0, "ITRF2020", epoch=2020.0)
    p2 = F.propagate(p1, model, to_epoch=2030.0)
    drift = p2.as_array() - p1.as_array()
    assert np.allclose(drift, np.array([0.025, -0.010, 0.005]) * 10.0)
    assert p2.epoch == 2030.0
    # A non-timeless coordinate: t1 and t2 are genuinely different.
    assert not np.allclose(p1.as_array(), p2.as_array())


def test_zero_velocity_leaves_a_coordinate_unchanged():
    model = F.PlateMotionModel("STABLE", (0.0, 0.0, 0.0))
    p1 = F.EpochStampedPoint(1000.0, 2000.0, 3000.0, "ITRF2014", epoch=2010.0)
    p2 = F.propagate(p1, model, to_epoch=2099.0)
    assert np.allclose(p1.as_array(), p2.as_array())


def test_propagation_is_reversible_round_trip():
    model = F.PlateMotionModel("SYNTH-PLATE", (0.03, 0.02, -0.01))
    p1 = F.EpochStampedPoint(4000000.0, 3000000.0, 3000000.0,
                             "ITRF2008", epoch=2005.0)
    forward = F.propagate(p1, model, to_epoch=2025.0)
    back = F.propagate(forward, model, to_epoch=2005.0)
    assert np.allclose(back.as_array(), p1.as_array(), atol=1e-9)


def test_bad_velocity_is_rejected():
    with pytest.raises(F.FrameError):
        F.PlateMotionModel("BAD", (0.1, 0.2))  # not 3 components
    with pytest.raises(F.FrameError):
        F.PlateMotionModel("BAD", (0.1, float("nan"), 0.3))


def test_certificate_conforms_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    cert = F.make_certificate(
        "ITRF2020", 2020.0, orientation_profile_id="IDENTITY@1.0.0",
        ephemeris_id=None)
    d = cert.to_dict()
    jsonschema.validate(instance=d, schema=schema)
    assert d["hash"].startswith("sha256:")
    assert d["time_scale"] == F.TIME_SCALE


def test_certificate_hash_is_deterministic_and_identity_sensitive():
    a = F.make_certificate("ITRF2020", 2020.0, "IDENTITY@1.0.0")
    b = F.make_certificate("ITRF2020", 2020.0, "IDENTITY@1.0.0")
    c = F.make_certificate("ITRF2014", 2020.0, "IDENTITY@1.0.0")
    assert a.hash == b.hash
    assert a.hash != c.hash


def test_certificate_rejects_unknown_frame_and_missing_profile():
    with pytest.raises(F.FrameError):
        F.make_certificate("ITRF1900", 2020.0, "IDENTITY@1.0.0")
    with pytest.raises(F.FrameError):
        F.make_certificate("ITRF2020", 2020.0, "")


def test_report_claims_nothing_physical():
    r = F.frames_report()
    assert r["claim_class"] == "MATHEMATICAL_TRANSLATION"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
