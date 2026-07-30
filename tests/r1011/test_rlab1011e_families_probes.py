"""R10.11E acceptance — reconstruction, families, probes, intake."""

from __future__ import annotations

import json
import pathlib

import pytest

from r1011 import e3_frame as e3
from r1011 import gf2_affine as gf
from r1011 import probe_intake as pi
from r1011.segmented_codec import T_SPARSE

EV = pathlib.Path(__file__).resolve().parents[2] / "docs" / "r1011" / "evidence"


@pytest.fixture(scope="module")
def comps():
    return gf.reconstruct(5), gf.reconstruct(6)


def test_independent_reconstruction_counts_and_knowns(comps):
    c5, c6 = comps
    assert len(c5) == 32 and len(c6) == 32
    for child, cs in ((5, c5), (6, c6)):
        for c in cs:
            assert len(set(c["table"])) == 64          # permutation
            assert gf.mat_invertible(c["A_rows"])
            for (s, ch), out in T_SPARSE.items():
                if ch == child:
                    assert c["table"][s] == out        # never overwritten


def test_semantic_match_with_imported_artifacts(comps):
    c5, c6 = comps
    for child, cs, fname in ((5, c5, "AFFINE_CHILD_5_32_COMPLETIONS.json"),
                             (6, c6, "AFFINE_CHILD_6_32_COMPLETIONS.json")):
        d = json.loads((EV / "r1011d" / fname).read_text(encoding="utf-8"))
        key = next(k for k in d if isinstance(d[k], list) and len(d[k]) == 32)
        imported = set()
        for it in d[key]:
            tb = it.get("full_table") or it.get("table") or it.get("outputs")
            imported.add(tuple(tb))
        assert {c["table"] for c in cs} == imported


def test_prior_result_replication(comps):
    c5, c6 = comps
    assert gf.shared_linear_core()["shared_matrix_count"] == 0
    rd = gf.rank_distribution(c5, c6)
    assert rd["min_rank"] == 4
    assert rd["rank_of_A5_xor_A6_distribution"] == {4: 64, 5: 576, 6: 384}


def test_basis_invariance(comps):
    assert gf.basis_invariance_check(5)["bit_reversed_completion_count"] == 32
    assert gf.basis_invariance_check(6)["bit_reversed_completion_count"] == 32


def test_conjugacy_and_delta(comps):
    c5, c6 = comps
    assert gf.conjugacy_search(c5, c6)["hit_count"] == 0
    d = gf.delta_operators(c5, c6)
    assert d["pair_count"] == 1024
    assert d["distinct_cycle_structures"] == 34


def test_equivalence_classes_no_arbitrary_representative(comps):
    c5, c6 = comps
    e5, e6 = gf.equivalence_classes(c5), gf.equivalence_classes(c6)
    assert sum(len(v) for v in e5.values()) == 32
    assert sum(len(v) for v in e6.values()) == 32
    assert len(e5) == 16 and len(e6) == 16


def test_probe_candidate_sets_frozen_and_selective():
    for pid, digest in (("P5", "c71ee3fd80b33d56"), ("P6", "0b684ca5b5f69c4d")):
        cs = json.loads((EV / f"R10_11E_PROBE_{pid}_CANDIDATES.json")
                        .read_text(encoding="utf-8"))
        assert cs["candidate_set_sha256"].startswith(digest)
        assert len(cs["candidates"]) == 32
        assert cs["distinct_wires"] == 32 and cs["wire_collisions"] == 0
        ia = cs["information_accounting"]
        assert ia["new_table_cells_observed"] == 2
        assert ia["new_table_cell_bits"] == 12
        assert ia["affine_completion_index_entropy_bits"] == 5
        # every candidate honors output1 + XOR invariant by construction
        for c in cs["candidates"]:
            s1, s2, s3 = c["refined_states"]
            assert s1 == cs["required_output1"]
            assert (s2 ^ s3) == cs["required_xor23"]
            # every candidate wire parses back to its states
            p = e3.parse(c["candidate_wire"])
            assert p.states == (s1, s2, s3)
            assert p.children == (cs["child"],)


def test_intake_register_then_score_roundtrip(tmp_path, monkeypatch):
    # use a scratch ledger; register a synthetic descendant equal to a
    # known candidate, then score: must select exactly one completion
    monkeypatch.setattr(pi, "LEDGER", tmp_path / "ledger.jsonl")
    cs = json.loads((EV / "R10_11E_PROBE_P5_CANDIDATES.json")
                    .read_text(encoding="utf-8"))
    wire = cs["candidates"][0]["candidate_wire"]
    reg = pi.register("P5", wire, "synthetic test descendant", "2026-07-28T00:00")
    out = pi.score(reg["receipt_id"])
    assert out["verdict"] == "SELECTS_COMPLETIONS"
    assert len(out["matched_completion_ids"]) == 1
    assert out["output1_matches_source_known"] and out["xor_invariant_holds"]
    # registration precedes scoring in the append-only ledger
    lines = [json.loads(l) for l in open(pi.LEDGER, encoding="utf-8")]
    assert [l["action"] for l in lines] == ["REGISTER", "SCORE"]


def test_no_lunar_or_geographic_influence():
    import inspect
    src = inspect.getsource(gf) + inspect.getsource(pi)
    for banned in ("lunar", "Ohio", "latitude", "longitude", "gazetteer",
                   "167854923"):
        assert banned not in src
