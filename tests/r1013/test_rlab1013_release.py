"""R10.13 release tests — Tranches A-E.

Real execution only: no mocks, no static receipts. FEM tests use
coarse meshes to stay fast but run the actual gmsh + skfem + ARPACK
pipeline.
"""

import copy
import json
import math
import pathlib

import pytest

from r1013 import SOFTWARE_EMITTABLE
from r1013.errors import ERROR_CODES, UserError, explain
from r1013.specimen import (TEMPLATE, canonical_json, density_check,
                            geometry_report, inspect, migrate,
                            readiness, specimen_hash, validate)

EX = pathlib.Path(__file__).resolve().parents[2] / "r1013" / "data" / \
    "examples"


def good_rec():
    rec = json.loads((EX / "crystal_complete.json").read_text())
    return rec


# ------------------------------------------------------- Tranche A
def test_gate_zero_mismatches_typed():
    from r1013.authority import GATE_ZERO_MISMATCHES, gate_zero_receipt
    ids = [m["id"] for m in GATE_ZERO_MISMATCHES]
    assert ids == [f"GZ-{i:02d}" for i in range(1, 6)]
    # the rgcs name collision is recorded and resolved by delegation
    gz2 = GATE_ZERO_MISMATCHES[1]
    assert "r1012.cli" in gz2["actual"] and "DELEGATES" in gz2["resolution"]
    r = gate_zero_receipt("h", "b", 1)
    assert r["schema"] == "rgcs.r1013.gate-zero.v1"


def test_corrections_extend_r1012_ledger():
    from r1012.ledger import CORRECTIONS
    from r1013.authority import CORRECTIONS_R1013
    assert len(CORRECTIONS) == 8               # COR-01..08 untouched
    ids = [c["id"] for c in CORRECTIONS_R1013]
    assert ids == [f"COR-{i:02d}" for i in range(9, 15)]
    by_id = {c["id"]: c for c in CORRECTIONS_R1013}
    assert "NO extension bit" in by_id["COR-09"]["current"]
    assert "REJECTED" in by_id["COR-11"]["current"]
    assert "REVOKED" in by_id["COR-12"]["current"]
    assert "HOLD" in by_id["COR-14"]["current"]


def test_revoked_artifacts_stay_inactive():
    from r1012.ledger import active_artifacts, revoked_artifacts
    act, rev = active_artifacts(), revoked_artifacts()
    assert not set(act) & set(rev)
    assert any("627" in r or "warp" in r.lower() for r in rev)


def test_command_status_has_no_release_facing_targets():
    from r1013.authority import COMMAND_STATUS
    for cmd, rec in COMMAND_STATUS.items():
        assert rec["status"] in ("CURRENT", "IMPLEMENTED", "REFUSED",
                                 "HISTORICAL"), cmd
        if rec["status"] == "REFUSED":
            assert rec.get("reason"), cmd


def test_release_docs_carry_no_preimplementation_banner():
    manual = pathlib.Path(__file__).resolve().parents[2] / "docs" / \
        "r1013" / "manual"
    hits = [p for p in manual.rglob("*.md")
            if "pre-implementation baseline" in
            p.read_text(encoding="utf-8")]
    assert hits == []


def test_refused_command_absent_from_cli_reference():
    ref = pathlib.Path(__file__).resolve().parents[2] / "docs" / \
        "r1013" / "manual" / "02_USER_MANUAL" / "CLI_REFERENCE.md"
    text = ref.read_text(encoding="utf-8")
    assert "rgcs frequency coordinate 4096" not in text
    assert "NOT shipped" in text


# ------------------------------------------------------- Tranche B
def test_examples_validate():
    for name in ("crystal_minimum.json", "crystal_complete.json"):
        rec = json.loads((EX / name).read_text())
        v = validate(rec)
        assert v["ok"], (name, v["errors"])


def test_template_requires_measurements():
    v = validate(TEMPLATE)
    assert not v["ok"]
    assert any(e["code"] == "RGCS-E004" for e in v["errors"])
    assert all(e["repair"] for e in v["errors"])


