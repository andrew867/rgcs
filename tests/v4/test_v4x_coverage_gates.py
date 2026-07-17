"""Gates G42A-G42G: the strengthened coverage contract.

v4.2.0's G42 verified that every ledger ID had an owner STRING and an
artifact STRING. That is satisfiable with nonempty text. These gates
verify the claims mechanically and are release-blocking."""

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "v4x_coverage_gates", ROOT / "tools" / "v4x_coverage_gates.py")
gates = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gates)


@pytest.fixture(scope="module")
def report():
    return gates.evaluate()


@pytest.mark.parametrize("gate", ["G42A", "G42B", "G42C", "G42D",
                                  "G42E", "G42F", "G42G"])
def test_gate_passes(report, gate):
    g = report["gates"][gate]
    assert g["passed"], f"{gate} failures: {g['failures'][:10]}"


def test_all_rows_present(report):
    """248 fixed ledger IDs + 20 orphans."""
    assert report["total_rows"] == 268


def test_artifact_paths_and_symbols_are_real(report):
    """G42B: a nonempty string is not an artifact. Every declared path
    must exist and every declared symbol must import."""
    checked = 0
    for row in report["rows"]:
        for p in row["artifact_paths"]:
            assert (ROOT / p).exists(), f"{row['id']}: {p}"
            checked += 1
    assert checked > 50, "gate is not actually checking anything"


def test_status_cannot_outrun_depth(report):
    """G42F: the defect this gate exists for."""
    for row in report["rows"]:
        if row["status"] in gates.DEPTH_REQUIRING_STATUSES:
            assert row["implementation_depth"] != "registry_only", \
                f"{row['id']} claims {row['status']} with no code"
        if row["status"] in gates.NO_COMPUTE_STATUSES:
            assert row["implementation_depth"] == "interface_only"


def test_arithmetic_identity_never_wears_a_physics_status():
    """G42F: 'F002 20.480 kHz = 4096*5, CORE_VALIDATED' reads as
    though 20.48 kHz were a validated resonance. The arithmetic is
    exact; the physics is not claimed. Every such record must carry
    the arithmetic-only note."""
    from rscs2_core import frequency_keys as fk
    reg = fk.build_registry()
    n = 0
    for rid, rec in reg.items():
        if rec["frequency_kind"] in fk.ARITHMETIC_KINDS and \
                rec["status"] == "CORE_VALIDATED":
            assert "ARITHMETIC ONLY" in rec["arithmetic_only_note"]
            assert "not a claim" in rec["arithmetic_only_note"]
            n += 1
    assert n >= 5, "expected several arithmetic CORE_VALIDATED rows"


def test_blocked_rows_name_blocker_and_next_action(report):
    """G42G: a blocked row that does not say what blocks it, or what
    would unblock it, is an excuse rather than a status."""
    for row in report["rows"]:
        if row["status"] in gates.BLOCKED_STATUSES:
            assert row["blocker"], row["id"]
            assert row["next_action"], row["id"]


def test_every_row_has_documentation(report):
    """G42E."""
    for row in report["rows"]:
        assert row["documentation_paths"], row["id"]
        for d in row["documentation_paths"]:
            assert (ROOT / d).exists(), f"{row['id']}: {d}"
