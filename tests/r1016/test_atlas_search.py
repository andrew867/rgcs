"""R10.16 — no-warp atlas search tests."""

import math

import numpy as np
import pytest

from r1016.project import (STRICT_ANCHORS, STRICT_GATE_RMS_KM,
                           RootVariant, enumerate_variants,
                           great_circle_km, project, reverse_bits30)
from r1016.views import MASK30, VIEW_IDS, candidates, split


def test_wire_split():
    assert split("165876523") == ("16", "587652", "3")
    with pytest.raises(Exception):
        split("99912345")


def test_all_declared_views_are_enumerated():
    cs = candidates("165876523")
    assert {c["view"] for c in cs} >= set(VIEW_IDS) - {
        "D_WINDOW_FULL_30", "E_WINDOW_PAYLOAD_30"}


def test_octal_digit_views_refuse_on_8_or_9():
    """Exact structural fact: a digit 8 or 9 has no octal reading."""
    cs = {c["view"]: c for c in candidates("165876523")
          if c.get("window") is None}
    for v in ("A_PAYLOAD_OCTAL_DIGITS", "B_FULL_WIRE_OCTAL_DIGITS"):
        assert cs[v]["word"] is None
        assert "8 or 9" in cs[v]["refusal"]


def test_integer_views_are_always_defined_when_in_range():
    cs = {c["view"]: c for c in candidates("165876523")
          if c.get("window") is None}
    assert cs["A2_PAYLOAD_INT"]["word"] == 587652
    assert cs["B2_FULL_WIRE_INT"]["word"] == 165876523


def test_words_never_exceed_30_bits():
    for wire in list(STRICT_ANCHORS) + ["1687425389431"]:
        for c in candidates(wire):
            if c.get("word") is not None:
                assert 0 <= c["word"] <= MASK30


def test_short_wires_have_no_30_bit_window():
    """The anchors are 28-bit, so views D/E cannot be gated at all."""
    for wire in STRICT_ANCHORS:
        assert int(wire).bit_length() < 30
        ds = [c for c in candidates(wire)
              if c["view"] == "D_WINDOW_FULL_30"]
        assert all(c["word"] is None for c in ds)


def test_bit_reversal_is_an_involution():
    for w in (165876523, 1, MASK30, 587652):
        assert reverse_bits30(reverse_bits30(w)) == w


def test_variant_enumeration_is_the_declared_discrete_space():
    v = enumerate_variants(("TRAINED",))
    assert len(v) == 20 * 2 * 2 * 2 * 2
    assert len({x.id for x in v}) == len(v)


def test_projector_reproduces_training_anchor():
    """Identity variant on the training word must land on Stonehenge."""
    from cwatlas.r1085a import final_projection as fp
    frame, _ = fp.training_alignment(2025.0)
    r = project(165876523, RootVariant(),
                np.asarray(frame.rotation, float))
    d = great_circle_km(r["lat"], r["lon"], fp.TRAINING_LAT_DEG,
                        fp.TRAINING_LON_DEG)
    assert d < 0.5, "the projector must reproduce the frozen root"


def test_great_circle_sanity():
    assert abs(great_circle_km(0, 0, 0, 1) - 111.19) < 0.5
    assert great_circle_km(51.1789, -1.8262, 51.1789, -1.8262) == 0.0


def test_strict_gate_fails_for_every_discrete_variant():
    """THE result: no no-warp discrete model reproduces the anchors."""
    from r1016.search import run
    res = run(contexts=("ALL_SEALED",))
    assert res["models_evaluated"] > 5000
    assert res["models_with_full_anchor_coverage"] > 1000
    assert res["survivor_count"] == 0
    assert res["verdict"] == \
        "STRICT_ANCHOR_GATE_FAILED_ALL_DISCRETE_VARIANTS"
    assert res["best"]["rms_km"] > 10 * STRICT_GATE_RMS_KM


def test_rigid_rotation_salvage_also_fails():
    """The optimal rotation is the most generous no-warp freedom."""
    from r1016.salvage import salvage_all
    from r1016.search import view_word_maps
    sal = salvage_all(view_word_maps(list(STRICT_ANCHORS)))
    assert not sal["any_passes_25km"]
    assert sal["merged_into_main_atlas"] is False
    assert sal["best"]["rms_km"] > STRICT_GATE_RMS_KM
    assert "DECODE" in sal["best"]["interpretation"].upper()


def test_pairwise_angles_are_rotation_invariant_and_mismatched():
    """Rotation-invariant proof that no orientation can align them."""
    import itertools

    from r1016.salvage import _unit, mesh_direction
    from r1016.search import view_word_maps
    m = {x["view"]: x for x in
         view_word_maps(list(STRICT_ANCHORS))}["A2_PAYLOAD_INT"]
    v = RootVariant()
    md, td = [], []
    for wire, (_p, lat, lon) in STRICT_ANCHORS.items():
        md.append(mesh_direction(m["words"][wire], v))
        td.append(_unit(lat, lon))

    def ang(a, b):
        return math.degrees(math.acos(
            min(1.0, max(-1.0, float(np.dot(a, b))))))

    pairs = tuple(itertools.combinations(range(len(md)), 2))
    assert len(md) == len(td) == len(STRICT_ANCHORS) >= 3
    diffs = [abs(ang(md[i], md[j]) - ang(td[i], td[j]))
             for i, j in pairs]
    # decoded set is a tight cluster; claimed set is spread out
    assert max(ang(md[i], md[j]) for i, j in pairs) < 6.0
    assert max(ang(td[i], td[j]) for i, j in pairs) > 45.0
    assert max(diffs) > 40.0, "mismatch must be rotation-invariant"


def test_no_private_wire_is_embedded_in_r1016_source():
    """r1016 reads path vectors at runtime; it never stores them."""
    import pathlib

    from rgcs_surface_wave.privacy import (WIRE_SIGNATURE,
                                           public_wire_allowlist)
    allow = public_wire_allowlist()
    root = pathlib.Path(__file__).resolve().parents[2] / "r1016"
    for f in root.rglob("*.py"):
        for m in WIRE_SIGNATURE.finditer(
                f.read_text(encoding="utf-8")):
            assert m.group(0) in allow, (f.name, "unknown wire in source")


def test_path_vectors_require_explicit_authorization():
    import os

    from r1016.inventory import private_wires
    saved = os.environ.pop("RGCS_R1016_PATH_VECTORS", None)
    try:
        assert private_wires(enable=True) == {}
        assert private_wires(enable=False) == {}
    finally:
        if saved is not None:
            os.environ["RGCS_R1016_PATH_VECTORS"] = saved


def test_confidence_classes_cannot_reach_a_b_c_without_a_gate():
    from r1016.atlas import CONFIDENCE, build_rows
    from r1016.search import run
    from cwatlas.r1085a import final_projection as fp
    res = run(contexts=("TRAINED",))
    frame, _ = fp.training_alignment(2025.0)
    rows = build_rows(False, res["best"],
                      np.asarray(frame.rotation, float),
                      include_private=False)
    classes = {r["confidence_class"] for r in rows}
    assert not (classes & {"A", "B", "C"}), \
        "no row may claim a calibrated class when the gate failed"
    assert classes <= set(CONFIDENCE)
