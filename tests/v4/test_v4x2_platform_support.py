"""Support-lane tests: B00 baseline, D01 stats, S01 safety, O01
orphans, Y03 census artifact, docs presence, coverage gates."""

import importlib.util
import json
import pathlib

import pytest

from resonator_platform import safety, stats

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- B00 -----------------------------------------------------------------

def test_baseline_frozen_history_and_snapshot():
    b = _load("v4x2_baseline")
    f = b.verify_frozen()
    assert f["passed"], f["problems"]
    snap = b.build()
    assert snap["schema"].startswith("rgcs.v4x2")
    assert snap["frozen_history"]["passed"]
    assert snap["branch_decision"]["programme_branch"] == "v4-dev"
    assert any(bl["id"] == "compute" for bl in snap["blockers"])


def test_baseline_tree_classification_preserves_user_work():
    b = _load("v4x2_baseline")
    t = b.classify_tree()
    assert "nothing here is deleted" in t["rule"]


# --- D01 -----------------------------------------------------------------

def test_mds_floor_and_prereg_refusal():
    m = stats.minimum_detectable_shift(0.4, 0.05)
    assert m["mds_hz"] > 3 * 0.4
    with pytest.raises(stats.StatsError):
        stats.preregistration(1000.0, band_hz=0.5, max_iterations=4,
                              remount_scatter_hz=0.4,
                              fit_uncertainty_hz=0.05)
    ok = stats.preregistration(1000.0, band_hz=3.0,
                               max_iterations=4,
                               remount_scatter_hz=0.4,
                               fit_uncertainty_hz=0.05)
    assert ok["declared_before_first_measurement"]
    assert len(ok["stopping_rules"]) == 4


def test_sequential_alpha_and_post_selection():
    a = stats.sequential_alpha(5)
    assert a["alpha_per_look"] == pytest.approx(0.01)
    fits = [{"error_hz": 5.0}, {"error_hz": 0.1},
            {"error_hz": 2.0}]
    g = stats.post_selection_guard(fits)
    assert g["post_selected"]          # best (idx 1) != last (idx 2)
    assert g["reported_index"] == 2


def test_multi_frequency_penalty_and_bootstrap():
    p = stats.multi_frequency_search_penalty(50, 5.0, 1000.0)
    assert p["expected_chance_hits"] == pytest.approx(0.5)
    ci = stats.bootstrap_ci([1.0, 1.2, 0.9, 1.1, 1.05])
    assert ci["ci"][0] < ci["mean"] < ci["ci"][1]


# --- S01 -----------------------------------------------------------------

def test_safety_refuses_without_evidence():
    with pytest.raises(safety.SafetyRefusal):
        safety.check_process("laser_trim", {})
    with pytest.raises(safety.SafetyRefusal):
        safety.check_process("unlisted_process", {})
    ok = safety.check_process("laser_trim", {
        "class-1 enclosure (interlocked)": True,
        "fume extraction with filtration rated for the material":
            True,
        "fire watch + extinguisher": True,
        "laser safety officer sign-off": True})
    assert ok["enabled"]
    assert "does not persist" in ok["note"]


def test_fr4_hard_refusal_is_declared():
    spec = safety.PROCESS_LIMITS["laser_trim"]
    assert any("FR-4" in r for r in spec["hard_refusals"])
    sw = safety.stop_work_record("smell of burning", "anyone")
    assert "no override path" in sw["restart_requires"]


# --- O01 -----------------------------------------------------------------

def test_orphan_sweep_all_disposed():
    o = _load("v4x2_orphan_sweep")
    rep = o.sweep()
    assert rep["orphans_found"] >= 6
    assert not rep["undisposed"]
    assert rep["total_coverage"] == 280 + rep["orphans_found"]
    ids = [r["id"] for r in rep["rows"]]
    assert len(ids) == len(set(ids))
    # census discoveries are registered
    assert any("female-apex" in r["title"] for r in rep["rows"])


