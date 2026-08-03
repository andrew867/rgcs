"""R10.73 bench-drive spec -- the seven mandated test groups."""

from __future__ import annotations

import cmath
import math

import pytest

from rgcs_phyrll_v07 import bench_drive as BD
from rgcs_phyrll_v07 import composed_sweep as CS
from rgcs_phyrll_v07.steering_optimizer import weighted_d_eff


# 1. no force/thrust namespace
def test_no_force_or_thrust_name_exists():
    for name in dir(BD):
        if not name.startswith("_"):
            assert "force" not in name.lower()
            assert "thrust" not in name.lower()


# 2. no wall-power path
def test_no_wall_power_path():
    import inspect
    src = inspect.getsource(BD)
    assert "wall" not in src.lower().replace("no wall power", "")
    assert "ring_power_from_wall" not in src


# 3. active floor enforced
def test_drive_table_honours_the_floor():
    rows = BD.drive_table()
    assert len(rows) == 37
    blanked = [r for r in rows if r["active_floor_status"] == "BLANKED"]
    ok = [r for r in rows if r["active_floor_status"] == "OK"]
    assert len(blanked) == 4 and len(ok) == 33
    assert not any(r["active_floor_status"] == "FLOOR_VIOLATION"
                   for r in rows)
    assert min(r["amplitude_weight"] for r in ok) >= \
        CS.ACTIVE_AMPLITUDE_FLOOR


# 4. axes reduce to R10.72 baselines
def test_drive_weights_are_the_r1072_constrained_optimum():
    assert BD.MOD == 0.5 and BD.LAG_RAD == math.pi
    a = BD.drive_weights()
    b = CS.composed_weights(0.5, math.pi)
    assert all(abs(x - y) < 1e-12 for x, y in zip(a, b))
    assert abs(weighted_d_eff(a)) == pytest.approx(0.4124, abs=2e-3)


def test_predicted_d_eff_matches_the_recipe():
    d = BD.predicted_d_eff()
    assert d["magnitude"] == pytest.approx(0.4124, abs=2e-3)
    assert d["offset_from_blank_axis_deg"] == pytest.approx(12.5, abs=1.0)


# 5. nulls preserve equal resource
def test_randomized_nulls_hold_the_same_amplitude_multiset():
    nm = BD.null_masks(n_random=6)
    assert all(r["equal_resource"] for r in nm["equal_resource_randomized"])


def test_declared_null_tables_are_complete():
    nm = BD.null_masks()
    for key in ("all_active_symmetric", "binary_blanking_best",
                "reversed_phase_lag", "rotated_mask_k7", "mirrored_mask"):
        assert len(nm["weight_tables"][key]) == 37
    names = {c["name"] for c in nm["bench_conditions"]}
    assert {"dummy_resistive_load", "no_crystal",
            "dummy_crystal"} <= names


# 6. d_eff transforms under rotation and mirror
def test_rotation_rotates_d_eff_by_the_cell_pitch():
    w = BD.drive_weights()
    d0 = weighted_d_eff(w)
    d7 = weighted_d_eff(w[-7:] + w[:-7])
    shift = math.degrees(cmath.phase(d7 / d0)) % 360.0
    assert shift == pytest.approx(math.degrees(2 * math.pi * 7 / 37),
                                  abs=1e-6)
    assert abs(d7) == pytest.approx(abs(d0), abs=1e-12)


def test_mirror_conjugates_d_eff():
    w = BD.drive_weights()
    m = [w[(-k) % 37].conjugate() for k in range(37)]
    dm = weighted_d_eff(m)
    d0 = weighted_d_eff(w)
    assert dm == pytest.approx(d0.conjugate(), abs=1e-12)


def test_reversed_lag_negates_the_steer_angle():
    """The correct transform, found by this test failing against a wrong
    conjugation claim: reversing the lag mirrors the steer about the
    amplitude-only axis EXACTLY (equal magnitude, negated offset). The
    naive claim d(-lag) == conj(d(+lag)) is FALSE -- conjugating the
    weights does not conjugate the basis phases."""
    d_amp = weighted_d_eff(CS.composed_weights(0.5, 0.0))
    d_fwd = weighted_d_eff(CS.composed_weights(0.5, math.pi))
    d_rev = weighted_d_eff(CS.composed_weights(0.5, -math.pi))
    axis = cmath.phase(d_amp)
    steer_f = math.degrees((cmath.phase(d_fwd) - axis + math.pi)
                           % (2 * math.pi) - math.pi)
    steer_r = math.degrees((cmath.phase(d_rev) - axis + math.pi)
                           % (2 * math.pi) - math.pi)
    assert steer_r == pytest.approx(-steer_f, abs=1e-9)
    assert abs(d_rev) == pytest.approx(abs(d_fwd), abs=1e-12)
    assert d_rev != pytest.approx(d_fwd.conjugate())   # the wrong claim


# 7. report refuses PASS without uncertainty or controls
def test_verdict_refused_without_uncertainty():
    with pytest.raises(BD.BenchVerdictRefused, match="uncertainty"):
        BD.evaluate_bench_result(10.0, 1.0, None, 0.5,
                                 {c: True for c in
                                  BD.REQUIRED_CONTROL_RESULTS})


def test_verdict_refused_with_missing_controls():
    with pytest.raises(BD.BenchVerdictRefused, match="missing control"):
        BD.evaluate_bench_result(10.0, 1.0, 5.0, 0.5,
                                 {"all_active_symmetric": True})


def test_verdict_pass_and_fail_both_reachable_with_full_inputs():
    controls = {c: {"receipt": "r"} for c in BD.REQUIRED_CONTROL_RESULTS}
    cmd = BD.predicted_d_eff()["angle_deg"]
    ok = BD.evaluate_bench_result(cmd + 2.0, 1.0, 5.0, 0.5, controls)
    assert ok["verdict"] == "PASS"
    bad = BD.evaluate_bench_result(cmd + 40.0, 1.0, 5.0, 0.5, controls)
    assert bad["verdict"] == "FAIL"


def test_probe_plan_covers_ring_compass_and_planes():
    p = BD.probe_plan()
    kinds = {}
    for pr in p["probes"]:
        kinds[pr["kind"]] = kinds.get(pr["kind"], 0) + 1
    assert kinds["perimeter"] == 37 and kinds["compass"] == 8
    assert kinds["above_plane"] == 4 and kinds["below_plane"] == 4
    assert p["lock_in_reference_hz"] == 1683456
    assert p["min_direct_sample_rate_hz"] >= 2 * 1683456
