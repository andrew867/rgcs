"""Program locks — hub registry (WS09) and coordinate bridge (WS01)."""

import json

import pytest

from rgcs_lab.authority import coordinate_status as cs
from rgcs_lab.authority import hub_registry as hub
from rgcs_lab.common.status_schema import MODULES


def test_hub_shows_all_nine_modules_with_nonclaims():
    assert tuple(c.module for c in hub.CARDS) == MODULES
    for c in hub.CARDS:
        assert c.demonstrates and c.does_not_demonstrate
        assert c.inputs and c.outputs
        assert c.owner in ("claude", "codex", "cursor", "mixed")


def test_missing_receipt_means_red_not_executed(tmp_path):
    s = hub.module_status("golay", repo_root=tmp_path)
    assert s.status == "RED"
    assert s.result["state"] == "NOT_EXECUTED"
    idx = hub.hub_index(repo_root=tmp_path)
    assert idx["module_count"] == 9 and idx["green_count"] == 0
    assert idx["headline"].startswith("Recursive infrastructure")


def test_invalid_receipt_is_loud_not_hidden(tmp_path):
    rdir = tmp_path / "docs" / "program" / "receipts"
    rdir.mkdir(parents=True)
    (rdir / "golay.json").write_text('{"module": "golay"}',
                                     encoding="utf-8")
    s = hub.module_status("golay", repo_root=tmp_path)
    assert s.status == "RED" and s.result["state"] == "INVALID_RECEIPT"


def test_valid_receipt_surfaces_verbatim(tmp_path):
    rdir = tmp_path / "docs" / "program" / "receipts"
    rdir.mkdir(parents=True)
    receipt = {"module": "golay", "version": "0.1",
               "source_commit": "abc", "status": "GREEN",
               "claim_class": ["EXACT_ARITHMETIC"], "inputs": {},
               "models": [], "result": {"demo": "bit flips corrected"},
               "warnings": ["software demonstration only"],
               "tests": ["tests/x"]}
    (rdir / "golay.json").write_text(json.dumps(receipt),
                                     encoding="utf-8")
    s = hub.module_status("golay", repo_root=tmp_path)
    assert s.status == "GREEN"
    assert s.receipt["source_commit"] == "abc"
    assert hub.hub_index(repo_root=tmp_path)["green_count"] == 1


def test_unknown_module_refused():
    with pytest.raises(KeyError, match="unknown module"):
        hub.card("warpdrive")


def test_coordinate_receipt_built_by_execution():
    receipt = cs.build_coordinate_receipt(source_commit="testcommit")
    assert receipt["status"] == "GREEN"                  # structural lane
    assert receipt["result"]["projection_lane"] == "YELLOW"
    assert receipt["result"]["projection_verdict"] == \
        cs.PROJECTION_VERDICT
    assert "TRAINING_EQUALITY" in receipt["claim_class"]
    assert "UNDERDETERMINED" in receipt["claim_class"]
    assert receipt["result"]["roundtrip_exact"] is True
    # the receipt is valid against the shared contract
    from rgcs_lab.common.status_schema import validate_receipt
    assert validate_receipt(receipt)["valid"]
