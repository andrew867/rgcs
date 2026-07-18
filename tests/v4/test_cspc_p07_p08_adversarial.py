"""P07/P08 (A30-A36): workbook integration and the adversarial campaign.

A34 requires attacking the programme's own results. Each test below is
an attack that MUST fail to find a way through — i.e. it asserts the
firewall holds. These are the checks that would catch the programme
quietly promoting its own arithmetic into a physical claim.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "v4" / "cspc"


# --- A32 workbook integration -------------------------------------------

def test_cscp_sheets_exist_and_are_populated():
    from rgcs_workbench import REQUIRED_SHEETS
    from rgcs_workbench.workbook import generate
    wb = generate(version="4.6.0", include_private=False)
    for sheet in ("CSCP Candidates", "CSCP Tetrahedron",
                  "CSCP Spacetime", "CSCP Experiments"):
        assert sheet in REQUIRED_SHEETS
        assert wb[sheet].max_row > 1, f"{sheet} is empty"


def test_workbook_reads_the_canonical_store_not_a_spreadsheet():
    """The candidate values in the workbook must equal the values the
    tests verify, because both come from cspc.exact."""
    from cspc.exact import FOLDS
    from rgcs_workbench.canonical import build
    rows = {r["id"]: r for r in build("4.6.0").rows("cspc_candidates")}
    assert rows["FKEY-CSPC-FOLD-9"]["exact_value"] == \
        FOLDS[9].quantity.exact_str("Hz")


def test_workbook_shows_supported_precision_beside_exact():
    """Transfer firewall 8 must be visible to a reader, not only to a
    test."""
    from rgcs_workbench.canonical import build
    rows = {r["id"]: r for r in build("4.6.0").rows("cspc_candidates")}
    fold = rows["FKEY-CSPC-FOLD-9"]
    assert fold["exact_value"] == "18.25392246246337890625"
    assert fold["physically_supported_value"] == "18.3"
    assert fold["overclaims_if_quoted_exactly"] is True


def test_travel_claims_appear_as_unsupported_in_the_workbook():
    from rgcs_workbench.canonical import build
    rows = build("4.6.0").rows("cspc_spacetime")
    travel = [r for r in rows if r["kind"] == "travel_claim"]
    assert len(travel) >= 5
    assert all(r["evidence_class"] == "UNSUPPORTED" for r in travel)


def test_public_export_still_excludes_private_content():
    from rgcs_workbench.canonical import build
    store = build("4.6.0")
    pub, priv = 0, 0
    for table in store.tables:
        pub += len(store.rows(table, include_private=False))
        priv += len(store.rows(table, include_private=True))
    assert pub <= priv


# --- A34 adversarial: attacks that must NOT succeed ---------------------

def test_attack_no_module_emits_a_physical_evidence_class():
    """Attack: does any CSCP surface claim a measurement?"""
    from cspc.experiments import compile_experiments
    from cspc.spacetime import falsification_map
    from cspc.tetra import ambiguity_report
    for payload in (compile_experiments(), falsification_map(),
                    ambiguity_report()):
        assert payload.get("evidence_class") not in (
            "BENCH_MEASUREMENT", "REPLICATED_MEASUREMENT",
            "INDEPENDENT_REPLICATION")


def test_attack_cannot_launder_simulation_into_measurement():
    from cspc import ClaimBoundaryError, require_non_physical
    with pytest.raises(ClaimBoundaryError):
        require_non_physical("BENCH_MEASUREMENT", "simulation output")


def test_attack_cannot_promote_a_source_claim_by_repetition():
    from cspc import ClaimBoundaryError
    from cspc.provenance import promote
    with pytest.raises(ClaimBoundaryError):
        promote("water-2.45", "SOURCE_CLAIM", "ANALYTIC_MODEL")


def test_attack_findings_doc_makes_no_physical_claim():
    """Attack: does the prose overclaim where the code does not?"""
    text = (DOCS / "CSCP_FINDINGS.md").read_text(encoding="utf-8")
    low = text.lower()
    assert "physical_untested" in low or "physically untested" in low
    for banned in ("proves that", "demonstrates coupling",
                   "confirms the hypothesis", "we measured"):
        assert banned not in low, f"findings doc contains {banned!r}"


def test_attack_findings_doc_reports_the_null_results():
    """A findings document that only reports flattering results is a
    failure mode. The nulls must be present."""
    text = (DOCS / "CSCP_FINDINGS.md").read_text(
        encoding="utf-8").lower()
    for required in ("circular", "null result", "unsupported",
                     "not detected", "human convention"):
        assert required in text, required


def test_attack_no_restricted_result_word_used_affirmatively():
    """'portal'/'warp' must not appear; 'travel' only with refusal."""
    import cspc
    text = (DOCS / "CSCP_FINDINGS.md").read_text(
        encoding="utf-8").lower()
    for word in ("portal", "warp"):
        assert word not in text
    if "travel" in text:
        assert "unsupported" in text
    assert "travel" in " ".join(cspc.RESTRICTED_RESULT_WORDS)


def test_attack_circularity_is_disclosed_not_buried():
    """Attack: is the programme's own corpus presented as a discovery?"""
    from cspc.corpus import analyse, cspc_candidates
    r = analyse("CSPC_CANDIDATES", cspc_candidates(),
                Fraction(2450000000), "SRC_2_45_GHZ", n_null=50)
    assert r.circularity_warning and "CIRCULAR" in r.circularity_warning


def test_attack_safety_gate_cannot_be_bypassed():
    from cspc.rf_safety import RFPlan, SafetyRefusal, require_approved
    with pytest.raises(SafetyRefusal):
        require_approved(RFPlan(
            id="ATTACK", frequency_hz=Fraction(2_450_000_000),
            enclosure="OPEN", output="ANTENNA",
            max_power_w=Fraction(100), isolated_supply=True))


def test_attack_energy_audit_cannot_be_made_favourable():
    """Attack: scale the apparatus up absurdly — is it ever close?"""
    from cspc.spacetime import energy_audit
    a = energy_audit(1e6, 3.15e7)          # a megawatt for a year
    assert a["verdict"] == "NEGLIGIBLE"
    assert a["ratio_to_proton_radius"] < 1e-10


def test_attack_metric_fingerprint_would_catch_a_tuned_metric():
    from cspc.nulls import metric_fingerprint
    assert metric_fingerprint() == \
        "e2456bca5110ed845dbd84ca25868df8c8d40c860105eec51e6f9fb6b92280b6"


# --- programme ledger integrity -----------------------------------------

def test_ledger_records_every_defect_found():
    text = (DOCS / "PROGRAMME_LEDGER.md").read_text(encoding="utf-8")
    for did in ("CSPC-D-001", "CSPC-D-002", "CSPC-D-003",
                "CSPC-D-004"):
        assert did in text


def test_baseline_and_findings_agree_that_physical_is_untested():
    b = json.loads((DOCS / "BASELINE_V4_6.json").read_text(
        encoding="utf-8"))
    assert b["physical_status"] == "UNTESTED"
    text = (DOCS / "CSCP_FINDINGS.md").read_text(encoding="utf-8")
    assert "PHYSICAL_UNTESTED" in text
