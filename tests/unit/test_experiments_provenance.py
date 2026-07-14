"""Unit tests: rgcs_core.experiments, rgcs_core.provenance,
rgcs_core.uncertainty — schemas, control subtraction, merit score,
classification metadata, forbidden vocabulary, JSON null policy."""

from __future__ import annotations

import importlib
import inspect
import json
import math
import os
import pkgutil

import numpy as np
import pytest

import rgcs_core
from rgcs_core.uncertainty import UncertainValue, default_wave_speed
from rgcs_core.provenance import (Classification, contains_forbidden_vocabulary,
                                  to_jsonable, json_dumps, sha256_file,
                                  sha256_of_jsonable, MODEL_VERSION)
from rgcs_core.experiments import (SensorChannel, ApparatusRecord, RunRecord,
                                   control_subtracted_metrics, merit_score,
                                   current_to_electron_rate,
                                   run_record_to_json)


# ---------------------------------------------------------------- schemas

def test_apparatus_record_schema():
    app = ApparatusRecord(
        campaign_id="C1", specimen_id="S1", crystal_length_mm=154.05,
        drive_branch="coil", shared_reference=True,
        reference_description="10 MHz shared clock",
        sensors=(SensorChannel(name="p1", position_mm=35.0, axis="x"),),
        known_artifacts=("mains hum 50 Hz",))
    d = to_jsonable(app)
    assert d["drive_branch"] == "coil"
    assert d["sensors"][0]["name"] == "p1"


def test_run_record_null_labels():
    base = dict(run_id="r1", condition="configuration",
                drive_off_time_s=1.0, acquisition_end_s=3.0)
    r = RunRecord(**base, negative_result=True, coherence_tested=False)
    assert r.null_label() == "amplitude-null, coherence-untested"   # D-20
    r2 = RunRecord(**base, negative_result=True, coherence_tested=True)
    assert r2.null_label() == "null (amplitude and coherence tested)"
    assert r.post_drive_coverage_ok() is True                        # KOS-12
    r3 = RunRecord(**base | {"acquisition_end_s": 2.0},
                   negative_result=False)
    assert r3.post_drive_coverage_ok() is False


def test_control_subtracted_metrics():
    out = control_subtracted_metrics([2.0, 2.1, 1.9, 2.0],
                                     [1.0, 1.05, 0.95, 1.0])
    assert out["control_subtracted_gain"] == pytest.approx(1.0, abs=0.05)
    assert out["effect_size_d"] > 5
    null = control_subtracted_metrics([1.0, 1.1, 0.9], [1.0, 1.05, 0.95])
    assert null["control_subtracted_gain"] == pytest.approx(0.0, abs=0.1)


def test_merit_score_bounds_and_note():
    r = merit_score(1.0, 1000.0, 1000.0, 1000.0, 1000.0)
    assert r["merit_score"] == pytest.approx(1.0)
    assert "not evidence" in r["note"]
    # Half-cycle phase residue kills the phase factor.
    r2 = merit_score(1.0, 1000.0, 1000.0, 1000.0, 1000.0,
                     phase_residue_cycles=0.5)
    assert r2["phase_factor"] == pytest.approx(0.0, abs=1e-12)


def test_electron_rate_golden():
    assert current_to_electron_rate(1e-14) == pytest.approx(62415.09,
                                                            abs=0.01)


# ------------------------------------------------------- uncertain values

def test_uncertain_value_basics():
    v = default_wave_speed()
    assert v.mean == 6310.0 and v.u_rel == 0.05
    assert v.sigma == pytest.approx(315.5)
    lo, hi = v.interval()
    assert (lo, hi) == pytest.approx((5994.5, 6625.5))
    s = v.scale(2.0)
    assert s.mean == 12620.0 and s.u_rel == 0.05
    r = v.reciprocal_scale(6310.0)
    assert r.mean == pytest.approx(1.0) and r.u_rel == 0.05
    with pytest.raises(ValueError):
        UncertainValue(float("nan"), 0.0)
    with pytest.raises(ValueError):
        UncertainValue(1.0, -0.1)


# ------------------------------------------------- provenance and policy

