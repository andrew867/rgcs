"""Y01/Y02 ladder analysis + B01 source registry tests."""

import numpy as np
import pytest

from rscs2_core import eye_ladder_analysis as ela
from sources.registry import v4x2_source_registry as srcreg


# --- Y001/Y006: canonical immutability ---------------------------------

def test_canonical_record_accessor_returns_copy():
    a = ela.canonical_record()
    a["separation_mm"] = 999.0
    b = ela.canonical_record()
    assert b["separation_mm"] == 3.906
    assert b["candidate_mm"] == [-0.295, -0.205, 102.240] or \
        tuple(b["candidate_mm"]) == (-0.295, -0.205, 102.240)


def test_interpretation_appends_never_replaces():
    rep = ela.ladder_interpretation()
    assert rep["supersedes"] is None
    assert "v4.1 canonical record" in rep["appends_to"]
    assert rep["canonical_v41"]["separation_mm"] == 3.906
    # scope language: computational vs physical separated
    assert "IMPLEMENTED IDEALIZED MODEL" in \
        rep["verdict"]["scope"]
    assert "never 'there is no cluster'" in \
        rep["verdict"]["language_rule"]


# --- Y002: MAC tracking ---------------------------------------------------

def test_mac_identity_and_orthogonal():
    a = np.array([1.0, 0.0, 2.0, -1.0])
    assert ela.mac(a, a) == pytest.approx(1.0)
    assert ela.mac(a, np.array([0.0, 1.0, 0.5, 1.0])) < 1.0
    assert ela.mac(np.array([1, 0.0]), np.array([0.0, 1])) == \
        pytest.approx(0.0)


def test_mode_permutation_detected():
    """Modes swapped between meshes must be tracked by MAC, not by
    index (the Y01 permutation test)."""
    m1 = [np.array([1.0, 0, 0, 0]), np.array([0, 1.0, 0, 0])]
    m2 = [np.array([0, 1.0, 0, 0]), np.array([1.0, 0, 0, 0])]
    tr = ela.track_modes(m1, m2)
    assert tr["assignment"][0]["fine_mode"] == 1
    assert tr["assignment"][1]["fine_mode"] == 0


def test_lost_mode_reported_not_paired():
    m1 = [np.array([1.0, 0, 0, 0])]
    m2 = [np.array([0.1, 0.9, 0.3, -0.2])]
    tr = ela.track_modes(m1, m2, threshold=0.9)
    assert tr["lost"] and tr["lost"][0]["status"] == \
        "LOST_OR_SWITCHED"


# --- Y003: convergence model dependence -------------------------------------

def test_convergence_models_and_spread():
    h = np.array([3.423, 2.362, 1.803])
    z = np.array([100.986, 99.989, 99.783])
    fit = ela.fit_convergence(h, z)
    assert set(fit["limits"]) == {"linear_h", "quadratic_h2",
                                  "geometric"}
    assert fit["extrapolation_spread"] > 0
    assert "spread" in fit["rule"] or "model" in fit["rule"]


def test_synthetic_convergent_ladder_recovers_limit():
    h = np.array([4.0, 2.0, 1.0])
    v = 10.0 + 0.5 * h ** 2          # exactly quadratic
    fit = ela.fit_convergence(h, v)
    assert fit["limits"]["quadratic_h2"] == pytest.approx(10.0,
                                                          abs=1e-9)


def test_signed_separation_components():
    s = ela.signed_separation((0, 0, 0), (3, 4, 12))
    assert s["magnitude_mm"] == pytest.approx(13.0)
    assert s["transverse_mm"] == pytest.approx(5.0)
    assert s["dz_mm"] == 12.0


# --- Y009-Y014: resource model -------------------------------------------------

def test_memory_model_backtests_on_calibration():
    m = ela.memory_model()
    assert 1.5 < m["exponent"] < 2.5      # 3-D fill-in, not the 2-D 1.5
    assert m["max_log_residual"] < 0.7
    assert "150x" in m["history"]


def test_prediction_is_a_range_not_a_number():
    p = ela.predict_memory_gb(69471)      # the cl=1.25 case
    assert p["low_gb"] < p["point_gb"] < p["high_gb"]
    assert p["high_gb"] > 31.6 * 0.6      # correctly infeasible here


def test_preflight_refuses_infeasible_and_approves_feasible():
    big = ela.preflight(69471)
    assert not big["approved"] and "REFUSED" in big["action"]
    small = ela.preflight(5394)
    assert small["approved"]


def test_job_manifest_complete():
    j = ela.job_manifest(1.25, 69471)
    assert j["schema"] == "rgcs.eye.job/1"
    assert j["expected_memory_gb"][1] > j["expected_memory_gb"][0]
    assert "incremental" in j["checkpointing"]


# --- B01: sources ------------------------------------------------------------

def test_all_five_sources_registered_with_hashes():
    assert len(srcreg.SOURCES) == 5
    for sid, s in srcreg.SOURCES.items():
        assert len(s["sha256_prefix"]) == 16
        assert s["size_bytes"] > 0
        assert s["doi"] and s["claim_card"]
        assert s["allowed_transfers"] and s["forbidden_transfers"]
        for eq in s["equations"]:
            assert eq["provenance"] and eq["implemented"]


def test_hash_regression_against_local_files():
    """When the corpus is present locally, verify the hashes; on CI
    (no internal-docs) the registry stands alone."""
    import hashlib
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2]
    local = root / srcreg.LOCAL_DIR
    if not local.exists():
        pytest.skip("corpus not present (expected on CI)")
    for s in srcreg.SOURCES.values():
        p = local / s["file"]
        assert p.exists(), s["file"]
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h.startswith(s["sha256_prefix"]), s["file"]
        assert p.stat().st_size == s["size_bytes"]


def test_transfer_firewall_rejects_quartz():
    with pytest.raises(srcreg.TransferFirewall):
        srcreg.check_transfer("SRC-V4X2-01", "alpha quartz wand",
                              "two-level detuning")
    with pytest.raises(srcreg.TransferFirewall):
        srcreg.check_transfer("SRC-V4X2-05",
                              "the 110 mm crystal specimen",
                              "coherent-sum mathematics")
    ok = srcreg.check_transfer("SRC-V4X2-05",
                               "abstract wave mathematics",
                               "coherent-sum decomposition")
    assert ok["allowed"]


def test_lookup_by_doi_file_and_equation():
    assert srcreg.lookup("10.1063/5.0321755")["file"] == \
        "065211_1_5.0321755.pdf"
    assert srcreg.lookup("pyt8-d7rt.pdf")["doi"] == \
        "10.1103/pyt8-d7rt"
    eq = srcreg.lookup("EQ-V4X2-05b")
    assert "azimuthal" in eq["provenance"]
    with pytest.raises(KeyError):
        srcreg.lookup("EQ-NOPE")


def test_in_press_drift_guard_and_concept_map():
    g = srcreg.drift_guard()
    assert "in press" in g["SRC-V4X2-02"]["state"]
    assert "never overwrite" in \
        g["SRC-V4X2-02"]["action_on_final_publication"]
    cm = srcreg.concept_map()
    assert "do NOT jointly establish" in cm["explicit_disclaimer"]


def test_conjecture_preserved_not_laundered():
    s = srcreg.SOURCES["SRC-V4X2-04"]
    spec = " ".join(s["claim_card"]["speculation"])
    assert "conjectural" in spec
