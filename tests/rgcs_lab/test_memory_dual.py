from rgcs_lab.dual_pole import audit_claim, audit_file
from rgcs_lab.memory import run_benchmark


def test_memory_benchmark_is_deterministic():
    a = run_benchmark("examples/rgcs_lab/memory", top_k=2)
    b = run_benchmark("examples/rgcs_lab/memory", top_k=2)
    assert a["result"]["rankings"] == b["result"]["rankings"]
    assert a["result"]["metrics"]["complete_proposed_system"]["stale_memory_avoidance"]


def test_dual_pole_blocks_forbidden_energy_claim():
    claim = {"proposal": "resonance gain proves excess energy",
             "claim_class": ["SOURCE_CLAIM"], "evidence": [{"id": "x"}]}
    result = audit_claim(claim)
    assert result["verdict"] == "BLOCK"


def test_dual_pole_accepts_bounded_yellow_example():
    rec = audit_file("examples/rgcs_lab/claim_yellow.json")
    assert rec["status"] == "YELLOW"
    assert rec["result"]["verdict"] == "ACCEPT_YELLOW"