# --- Y03 artifact -----------------------------------------------------------

def test_census_artifact_language_and_findings():
    p = ROOT / "docs/v4/proof/C02/independent_census.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    st = d["findings"]["statement"]
    assert "not a nonexistence claim" in st
    assert "not a physical measurement" in st
    assert d["eigenspace_tracking"]["tracked"]
    assert max(d["eigenspace_tracking"]["principal_angles_deg"]) < 30
    # unbiased: no nearest-selection notion anywhere in the config
    assert "no nearest-to-candidate" in d["purpose"] or \
        "no nearest" in d["purpose"]


def test_claim_card_versioned_with_corrections():
    txt = (ROOT / "docs/v4/EYE_CLAIM_CARD.md").read_text(
        encoding="utf-8")
    assert "CLAIM CARD v4" in txt
    assert "Correction trail" in txt
    assert "one apex feature" in txt.lower() or \
        "One apex feature" in txt
    assert "What this is NOT" in txt


# --- coverage gates -----------------------------------------------------------

def test_v4x2_coverage_all_gates_pass():
    cov = _load("v4x2_coverage")
    rep = cov.evaluate()
    assert rep["total"] == 280
    for k, v in rep["gates"].items():
        assert v["passed"], f"{k}: {v['failures'][:6]}"


def test_snapshot_matches_pack_when_present():
    snap = json.loads((ROOT / "docs/v4/V4X2_LEDGER_IDS.json"
                       ).read_text(encoding="utf-8"))
    assert snap["total"] == 280
    pack = ROOT / ("internal-docs/plans-v4/RGCS_Post_v4_2_Emergent_"
                   "Resonator_Prompt_Pack_v2/coverage_ledger.json")
    if not pack.exists():
        pytest.skip("pack not present (expected on CI)")
    rows = json.loads(pack.read_text(encoding="utf-8"))
    assert {r["id"] for r in rows} == set(snap["ids"])


# --- docs presence (R12/V01/P01/P02/H01/L01/L02) -------------------------------

@pytest.mark.parametrize("doc", [
    "docs/v4/resonator/CLOSED_LOOP_PLATFORM.md",
    "docs/v4/resonator/NEW_PAPER_REFERENCE_MODELS.md",
    "docs/v4/resonator/EYE_POSTREFINEMENT_AND_RESOURCES.md",
    "docs/v4/resonator/BROADCAST_HERITAGE.md",
    "docs/v4/resonator/PRODUCT_TIERS_AND_CLAIMS.md",
    "docs/v4/resonator/OPEN_COMMONS_AND_ASSURANCE.md",
    "docs/v4/resonator/LORE_AND_INTUITION_POLICY.md",
    "docs/v4/resonator/PUBLIC_NARRATIVE_AND_FACTCHECK.md",
    "docs/v4/resonator/INTUITION_LEDGER.json",
    "docs/v4/EYE_CLAIM_CARD.md",
])
def test_required_doc_exists(doc):
    assert (ROOT / doc).exists()


def test_private_lore_never_in_repo():
    """L01: the lore ledger is local-only; no lore content file may
    be tracked. The POLICY is public; the CONTENT never is."""
    import subprocess
    out = subprocess.run(
        ["git", "ls-files", "internal-docs/"],
        capture_output=True, text=True, cwd=ROOT).stdout
    assert out.strip() == "", "internal-docs must stay untracked"


def test_intuition_ledger_baseline_labelled_retrospective():
    d = json.loads((ROOT / "docs/v4/resonator/INTUITION_LEDGER.json"
                    ).read_text(encoding="utf-8"))
    assert d["append_only"]
    for e in d["entries"]:
        assert e["cohort"] == "RETROSPECTIVE_BASELINE"
        assert e["skill_evidence"] is False
        assert e["outcome"] in d["outcome_vocabulary"]
    # the weak analogy is recorded, not hidden
    assert any(e["outcome"] == "WEAK_ANALOGY" for e in d["entries"])
