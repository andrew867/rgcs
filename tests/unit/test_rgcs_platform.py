"""Unit tests for the Agent 08 platform tranche: FEA export contract,
crystal DB persistence + migration, HG memory persistence (H-15/H-17/H-19
now machine-tested), provenance graph, waveform preview, and the V2-WIN-01
bundle arcname rule."""
from __future__ import annotations

import json
import math

import numpy as np
import pytest

from rgcs_core.crystal_db import (CRYSTAL_DB_SCHEMA_VERSION, add_record,
                                  get_record, load_db, migrate, new_record,
                                  save_db)
from rgcs_core.fea_export import (fea_export, material_card,
                                  verify_fea_export, write_fea_export)


# --- FEA export ---

def test_material_card_matches_anisotropy():
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_C_GPA,
                                      ALPHA_QUARTZ_DENSITY_KG_M3)
    card = material_card()
    assert card["density_kg_m3"] == ALPHA_QUARTZ_DENSITY_KG_M3
    assert np.allclose(np.array(card["stiffness_voigt_pa"]),
                       ALPHA_QUARTZ_C_GPA * 1e9)
    assert card["classification"] == "Established"


def test_fea_export_roundtrip(tmp_path):
    geo = {"length_mm": 154.0, "diameter_wide_mm": 40.0,
           "diameter_narrow_mm": 30.0, "facet_count": 6}
    doc = fea_export("SP-Q154-001", geo,
                     {"z1_deg": 10.0, "x_deg": 5.0, "z2_deg": 0.0})
    assert doc["orientation_known"]
    assert "anisotropic" in doc["model_selection_note"]
    p = write_fea_export(doc, tmp_path / "fea" / "q154.json")
    assert verify_fea_export(p)
    # tamper -> verification fails
    tampered = json.loads(p.read_text())
    tampered["geometry"]["length_mm"] = 155.0
    p.write_text(json.dumps(tampered))
    assert not verify_fea_export(p)


def test_fea_export_unknown_orientation_keeps_scalar_band():
    geo = {"length_mm": 154.0, "diameter_wide_mm": 40.0,
           "diameter_narrow_mm": 30.0, "facet_count": 6}
    doc = fea_export("SP-X", geo, None)
    assert not doc["orientation_known"]
    assert "scalar" in doc["model_selection_note"]
    with pytest.raises(ValueError):
        fea_export("SP-X", {"length_mm": 154.0}, None)


# --- crystal DB ---

def test_crystal_db_roundtrip(tmp_path):
    r1 = new_record("SP-A", 154.0, 40.0, 30.0, 6,
                    orientation_euler_zxz_deg={"z1_deg": 1.0, "x_deg": 2.0,
                                               "z2_deg": 3.0},
                    uncertainties={"length_mm": 0.05},
                    environment={"humidity_pct": 40})
    r2 = new_record("SP-B", 100.0, 30.0, 20.0, 6)
    p = save_db([r1, r2], tmp_path / "crystals.json")
    back = load_db(p)
    assert [r["specimen_id"] for r in back] == ["SP-A", "SP-B"]
    assert get_record(back, "SP-A")["uncertainties"]["length_mm"] == 0.05
    assert not get_record(back, "SP-B")["orientation_known"]
    with pytest.raises(KeyError):
        get_record(back, "SP-C")
    with pytest.raises(ValueError):
        add_record(back, r1)          # duplicate id
    with pytest.raises(ValueError):
        save_db([r1, r1], tmp_path / "dup.json")


def test_crystal_db_migration_rules():
    # newer-than-software fails loudly
    with pytest.raises(ValueError):
        migrate({"schema_version": CRYSTAL_DB_SCHEMA_VERSION + 1,
                 "records": []})
    # missing hook fails loudly (version 0 has no registered migration)
    with pytest.raises(ValueError):
        migrate({"schema_version": 0, "records": []})
    # current version is a no-op
    doc = {"schema_version": CRYSTAL_DB_SCHEMA_VERSION, "records": []}
    assert migrate(doc) == doc
    with pytest.raises(ValueError):
        new_record("SP-X", -1.0, 40.0, 30.0, 6)


# --- HG memory persistence (H-15 / H-17 / H-19 now machine-tested) ---

def _hg_record(x: float, t: float, sigma: float = 0.1):
    from rscs_core.coordinates import (ModalState, OrientationFrame,
                                       SpatialCoordinate, TimeCoordinate,
                                       Uncertainty)
    from rscs_core.memory import hg_store
    pos = SpatialCoordinate((x, 0.0, 0.0), "world")
    frame = OrientationFrame(np.eye(3), 1, "world")
    return hg_store(pos, pos, frame, TimeCoordinate(t),
                    ModalState(np.array([1 + 0j])),
                    uncertainty=Uncertainty(x, sigma))