@pytest.mark.parametrize("mutate,code", [
    (lambda r: r["geometry"].update(length_mm=-5), "RGCS-E005"),
    (lambda r: r["geometry"].update(narrow_diameter_mm=99.0),
     "RGCS-E007"),
    (lambda r: r["geometry"].update(diameter_mode="diagonal"),
     "RGCS-E006"),
    (lambda r: r["geometry"].update(facets=2), "RGCS-E005"),
    (lambda r: r["geometry"].update(female_angle_deg=190.0),
     "RGCS-E005"),
    (lambda r: r.update(schema_version="rgcs.crystal/0.9"),
     "RGCS-E003"),
    (lambda r: r["material"].update(handedness="chiral"),
     "RGCS-E006"),
    (lambda r: r["orientation"].update(status="guessed"),
     "RGCS-E006"),
    (lambda r: r["geometry"].update(length_mm=10.0), "RGCS-E007"),
])
def test_adversarial_fields(mutate, code):
    rec = good_rec()
    mutate(rec)
    v = validate(rec)
    assert not v["ok"]
    assert code in [e["code"] for e in v["errors"]], v["errors"]


def test_nan_and_string_numbers_rejected():
    rec = good_rec()
    rec["geometry"]["length_mm"] = "77.8"
    assert not validate(rec)["ok"]
    rec = good_rec()
    rec["geometry"]["length_mm"] = float("nan")
    assert not validate(rec)["ok"]


def test_canonical_hash_deterministic_and_order_free():
    rec = good_rec()
    shuffled = json.loads(json.dumps(rec))
    shuffled["geometry"] = dict(reversed(list(rec["geometry"].items())))
    assert specimen_hash(rec) == specimen_hash(shuffled)
    assert canonical_json(rec) == canonical_json(shuffled)


def test_migrate_never_mutates_input():
    legacy = {"schema_version": "old", "specimen_id": "x", "name": "x",
              "material": {"material_id": "alpha_quartz"},
              "geometry": {"length": 50.0, "wide_diameter": 20.0}}
    before = copy.deepcopy(legacy)
    out = migrate(legacy)
    assert legacy == before
    assert out["schema_version"].endswith("/1.0")
    assert out["geometry"]["length_mm"] == 50.0
    assert out["provenance"]["migration"]


def test_readiness_gates_minimum_record():
    rec = json.loads((EX / "crystal_minimum.json").read_text())
    r = readiness(rec)
    assert r["quick_estimate"] and not r["mesh_and_modes"]
    with pytest.raises(UserError) as ei:
        geometry_report(rec)
    assert ei.value.code == "RGCS-E008"


def test_source_claims_never_measurements():
    rec = good_rec()
    rec["source_claims"] = [{"mass_g": 100.0, "note": "claimed"}]
    v = validate(rec)
    assert v["ok"]
    assert any("never used as a measurement" in w for w in v["warnings"])
    # and the claim does not affect density-check
    d = density_check(rec)
    assert abs(d["mass_g"] - 68.0) < 1e-12


def test_density_check_flags_mismatch():
    rec = good_rec()
    rec["measurements"]["mass_g"] = 40.0        # way off for the volume
    d = density_check(rec)
    assert d["consistent"] is False
    assert d["error"]["code"] == "RGCS-E009"


def test_fixture_registry_and_refusals():
    from r1013.fixtures import (FIXTURE_TYPES, make_fixture,
                                validate_fixture)
    assert set(FIXTURE_TYPES) == {"free", "free_suspension",
                                  "three_point", "soft_pad",
                                  "center_clamp", "end_clamp",
                                  "custom"}
    for t in FIXTURE_TYPES:
        if t == "custom":
            continue
        f = make_fixture(t)
        assert validate_fixture(f)["ok"]
        assert f["model"]["approximation"]
    with pytest.raises(UserError):
        make_fixture("vice_grip")
    with pytest.raises(UserError):
        make_fixture("custom")                  # no contacts
    f = make_fixture("custom",
                     contacts=[{"position_mm": [0, 0, 10]}])
    assert validate_fixture(f)["ok"]


