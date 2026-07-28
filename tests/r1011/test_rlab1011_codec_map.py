"""R10.11 acceptance — unified codec search, flat-face map, firewalls."""

from __future__ import annotations

import inspect
import json
import pathlib

import pytest

np = pytest.importorskip("numpy")

from r1011 import codec_search as cs
from r1011 import flat_hedron as fh

EV = pathlib.Path(__file__).resolve().parents[2] / "docs" / "r1011" / "evidence"
PAIRS = [(165876523, 1643789253), (168930443, 1672875493),
         (165892733, 1658274383)]
SEALED = {165892323, 1687209343, 168724343, 165872943, 165829473, 167854923}


# ------------------------------------------------------------------ codec
def test_codec_families_finite_documented_zero_survivors():
    rep = cs.evaluate(PAIRS)
    assert rep["pair_count"] == 3
    assert rep["candidate_count"] == 183
    assert rep["survivor_count"] == 0
    assert rep["status"] == "TESTED_GRAMMAR_INCOMPLETE_ZERO_SURVIVORS"
    for r in rep["results"]:
        if not r["survives"]:
            assert r["rejection"] or any(
                not p.get("hit", False) for p in r["per_pair"])


def test_scatter_family_zero_even_per_pair():
    res = cs.family_e_scatter(PAIRS)
    assert not res.survives
    assert all(row["hit_count"] == 0 for row in res.per_pair)


def test_family_c_typed_digit_pattern_recorded():
    (res,) = cs.family_c(PAIRS)
    thirds = [(r["typed_compact"][2], r["typed_refined"][2])
              for r in res.per_pair]
    assert thirds == [("5", "4"), ("8", "7"), ("5", "5")]
    assert not res.survives


def test_no_location_names_in_codec_or_map_code():
    for mod in (cs, fh):
        src = inspect.getsource(mod)
        for banned in ("Stonehenge", "Toronto", "Montreal", "Montréal",
                       "Erie", "CYYT", "John", "stonehenge", "toronto",
                       "montreal", "erie", "cyyt"):
            assert banned not in src


# ------------------------------------------------------------------ map
def _model():
    m = json.loads((EV / "R10_11_NODE_LIFT_PARAMETERS.json")
                   .read_text(encoding="utf-8"))
    return (np.array(m["nodes_unit_xyz"]),
            {int(k): tuple(v) for k, v in m["faces"].items()}, m)


def test_flat_face_model_frozen_convex_and_exact():
    nodes, faces, m = _model()
    assert m["profile_id"] == "FLAT_FACE_NODE_CURVATURE_V1_CANDIDATE"
    assert m["claim_status"] == "CALIBRATED_CANDIDATE_NOT_VALIDATED"
    cv = fh.convexity_audit(nodes, faces)
    assert cv["convex"] and cv["outward_consistent_faces"] == 20
    for row in m["fit"]["anchor_rows"]:
        assert row["residual_deg"] < 1e-3
    assert m["fit"]["root_centroid_err_deg"] < 1e-4


def test_no_fold_and_edge_continuity_depth5():
    nodes, faces, _ = _model()
    oa = fh.orientation_audit(nodes, faces, 5)
    assert oa["orientation_reversals"] == 0
    assert oa["shared_edge_mismatches"] == 0


def test_inverse_lookup_roundtrip():
    nodes, faces, _ = _model()
    rng = np.random.default_rng(5)
    for _ in range(12):
        mf = int(rng.integers(0, 20))
        p = tuple(int(x) for x in rng.integers(0, 4, 11))
        pt = fh.address_point(nodes, faces, mf, p)
        assert fh.inverse_lookup(nodes, faces, pt, depth=11) == (mf, p)


def test_no_rbf_or_displacement_field_in_new_candidate():
    src = inspect.getsource(fh)
    for banned in ("RBF_STEP", "centers_ecef", "weights_ecef", "WARP_STEPS"):
        assert banned not in src.replace("no stored warp\n    steps", "")
    _, _, m = _model()
    assert "operator_steps_file" not in m


# ------------------------------------------------------------- firewalls
def test_uk_cluster_and_holdouts_not_fit_inputs():
    _, _, m = _model()
    # fit anchors: exactly three rows, faces 12/19 — the declared anchors
    assert len(m["fit"]["anchor_rows"]) == 3
    from r109.registry import fit_anchors
    assert SEALED.isdisjoint({r.raw for r in fit_anchors()})
    # census UK rows never appear as calibration inputs (module takes
    # only the three opaque anchors; no other targets exist in the fit)


def test_holdout_freeze_and_predictions():
    fz = json.loads((EV / "R10_11_HOLDOUT_FREEZE_RECEIPT.json")
                    .read_text(encoding="utf-8"))
    assert fz["parent_commit"].startswith("f34bb52")
    assert "DEMOTED" in fz["frozen"]["codec"]
    doc = json.loads((EV / "R10_11_PREREVEAL_PREDICTIONS.json")
                     .read_text(encoding="utf-8"))
    assert len(doc["receipt_sha256_of_predictions"]) == 64
    by_raw = {p["raw"]: p for p in doc["predictions"]}
    for raw in (165892323, 168724343, 165872943, 165829473):
        p = by_raw[raw]
        assert len(p["newmap"]["terminal_polygon"]) == 3
        assert 0 < p["newmap"]["uncertainty_radius_deg"] < 1.0
        assert "no location claim" in p["prediction_class"]
    assert "BLOCKED" in by_raw[1687209343]["prediction_class"]


def test_old_profile_demoted_but_exact():
    # the old structural profile still round-trips exactly (nothing
    # was broken by demotion) — semantics, not arithmetic, changed
    import rgcs_coordinate as rc
    for c, r in PAIRS:
        t = rc.decode_coordinate(c).to_dict()
        from rgcs_coordinate.codecs import federation_terra_30 as t10
        assert t10.encode(t["face_id"], t["q22_path"],
                          t["extracted_shell"]) == c