def test_json_null_never_nan():
    payload = {"a": float("nan"), "b": float("inf"), "c": 1.0,
               "d": np.float64("nan"), "e": None}
    text = json_dumps(payload)
    parsed = json.loads(text)
    assert parsed["a"] is None and parsed["b"] is None
    assert parsed["d"] is None and parsed["c"] == 1.0
    assert "NaN" not in text and "Infinity" not in text


def test_node_positions_serializes_null_measured():
    from rgcs_core.geometry import node_positions
    out = node_positions(154.052734, 17.415434, 14.812763)
    parsed = json.loads(json_dumps(out))
    assert parsed["measured_node_mm"] is None


def test_run_record_json_roundtrip():
    r = RunRecord(run_id="r9", condition="control",
                  control_kind="dummy_load", negative_result=True)
    parsed = json.loads(json_dumps(run_record_to_json(r)))
    assert parsed["amplitude_summary"] is None
    assert parsed["null_label"] == "amplitude-null, coherence-untested"


def test_sha256_helpers(tmp_path):
    p = tmp_path / "x.bin"
    p.write_bytes(b"rgcs")
    assert len(sha256_file(str(p))) == 64
    h1 = sha256_of_jsonable({"a": 1, "b": [2, 3]})
    h2 = sha256_of_jsonable({"b": [2, 3], "a": 1})
    assert h1 == h2      # canonical (sorted) form


def test_no_hybrid_classification_labels():
    with pytest.raises(ValueError):
        Classification("semi-established")
    with pytest.raises(ValueError):
        Classification("effectively confirmed")


def _iter_public_functions():
    """All public functions defined inside rgcs_core modules."""
    pkg_dir = os.path.dirname(rgcs_core.__file__)
    for mod_info in pkgutil.walk_packages([pkg_dir], prefix="rgcs_core."):
        mod = importlib.import_module(mod_info.name)
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("_"):
                continue
            if not fn.__module__.startswith("rgcs_core"):
                continue
            yield mod_info.name, name, fn


def test_classification_metadata_on_every_public_function():
    """Policy section 4.1: every claim-bearing public function carries
    machine-readable classification metadata."""
    exempt = {
        # pure serialization / metadata plumbing, not claim-bearing
        "rgcs_core.provenance", "rgcs_core.uncertainty",
    }
    missing = []
    for mod_name, name, fn in _iter_public_functions():
        if fn.__module__ in exempt or mod_name in exempt:
            continue
        if name in {"run_record_to_json"}:      # serialization helper
            continue
        if not hasattr(fn, "classification"):
            missing.append(f"{fn.__module__}.{name}")
    assert not missing, f"functions missing classification metadata: {missing}"


def test_classification_labels_are_valid():
    valid = {"Established", "Derived", "Hypothesis", "Source claim"}
    for _, _, fn in _iter_public_functions():
        meta = getattr(fn, "classification", None)
        if meta is not None:
            assert meta.label in valid


def _vocab_offenders(pkg_dir: str) -> list:
    offenders = []
    for root, _dirs, files in os.walk(pkg_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            path = os.path.join(root, fname)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            found = contains_forbidden_vocabulary(text)
            if found:
                offenders.append((path, found))
    return offenders


def test_forbidden_vocabulary_absent_from_source():
    """QA vocabulary gate: forbidden physical-equivalence phrases must not
    appear anywhere in rgcs_core source (code or docstrings)."""
    offenders = _vocab_offenders(os.path.dirname(rgcs_core.__file__))
    assert not offenders, f"forbidden vocabulary found: {offenders}"


def test_forbidden_vocabulary_absent_from_desktop():
    """QA-D-11: extend the vocabulary gate to rgcs_desktop (UI strings,
    docstrings, viewer labels) — user-facing text must respect the same
    classification discipline as the core."""
    import rgcs_desktop
    offenders = _vocab_offenders(os.path.dirname(rgcs_desktop.__file__))
    assert not offenders, f"forbidden vocabulary found: {offenders}"


def test_forbidden_vocabulary_detector_works():
    assert contains_forbidden_vocabulary("a quantum " + "shear signal")
    assert contains_forbidden_vocabulary("the B" + "EC forms")
    assert not contains_forbidden_vocabulary("because coherence rises")
    assert not contains_forbidden_vocabulary("ordinary crystal physics")


def test_model_version_present():
    assert "RGCS-v2" in MODEL_VERSION
