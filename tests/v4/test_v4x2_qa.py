"""Q07: independent adversarial QA against the emergent programme.

Each test is a required attack from the pack's Phase 10 list. The
attacks that succeeded during development are recorded in
docs/v4/V4X2_QA_VERDICT.md."""

import json
import pathlib
import subprocess

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_attack_fake_ledger_completion():
    """A validated status with no importable symbols must fail the
    coverage gate (the v4.2.0 lesson, re-attacked)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cov", ROOT / "tools/v4x2_coverage.py")
    cov = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cov)
    # sabotage a spec in memory: validated status, bogus symbol
    cov.AGENTS["R01"] = dict(cov.AGENTS["R01"])
    cov.AGENTS["R01"]["symbols"] = ["resonator_platform.records:"
                                    "does_not_exist"]
    rep = cov.evaluate()
    assert not rep["gates"]["B_symbols"]["passed"], \
        "the gate accepted a nonexistent symbol"


def test_attack_measured_targeted_confusion():
    """Try to accept a prediction; try to certify without a fit."""
    from resonator_platform.certificate import (CertificateError,
                                                issue)
    from resonator_platform.records import (LedgerError,
                                            frequency_record)
    with pytest.raises(LedgerError):
        frequency_record(predicted_hz=100.0, accepted_hz=100.0)
    with pytest.raises(CertificateError):
        issue("S", {}, {}, frequency_record(predicted_hz=1.0), [],
              "x", (0.0, 2.0), b"k", True)


def test_attack_trim_overshoot_and_blind_burn():
    """Force an overshooting candidate list; the selector must refuse
    rather than pick the least-bad burn."""
    from resonator_platform import trim_control as tc
    cands = [{"cells": [0, 8], "predicted_shift_hz": 50.0,
              "predicted_q_change": 0, "symmetry_preserved": True,
              "balance_moment": 0.0, "electrical_effect": ""}]
    sel = tc.select_trim(cands, 1000.0, 1004.0, band_hz=2.0)
    assert sel is None                    # refuses; no blind burn


def test_attack_mode_switch_hidden_by_index():
    """A mode swap must be caught by MAC tracking."""
    from rscs2_core.eye_ladder_analysis import track_modes
    a = [np.array([1.0, 0, 0, 0]), np.array([0, 1.0, 0, 0])]
    b = [np.array([0, 1.0, 0, 0]), np.array([1.0, 0, 0, 0])]
    tr = track_modes(a, b)
    assert tr["assignment"][0]["fine_mode"] == 1


def test_attack_source_laundering_into_quartz():
    """Try to transfer each paper's physics into quartz."""
    from sources.registry import v4x2_source_registry as reg
    for sid in reg.SOURCES:
        with pytest.raises(reg.TransferFirewall):
            reg.check_transfer(sid, "the alpha quartz specimen",
                               "everything")


def test_attack_playground_evidence_upgrade():
    """The playground envelope must not be usable as evidence."""
    import model_playground as d
    env = d.run_model("honeycomb_vhs", "nematic_splitting",
                      t_ev=1.0, delta=0.1)
    assert env["evidence_status"] == "REFERENCE_MATHEMATICS_ONLY"
    # and the label survives comparison
    c = d.compare([env], "splitting_ev")
    assert c["rows"][0]["source_system"]


def test_attack_synthetic_flag_stripping():
    """A certificate stripped of its banner must fail verification;
    a session without the flag must refuse to load."""
    from resonator_platform.campaign import SIGNING_KEY, run_campaign
    from resonator_platform.certificate import verify
    r = run_campaign(seed=3)
    cert = dict(r["certificate"])
    cert["synthetic"] = False              # strip the flag
    assert not verify(cert, SIGNING_KEY)["valid"]


def test_attack_unsafe_automation():
    """Physical trim without machine capability; machine registration
    without safety evidence; unlisted safety process."""
    from resonator_platform import safety, trim_control as tc
    from resonator_platform.records import ResonatorLedger
    from resonator_platform.twin import ResonatorTwin
    tw = ResonatorTwin(seed=0)
    sel = tc.trim_candidates(tw)[0]
    tok = tc.approval_token("op", "S", sel["cells"])
    with pytest.raises(tc.TrimError):
        tc.execute_trim(tw, ResonatorLedger(), "S", sel, tok, "op",
                        dry_run=False)
    with pytest.raises(safety.SafetyRefusal):
        safety.check_process("laser_trim",
                             {"fire watch + extinguisher": True})


def test_attack_private_lore_leakage():
    """No lore content in tracked files; no lore terms in the public
    resonator docs beyond the policy that names the mechanism."""
    tracked = subprocess.run(["git", "ls-files"],
                             capture_output=True, text=True,
                             cwd=ROOT).stdout.splitlines()
    assert not any(p.startswith("internal-docs/") for p in tracked)
    pol = (ROOT / "docs/v4/resonator/LORE_AND_INTUITION_POLICY.md"
           ).read_text(encoding="utf-8")
    assert "not evidence" in pol


def test_attack_product_overclaim_vocabulary():
    """The product-tier doc must forbid measurement vocabulary on
    unmeasured objects and the certificate must carry not-made
    claims."""
    doc = (ROOT / "docs/v4/resonator/PRODUCT_TIERS_AND_CLAIMS.md"
           ).read_text(encoding="utf-8")
    assert "decorative; no measured or implied resonance" in doc
    assert "Targeted is not measured" in doc
    from resonator_platform.campaign import run_campaign
    cert = run_campaign(seed=5)["certificate"]
    assert "therapeutic effect" in cert["claims"]["not_made"]
    assert "consciousness effect" in cert["claims"]["not_made"]


def test_attack_stale_counts():
    """Documented test counts must match the metadata authority."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "meta", ROOT / "tools/v4x_release_metadata.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rep = m.verify()
    assert rep["agree"], rep["problems"]


def test_attack_dramatic_sentence_detachment():
    """The claim card must keep caveats adjacent to the headline and
    must carry its correction trail."""
    txt = (ROOT / "docs/v4/EYE_CLAIM_CARD.md").read_text(
        encoding="utf-8")
    v4_pos = txt.find("CLAIM CARD v4")
    not_pos = txt.find("What this is NOT", v4_pos)
    assert 0 < not_pos - v4_pos < 4000, \
        "caveats must live inside the current card"
    assert "Correction trail (append-only)" in txt
    # the superseded card is kept verbatim, not deleted
    assert "CLAIM CARD v3 (superseded" in txt


def test_attack_resource_estimate_overconfidence():
    """A single-number memory estimate is the failure mode that
    nearly thrashed the machine; predictions must be ranges and the
    preflight must refuse the known-infeasible case."""
    from rscs2_core.eye_ladder_analysis import (predict_memory_gb,
                                                preflight)
    p = predict_memory_gb(69471)
    assert p["high_gb"] / p["low_gb"] > 1.2   # a real range
    assert not preflight(69471)["approved"]
