"""V3 pack tests: phi arithmetic, near-neighbor discipline, and the
actual sale-crystal triage.

Adapted from 08_TESTS/sample_tests_v3_phi_gravity_and_actual_crystals
in the 2026-08-06 V3 pack. Everything here is arithmetic over
source-reported values and sale-list estimates; nothing is a
measurement and nothing validates the source's physics.
"""

from __future__ import annotations

import math
import pathlib

from rgcs_workbench.public_cage import claim_firewall as CF
from rgcs_workbench.public_cage import phi_ladders as PL

ROOT = pathlib.Path(__file__).resolve().parents[2]


# ------------------------------------------------- phi arithmetic

def test_phi_planck_hydrogen_radii_source_values():
    assert abs(PL.phi_planck_length_angstrom(116) - 0.282537) < 0.001
    assert abs(PL.phi_planck_length_angstrom(117) - 0.457154) < 0.001
    assert abs(PL.phi_planck_length_angstrom(118) - 0.739691) < 0.001


def test_phi_planck_time_frequency_source_value():
    f171 = PL.phi_planck_frequency_hz(171)
    assert abs(f171 - 13.563688e6) / 13.563688e6 < 0.001


def test_ladders_regenerate_from_their_formulas():
    for row in PL.load_phi_schumann_ladder():
        assert math.isclose(row["frequency_hz"],
                            PL.phi_schumann_hz(row["n"]), rel_tol=1e-9)
    for row in PL.load_phi_planck_frequency_ladder():
        assert math.isclose(row["frequency_hz"],
                            PL.phi_planck_frequency_hz(row["n"]),
                            rel_tol=1e-9)
    for row in PL.load_phi_planck_hydrogen_radii():
        assert math.isclose(row["radius_angstrom"],
                            PL.phi_planck_length_angstrom(row["n"]),
                            rel_tol=1e-9)


# ------------------------------------------- near-neighbor discipline

def test_keep_near_neighbors_separate():
    assert 4079.44 != 4096
    assert 20.4992 != 20.48
    assert 13.563688e6 != 13.18359375e6
    for receipt in PL.near_neighbor_receipts():
        assert receipt["distinct"] is True
        assert receipt["classification"] == "CANDIDATE_BRIDGE"
        assert receipt["rule"] == (
            "FAMILIES_NEVER_MERGE_WITHOUT_CORRECTION_RULE")


def test_near_neighbor_offsets_are_recorded_and_nonzero():
    offsets = [abs(r["offset_percent"])
               for r in PL.near_neighbor_receipts()]
    assert all(o > 0.05 for o in offsets)
    assert any(o > 2.0 for o in offsets)      # the 13.56 vs 13.18 MHz gap


def test_phi_schumann_n13_is_near_but_not_4096():
    n13 = PL.phi_schumann_hz(13)
    assert abs(PL.offset_percent(n13, 4096.0)) < 1.0
    assert n13 != 4096.0


# ------------------------------------------- actual sale-crystal triage

def test_scored_dataset_is_sale_derived_and_two_lane():
    assert PL.validate_scored_modes() == []
    rows = PL.load_scored_modes()
    assert len(rows) >= 9
    assert all(r["crystal_id"].startswith("SALE_") for r in rows)


def test_csv_and_json_scored_datasets_agree():
    js = PL.load_scored_modes()
    cs = PL.load_scored_modes_csv()
    assert len(js) == len(cs)
    assert [r["crystal_id"] for r in js] == [r["crystal_id"] for r in cs]


def test_best_phi_candidate_is_the_125mm_actual_sale_crystal():
    phi_n16 = PL.phi_schumann_hz(16)
    assert abs(PL.offset_percent(17367.72, phi_n16)) < 0.6
    ranking = PL.rank_candidates()
    best = ranking["score_phi_schumann_family"]
    assert best["crystal_id"] == "SALE_HIMALAYAN_12SIDED_125MM"
    assert abs(best["offset_percent"]) < 0.6


def test_157mm_is_rgcs_octave_champion_not_phi_champion():
    rgcs_target = 4096 * 5
    axial_157 = 20098.13
    assert abs(PL.offset_percent(axial_157, rgcs_target)) < 2.0
    assert abs(PL.offset_percent(axial_157, PL.phi_schumann_hz(16))) > 10.0
    ranking = PL.rank_candidates()
    best = ranking["score_rgcs_4096_family"]
    assert best["crystal_id"] == "SALE_HIMALAYAN_8SIDED_157MM"
    assert best["mode"] == "axial_f1"


def test_multi_hit_phi_candidate_is_the_rutilated_138mm():
    ranking = PL.rank_candidates()
    multi = ranking["best_multi_hit_phi"]
    assert multi["crystal_id"] == "SALE_RUTILATED_24SIDED_138MM"
    assert len(multi["modes_within_3p5_percent"]) >= 2


def test_ranking_is_estimates_not_measurements():
    ranking = PL.rank_candidates()
    assert ranking["basis"] == "SALE_LIST_ESTIMATES_NOT_MEASUREMENTS"
    assert ranking["classification"] == "NOT_RGCS_VALIDATION"


# ------------------------------------------------------- claim scans

def test_new_docs_and_data_scan_clean():
    targets = [ROOT / "docs" / "research" / "phi_ladder_comparison.md",
               ROOT / "docs" / "research" / "actual_sale_crystal_triage.md"]
    report = CF.firewall_report(CF.scan_paths(targets))
    assert report["clean"], report
    surface = CF.cage_public_surface(ROOT)
    names = {p.name for p in surface}
    assert "phi_schumann_ladder.json" in names
    assert "actual_sale_crystal_phi_rgcs_scored_modes.csv" in names
    assert CF.firewall_report(CF.scan_paths(surface))["clean"]


def test_source_language_stays_classified_not_validated():
    text = (ROOT / "docs" / "research" / "phi_ladder_comparison.md"
            ).read_text(encoding="utf-8")
    assert "SOURCE_REPORTED_ARITHMETIC" in text
    assert "NOT_RGCS_VALIDATION" in text
    assert "CANDIDATE_BRIDGE" in text
    assert "the claim is not advanced" in text.lower()