def test_hg_persistence_roundtrip_h15(tmp_path):
    from rscs_core.memory import (allocentric_key, load_store,
                                  retrieve_by_key, save_store)
    recs = [_hg_record(1.0, 0.0), _hg_record(2.0, 1.0), _hg_record(1.0, 2.0)]
    p = save_store(recs, tmp_path / "hg.json")
    back = load_store(p)
    assert len(back) == 3
    # H-15: keyed retrieval; distinct keys never collide
    k1 = allocentric_key(back[0])
    hits = retrieve_by_key(back, k1)
    assert len(hits) == 2               # the two records at x=1.0
    assert all(r.allocentric.xyz_mm[0] == 1.0 for r in hits)
    assert retrieve_by_key(back, allocentric_key(back[1])) == [back[1]]
    assert retrieve_by_key(back, "999:999:999") == []   # true miss, no error
    # round-trip preserves the full typed record
    assert back[0].frame_consistent()
    assert back[0].uncertainty.value == 1.0


def test_hg_persistence_temporal_continuity_h17(tmp_path):
    from rscs_core.memory import load_store, save_store
    ordered = [_hg_record(1.0, 0.0), _hg_record(2.0, 1.0)]
    p = save_store(ordered, tmp_path / "ok.json")
    back = load_store(p)
    times = [r.event_time.t_s for r in back]
    assert times == sorted(times)       # append order preserved
    # non-monotonic append is a loud error unless acknowledged
    disordered = [_hg_record(1.0, 5.0), _hg_record(2.0, 1.0)]
    with pytest.raises(ValueError):
        save_store(disordered, tmp_path / "bad.json")
    p2 = save_store(disordered, tmp_path / "ack.json",
                    allow_non_monotonic=True)
    assert [r.event_time.t_s for r in load_store(p2)] == [5.0, 1.0]


def test_hg_uncertainty_calibration_h19(tmp_path):
    # H-19: an update with a SHARPER observation must not silently inflate
    # sigma; the update operator keeps the prior unless the caller supplies
    # the reconciled uncertainty explicitly (the explicit flag)
    from rscs_core.coordinates import ModalState, Uncertainty
    from rscs_core.memory import hg_update, load_store, save_store
    rec = _hg_record(1.0, 0.0, sigma=0.10)
    updated = hg_update(rec, ModalState(np.array([0.9 + 0j])),
                        Uncertainty(1.0, 0.05))
    assert updated.uncertainty.u_rel <= rec.uncertainty.u_rel
    p = save_store([updated], tmp_path / "u.json")
    assert load_store(p)[0].uncertainty.u_rel == 0.05


# --- provenance graph ---

def test_provenance_graph_builds():
    from rgcs_desktop.services.provenance_graph import build_provenance_graph
    g = build_provenance_graph()
    kinds = g["counts"]["by_kind"]
    assert kinds.get("rscs_operator", 0) >= 23
    assert kinds.get("rscs_coordinate", 0) >= 17
    assert kinds.get("source", 0) >= 6
    ids = {n["id"] for n in g["nodes"]}
    assert {"RSCS-O.4", "RSCS-O.17", "EP-01-01", "SRC-3-01"} <= ids
    # the anti-Hermitian keystone must trace to its source via an EP row
    assert any(e["from"] == "EP-01-01" and e["to"] == "RSCS-O.4"
               and e["kind"] == "feeds" for e in g["edges"])
    assert any(e["from"] == "EP-01-01" and e["to"] == "SRC-3-01"
               and e["kind"] == "adapts" for e in g["edges"])
    # determinism
    g2 = build_provenance_graph()
    assert g["nodes"] == g2["nodes"] and g["edges"] == g2["edges"]


# --- waveform preview ---

def test_waveform_preview():
    from rgcs_desktop.services.waveform_preview import (
        phase_budget_rows, preview_macro_envelope, preview_waveform)
    w = preview_waveform("carrier_4096", duration_s=0.002)
    assert w["t_s"].shape == w["value_v"].shape
    assert np.max(np.abs(w["value_v"])) == pytest.approx(2.5)  # 5 Vpp / 2
    with pytest.raises(ValueError):
        preview_waveform("nonexistent")
    env = preview_macro_envelope("half_spacing")
    # 4*(46+23)+92 = 368 ms macro
    assert env["macro_ms"] == pytest.approx(368.0)
    assert env["segments"][0] == (0.0, 46.0, "on")
    assert env["segments"][1][2] == "off"
    with pytest.raises(ValueError):
        preview_macro_envelope("double_pulse")   # D7-002: not a mode name
    from rgcs_core.timing import phase_at_coordinate
    rows = phase_budget_rows(phase_at_coordinate(4096.0, cable_length_m=2.0))
    assert rows[-1]["kind"] == "total"
    assert any(r["term"] == "cable_s" for r in rows)


# --- V2-WIN-01 arcname rule (regression guard for the fix) ---

def test_bundle_arcnames_posix(tmp_path):
    import inspect

    from rgcs_desktop.services import bundle
    src = inspect.getsource(bundle.export_bundle)
    assert "as_posix" in src            # the MIG-CODE-07 fix stays in place
    assert "str(p.relative_to" not in src