# ------------------------------------------------------- Tranche C
def test_hand_calculation_77p8_reproduced():
    """The documented 77.8 mm / 6310 m/s screening numbers."""
    from r1013.estimate import quick_estimate
    rec = json.loads((EX / "crystal_minimum.json").read_text())
    r = quick_estimate(rec, ("axial-quarter", "axial-half"), 1)
    q = [e for e in r["estimates"] if e["model"] == "axial-quarter"][0]
    h = [e for e in r["estimates"] if e["model"] == "axial-half"][0]
    assert abs(q["frequency_hz"] - 6310 / (4 * 0.0778)) < 0.5
    assert abs(h["frequency_hz"] - 6310 / (2 * 0.0778)) < 0.5
    for e in r["estimates"]:
        for k in ("formula", "speed_m_s", "boundary_assumption",
                  "uncertainty_hz", "harmonic", "evidence_class"):
            assert k in e
        assert e["evidence_class"] == "ESTIMATE"


def test_estimate_uses_christoffel_when_oriented():
    from r1013.estimate import quick_estimate
    rec = good_rec()
    rec["orientation"] = {"status": "known",
                          "euler_zxz_deg": [0.0, 0.0, 0.0]}
    r = quick_estimate(rec)
    assert "Christoffel" in r["estimates"][0]["speed_basis"]
    assert abs(r["speed_m_s"] - 6310) < 100     # c-axis qL near 6330


def test_christoffel_matches_frozen_authority():
    from rgcs_core.anisotropy import wave_speeds
    from r1013.christoffel_api import directions_report
    rep = directions_report([[0, 0, 1]], frame="crystal")
    frozen = wave_speeds([0, 0, 1])
    assert abs(rep["rows"][0]["qL_m_s"]
               - frozen["v_quasi_long_m_s"]) < 1e-6


def test_orientation_ensemble_bracket():
    from r1013.christoffel_api import orientation_ensemble
    e = orientation_ensemble(n=16)
    assert e["qL_min_m_s"] < e["qL_median_m_s"] < e["qL_max_m_s"]
    assert e["note"].startswith("orientation unknown")


def test_certificate_seals_and_verifies():
    from r1013.certificate import build_certificate, verify_certificate
    from r1013.estimate import quick_estimate
    rec = good_rec()
    cert = build_certificate(rec, quick_estimate(rec), "estimate")
    assert verify_certificate(cert)["ok"]
    cert["frequencies_hz"] = [1.0]
    assert not verify_certificate(cert)["ok"]


def test_certificate_rejects_measurement_class():
    from r1013.certificate import build_certificate
    rec = good_rec()
    with pytest.raises(UserError) as ei:
        build_certificate(rec, {"evidence_class": "MEASUREMENT"},
                          "fake")
    assert ei.value.code == "RGCS-E015"
    assert "MEASUREMENT" not in SOFTWARE_EMITTABLE


# ---------------------------------------------- Tranche C: FEM (gmsh)
def test_custom_fem_modes_free_body(tmp_path):
    from r1013.fem_api import elastic_modes, mesh_specimen
    rec = good_rec()
    m = mesh_specimen(rec, 12.0, tmp_path)
    sol = elastic_modes(rec, m, 8)
    assert sol["n_rigid_modes"] == 6
    assert sol["frequencies_hz"]
    assert sol["evidence_class"] == "NUMERICAL_SIMULATION"
    assert sol["orthonormality_error"] < 1e-8
    # mass patch: rho * V within 2 percent on the coarse mesh
    vol = geometry_report(rec)["analytic_volume_mm3"] * 1e-9
    assert abs(sol["total_mass_kg"] - 2648.0 * vol) / (2648.0 * vol) \
        < 0.02
    assert any("orientation" in w for w in sol["warnings"])


def test_fem_refuses_unknown_material(tmp_path):
    from r1013.fem_api import elastic_modes
    rec = good_rec()
    rec["material"]["material_id"] = "calcite"
    with pytest.raises(UserError) as ei:
        elastic_modes(rec, {"nodes_m": None, "tets": None}, 4)
    assert ei.value.code == "RGCS-E013"


