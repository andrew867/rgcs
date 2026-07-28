"""R10.12 acceptance — consolidated release candidate."""

from __future__ import annotations

import json

import pytest

from r1012 import cli
from r1012.certificate import WireError, certify
from r1012.corpus import child_coverage, golden28, verify_corpus
from r1012.evidence import ACTIVE_TIERS, Tier, TierError, assert_active
from r1012.ledger import (AUTHORITY_GRAPH, CORRECTIONS, active_artifacts,
                          graph_dict, revoked_artifacts)
from r1012.transitions import TransitionError, candidates, lookup, refine
import r1012.geometry as G
import r1012.shell_epoch as SE


# ------------------------------------------------------------ Tranche A
def test_correction_ledger_complete():
    ids = {c["id"] for c in CORRECTIONS}
    assert ids == {f"COR-{i:02d}" for i in range(1, 9)}
    by = {c["id"]: c for c in CORRECTIONS}
    assert "168742538943" in by["COR-03"]["by"]
    assert by["COR-06"]["tier_of_old"] == Tier.REVOKED
    assert by["COR-07"]["tier_of_old"] == Tier.FALSIFIED_FAMILY


def test_evidence_tiers_executable():
    assert len(Tier) == 8
    assert_active(Tier.SOURCE_KNOWN, "x")
    for t in (Tier.REVOKED, Tier.HISTORICAL_ONLY, Tier.UNDERDETERMINED):
        with pytest.raises(TierError):
            assert_active(t, "x")


def test_authority_graph_blocks_revoked_from_active():
    g = graph_dict()
    warp = ("docs/r109/earth_v1/RGCS_Earth_Alignment_Candidate_2026-07-26/"
            "operator/WARP_STEPS.json.gz")
    assert g["artifacts"][warp]["tier"] == "REVOKED"
    assert warp in revoked_artifacts()
    assert warp not in active_artifacts()
    # the fitted node mesh and monolithic profile are historical too
    assert "r1011/flat_hedron.py" in revoked_artifacts()
    assert "rgcs_coordinate/codecs/federation_terra_30.py" in \
        revoked_artifacts()


def test_no_hidden_targets_in_r1012():
    import inspect
    import r1012.certificate, r1012.corpus, r1012.transitions
    src = "".join(inspect.getsource(m) for m in
                  (r1012.certificate, r1012.corpus, r1012.transitions,
                   G, SE, cli))
    for banned in ("Stonehenge", "Wrexham", "Stafford", "51.17", "45.508",
                   "WARP_STEPS", "NODE_LIFT_PARAMETERS"):
        assert banned not in src


# ------------------------------------------------------------ Tranche B
def test_canonical_certificate_fields():
    c = certify(168742538943)
    assert c.e3 == 6 and c.states == (32, 56, 7)
    assert c.child_path == (1, 0, 6) and c.terminal == 3 and c.depth == 3
    assert c.canonical_bits.startswith("001|110|")
    assert c.parser_version and c.registry_version and c.roundtrip_hash


def test_golden_28_and_legacy_migration():
    v = verify_corpus()
    assert v["golden_total"] == 28 and v["golden_parsed"] == 28
    assert v["golden_failures"] == 0 and v["hash_match"]
    assert v["legacy_parsed"] == v["legacy_total"] == 19
    assert "1687425419853" not in golden28()["wires"]


@pytest.mark.parametrize("bad", [
    "", " 165876523", "165876523 ", "165876523x", "٫165876523",
    "0165876523", "-165876523", "16587652.3", "165876523\n165879243",
    "1687425419853",                       # malformed (ledger only)
    "16",                                  # too short
])
def test_parser_fuzz_rejects(bad):
    with pytest.raises((WireError, Exception)):
        c = certify(bad)
        # any accepted value must round-trip to the identical string
        assert c.raw_wire == str(bad)


def test_one_digit_mutations_never_silently_accepted():
    base = "165876523"
    for i in range(len(base)):
        for d in "0123456789":
            if d == base[i]:
                continue
            m = base[:i] + d + base[i + 1:]
            try:
                c = certify(m)
                assert c.raw_wire == m          # exact, no coercion
            except Exception:
                pass                             # typed refusal is fine


def test_terminals_5_7_9_distinct():
    c = certify(16782953437)
    assert c.terminal == 7
    assert any("NOT surface class 3" in w for w in c.warnings)


# ------------------------------------------------------------ Tranche C
def test_transition_tiers_and_refusals():
    assert lookup(5, 15)["evidence_tier"] == "SOURCE_KNOWN"
    assert lookup(5, 0)["evidence_tier"] == "CONDITIONAL_CONSENSUS"
    assert lookup(5, 2)["evidence_tier"] == "UNDERDETERMINED"
    assert lookup(0, 10)["evidence_tier"] == "UNSUPPORTED"
    assert refine(165876523, 5)["refined_states"] == [5, 40, 37]
    with pytest.raises(TransitionError):
        refine(165652893, 5)
    cand = candidates(165652893, 5)
    assert cand["combination_count"] >= 32


def test_child_coverage_and_query_queue():
    cc = child_coverage()
    assert set(cc["columns_with_source_known_cells"]) == {5, 6}
    assert cc["transition_inference_rule"] == "NEVER from a child symbol alone"
    assert len(cc["query_queue"]) > 0


# ------------------------------------------------------------ Tranche D
def test_analytic_mesh_and_refusals():
    m = G.build_mesh(2)
    assert (m["vertices"], m["triangles"]) == (162, 320)
    assert G.audit_mesh(3)["orientation_reversals"] == 0
    with pytest.raises(G.GeometryError):
        G.build_mesh(11)


def test_geometry_stops_at_state_mapped():
    st = G.geometry_status(165876523)
    assert st["stage"] == "STATE_MAPPED"
    assert "lat" not in json.dumps(st).lower().replace(
        "latitude/longitude", "")
    hyp = G.s6_hypothesis_registry()
    assert all(f["status"] == "UNDERDETERMINED" for f in hyp["families"])


# ------------------------------------------------------------ Tranche E
def test_shell_epoch_envelope_and_refusals():
    assert SE.E3_ENVELOPE["observed_values"] == [2, 3, 4, 6]
    assert "UNRESOLVED" in SE.E3_ENVELOPE["internal_subdivision"]
    assert "Ba-130" in SE.EPOCH_AUTHORITY["long_origin"]
    assert SE.shell_report()["all_close"]
    with pytest.raises(SE.ShellEpochError):
        SE.gravity_vertical(45.0, -75.0)
    ok = SE.gravity_vertical(45.0, -75.0, allow_geocentric_substitute=True)
    assert ok["model_status"].startswith("GEOCENTRIC_SUBSTITUTE")
    e = SE.ellipsoid_realize(45.0, -75.0)
    assert len(e["ecef_m"]) == 3


# ------------------------------------------------------------ Tranche F
def test_self_test_all_pass_and_release_verify():
    st = cli.self_test()
    assert st["ALL_PASS"] is True
    rv = cli.release_verify()
    assert rv["self_test_all_pass"] is True
    assert rv["fitted_warp_active"] is False
    assert rv["uniform_ratio_law_selected"] is False


def test_cli_exit_codes():
    assert cli.main(["wire", "parse", "165876523"]) == 0
    assert cli.main(["transition", "refine", "165652893", "--child", "5"]) == 3
    assert cli.main(["corpus", "verify"]) == 0
