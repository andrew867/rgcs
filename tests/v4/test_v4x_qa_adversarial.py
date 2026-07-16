"""Q01 adversarial QA against the V4X lanes.

Each test is an attack the QA agent is required to attempt: source
laundering, capability bypass, threshold reintroduction, numerology,
fabricated measurement, quarantine leakage, and stale coverage."""

import pathlib

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_no_multi_mm_proximity_threshold_reintroduced():
    """The 4 mm heuristic must not reappear anywhere in the Eye path.

    Attack: a future edit reintroduces a proximity threshold under a
    new name. Any tolerance compared against a separation must be the
    1e-6 mm numerical tolerance."""
    from rscs2_core import eye
    src = (ROOT / "rscs2_core" / "eye.py").read_text(encoding="utf-8")
    assert eye.NUMERICAL_COINCIDENCE_TOL_MM == 1e-6
    for bad in ("4.0  # mm", "PROXIMITY_THRESHOLD", "NODE_TOL_MM = 4"):
        assert bad not in src
    # a 3.94 mm separation is reported as 3.94 mm, never as a match
    out = eye.node_coincidence_comparison(
        np.array([0.0, 0.0, 0.0]), np.array([[3.94, 0.0, 0.0]]),
        candidate_halfwidth_mm=0.1, comparator_halfwidth_mm=0.1,
        mesh_resolution_mm=0.1, convergence_shift_mm=0.01,
        cloud_rms_mm=0.01)
    assert out["separation_mm"] == pytest.approx(3.94)
    assert out["classification"] != "EXACT_CONVENTIONAL_NODE_COINCIDENCE"


def test_source_cannot_be_laundered_into_derived():
    """Attack: relabel a source claim as derived physics."""
    from rscs2_core.research_records import make_record, RecordError
    from consciousness_lane import theory_registry as tr
    reg = tr.build_theory_registry()
    # SRC/HYP entries must not be sitting at a validated status
    for rid, rec in reg.items():
        if set(rec["evidence_tags"]) & {"SRC", "HYP"}:
            assert rec["status"] not in ("CORE_VALIDATED",
                                         "EXPERIMENTALLY_MEASURED")
    with pytest.raises(RecordError):
        make_record("ConsciousnessLayerRecord", "X", "myth as fact",
                    "consciousness", "REDUCED_ORDER_VALIDATED",
                    ["SRC"], layer="private_myth")


def test_future_interface_cannot_be_coerced_into_a_number():
    """Attack: call a deferred interface and use whatever falls out."""
    from rscs2_core import interfaces_future as ifu
    for iid in ifu.INTERFACES:
        rec = ifu.interface_record(iid)
        assert rec["value"] is None
        assert rec["classification"] == "INTERFACE_ONLY"
        with pytest.raises(ifu.FutureInterfaceError):
            ifu.request_computation(iid, {"anything": 1})


def test_consciousness_cannot_reach_quartz_solvers():
    """Attack: import a quartz solver from the quarantined lane."""
    import ast

    import consciousness_lane as cl
    for f in pathlib.Path(cl.__file__).parent.glob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for n in names:
                assert n not in cl.FORBIDDEN_IMPORTS, (f.name, n)


def test_ethics_gate_cannot_be_argued_around():
    """Attack: declare a human protocol safe enough to proceed."""
    from rscs2_core.research_records import safety_gate
    g = safety_gate({"campaign_kind": "operator_state",
                     "declared_limits": {"voltage_v": 0.0},
                     "engineering_risk": "none"})
    assert g["required_status"] == "ETHICS_APPROVAL_REQUIRED"
    assert not g["passed"]


def test_synthetic_daq_output_carries_no_meas_tag():
    """Attack: pass synthetic ring-down through as a measurement."""
    from rscs2_core import protocols_v4x as pv
    t, y = pv.synth_ring_down(1000.0, 500.0, 50000.0, 0.5)
    out = pv.analyze_ring_down(t, y)
    assert "MEAS" not in str(out)
    assert out["synthetic_validated"] is True


def test_frequency_near_miss_not_rounded_into_a_match():
    """Attack: 21*195 = 4095 quietly becomes 4096."""
    from rscs2_core import frequency_keys as fk
    sig = fk.coincidence_significance(4095.0, [4096.0],
                                      tolerance_hz=0.5,
                                      band_hz=(1.0, 10000.0),
                                      n_candidates_tried=100)
    assert not sig["within_tolerance"]
    # and a "hit" found after trying many candidates is not evidence
    loose = fk.coincidence_significance(4096.0, [4096.0],
                                        tolerance_hz=5.0,
                                        band_hz=(1.0, 10000.0),
                                        n_candidates_tried=5000)
    assert loose["within_tolerance"]
    assert loose["expected_chance_hits"] > 1.0
    assert not loose["significant"]


def test_coverage_ledger_is_not_stale():
    """Attack: ledger passes because IDs were dropped from parsing."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cov", ROOT / "tools" / "v4x_coverage_ledger.py")
    cov = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cov)
    rep = cov.build()
    assert rep["total_ids"] == 248
    assert rep["gate_G42_pass"]