def test_canonical_variants_roundtrip_through_specimen():
    """ideal_n7 and nominal exported as specimen records reproduce
    their geometry with zero drift (Phase 10)."""
    from rscs2_core.crystal110 import (analytic_volume_mm3,
                                       build_crystal)
    from r1013.specimen import to_crystal
    for variant in ("ideal_n7", "nominal"):
        c = build_crystal(variant)
        rec = {"schema_version": "rgcs.crystal-specimen/1.0",
               "specimen_id": f"rt-{variant}", "name": variant,
               "material": {"material_id": "alpha_quartz"},
               "geometry": {"length_mm": c.length_mm,
                            "wide_diameter_mm": c.wide_diameter_mm,
                            "narrow_diameter_mm": c.narrow_diameter_mm,
                            "facets": c.facets,
                            "female_angle_deg": c.female_angle_deg,
                            "male_angle_deg": c.male_angle_deg,
                            "diameter_mode": "across_vertices",
                            "angle_mode": "face_slope"}}
        c2 = to_crystal(rec)
        assert c2.length_mm == c.length_mm
        assert abs(analytic_volume_mm3(c2) - analytic_volume_mm3(c)) \
            < 1e-9


def test_imported_mesh_audits(tmp_path):
    import meshio
    import numpy as np
    from r1013.fem_api import import_mesh
    # unit cube, two-per-face split into 6 tets: closed and manifold
    pts = np.array([[x, y, z] for x in (0, 1) for y in (0, 1)
                    for z in (0, 1)], float)
    tets = np.array([[0, 1, 3, 7], [0, 1, 5, 7], [0, 4, 5, 7],
                     [0, 2, 3, 7], [0, 2, 6, 7], [0, 4, 6, 7]])
    # enforce consistent positive orientation (swap two nodes where
    # the signed volume is negative)
    for t in tets:
        a, b, c, d = pts[t]
        if np.dot(np.cross(b - a, c - a), d - a) < 0:
            t[0], t[1] = t[1], t[0]
    f = tmp_path / "cube.vtk"
    meshio.write(f, meshio.Mesh(pts, [("tetra", tets)]))
    out = import_mesh(f, "mm", expected_volume_mm3=1.0)
    assert out["manifest"]["audit_status"] == "PASS"
    assert abs(out["manifest"]["volume_mm3"] - 1.0) < 1e-9
    # wrong unit refuses on volume
    with pytest.raises(UserError) as ei:
        import_mesh(f, "m", expected_volume_mm3=1.0)
    assert ei.value.code == "RGCS-E012"


# ------------------------------------------------------- Tranche E
def test_timing_compiler_exact():
    from r1013.timing import timing_relationship, timing_table
    t = timing_relationship()
    assert t["carrier_hz"] == 4096
    assert t["nominal_macrocycle_ms"] == 552.0
    assert t["closed_macrocycle_ms"] == 552.001953125
    assert t["trim_us"] == 1.953125
    assert t["phase_states"] == 125
    assert t["phase_step_deg"] == 2.88
    assert t["closure_cycles"] == 2261
    assert t["evidence_class"] == "SOURCE_PROVENANCE_ONLY"
    tab = timing_table()
    assert len(tab) == 125
    assert tab[1]["delta_t_us"] == 1.953125
    assert tab[124]["phase_deg"] == 124 * 2.88


def test_aperture_integers_regenerated():
    from r1013 import aperture
    r = aperture.rates()
    assert (r["total_passages_per_s"], r["active_passages_per_s"],
            r["gap_passages_per_s"]) == (560, 528, 32)
    assert (r["sub_bins_total"], r["sub_bins_active"],
            r["sub_bins_blank"]) == (560, 528, 32)
    mc = aperture.master_clock()
    assert mc["ticks_per_revolution"] == 224000
    assert mc["master_clock_hz"] == 3584000
    g = aperture.geometry()
    assert abs(g["inner_radius"] - 82.2616108) < 1e-4
    assert abs(g["delta_theta_deg"] - 360 / 35) < 1e-12
    assert math.isclose(g["inner_radius"] ** 2 / g["outer_radius"] ** 2,
                        29 / 89, rel_tol=1e-12)


def test_gap_indices_refuse_selection():
    from r1013 import aperture
    assert aperture.gap_indices()["status"] == "UNDERDETERMINED"
    with pytest.raises(UserError) as ei:
        aperture.gap_indices(select=(3, 20))
    assert ei.value.code == "RGCS-E013"
    v = aperture.enumerate_gap_variants()
    assert v["count"] == 35 * 34 // 2


def test_energy_ledger_balances_and_refuses_phryll():
    from r1013.dynamic_boundary_ledger import (SOURCE_INTERPRETATIONS,
                                               energy_ledger,
                                               interpret, sidebands,
                                               gate_waveform)
    led = energy_ledger(q=13, switch_work_j=0.1, pump_energy_j=0.2,
                        loss_fraction=0.1)
    assert abs(led["balance_residual_j"]) < 1e-12
    assert led["model_status"] == "RESEARCH_ONLY_CONVENTIONAL"
    for claim in SOURCE_INTERPRETATIONS:
        assert interpret(claim)["status"] == "REFUSED"
    w = gate_waveform(0)
    sb = sidebands(w["carrier"] * w["gate"], fs_hz=8192 * 2)
    assert sb and all(s["relative_power"] <= 1.0 for s in sb)


def test_varcodec_no_extension_bit_and_splits():
    from r1013.varcodec import encode, parse_all
    pa = parse_all("165876523")
    assert pa["no_extension_bit"] is True
    assert pa["split_count"] == 1               # compact: only (0,0)
    pa = parse_all("1643789253")
    assert pa["split_count"] == 2               # (0,1) and (1,0)
    assert {(s.depth_left, s.depth_right) for s in pa["splits"]} == \
        {(0, 1), (1, 0)}
    for s in pa["splits"]:
        assert encode(s) == "1643789253"
    assert pa["state_labels_source_reported"] == [
        "toroidal_phase", "poloidal_phase", "radial_phase"]


def test_varcodec_agrees_with_locked_parser_on_corpus():
    from r1011.e3_frame import E3FrameError
    from r1013.exact_cover import WIRES_19
    from r1013.varcodec import agrees_with_e3_frame
    from r1012.corpus import golden28
    wires = [str(w) for w in golden28()["wires"]] + WIRES_19
    for w in wires:
        assert agrees_with_e3_frame(w)["agrees"], w


def test_varcodec_overflow_refuses():
    from r1013.varcodec import VarCodecError, parse_all
    with pytest.raises(VarCodecError, match="width family"):
        parse_all("1687425419853")              # the known malformed wire


def test_exact_cover_typed_negative_with_source_request():
    from r1013.exact_cover import KNOWN_PAIRS, link_test, solve
    for a, b in KNOWN_PAIRS:
        assert link_test(a, b)["linked"], (a, b)
    r = solve()
    assert r["wire_count"] == 19
    assert r["search_exhausted"]
    assert r["status"] == "NO_PARTITION_UNDER_CURRENT_CONSTRAINTS"
    assert "165872393" in r["next_source_request"]
    assert r["candidate_triples"] == 0


def test_edge_law_registry_no_selection():
    from fractions import Fraction
    from r1013.edge_law import BASE_ODDS, edge_fraction, registry, \
        select_law
    assert BASE_ODDS == Fraction(10, 9)
    reg = registry()
    assert reg["selected"] is None
    assert abs(reg["base_edge_fraction"] - 10 / 19) < 1e-12
    m0 = [f for f in reg["families"] if f["id"] == "M0_IDENTITY"][0]
    assert m0["status"] == "REJECTED_GLOBAL"
    sundial = [f for f in reg["families"]
               if f["id"] == "M3_RAD_SUNDIAL"][0]
    assert "15" in sundial["form"]
    assert sundial["status"] == "UNRESOLVED_SOURCE_CLUE"
    with pytest.raises(UserError) as ei:
        select_law("M4_CHILD_INDEXED")
    assert ei.value.code == "RGCS-E013"
    # hypothetical evaluation stays conditional
    assert "no law is selected" in edge_fraction(1.1)["conditional_on"]


def test_error_registry_complete():
    assert len(ERROR_CODES) == 15
    for code in ERROR_CODES:
        e = explain(code)
        assert e["repair"] and e["meaning"]
    with pytest.raises(UserError):
        explain("RGCS-E999")
