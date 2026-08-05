"""R10.59 -- the documentation set, the certificates, and the path map.

The path tests are the ones that matter most here. They separate two
questions that are easy to conflate:

  * is the PATH between two points correct?   -- decidable, and decided
  * are the POINTS the right places?          -- open, V1-B01/B02

Every assertion below is on the first question. The second is asserted
only in the negative: no artifact may claim a located target.
"""

import json
import math
import os
import re

import pytest

from r1053 import certificate, kernel, ledger, lock, pathmap, projector

DOCS = ("docs/EARTH_ROOT_V1.md",
        "docs/VARIABLE_LENGTH_CODEC.md",
        "docs/15KM_CELL_FIELD_ENVELOPE_MODEL.md",
        "docs/FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md",
        "docs/OA_CONVERGENCE_LEDGER.md",
        "docs/USER_MANUAL.md",
        "manuscripts/RGCS_Earth_Root_V1_Manuscript.md")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ------------------------------------------------------------- docs

def test_every_required_document_exists_and_is_substantial():
    for rel in DOCS + ("README.md", "CHANGELOG.md"):
        text = _read(rel)
        assert len(text) > 1200, f"{rel} is too short to be the real thing"


def test_claim_boundary_is_verbatim_where_it_appears():
    """The exact public phrasing, not a paraphrase."""
    required = certificate.CLAIM_BOUNDARY
    for rel in ("README.md", "docs/USER_MANUAL.md",
                "docs/EARTH_ROOT_V1.md",
                "manuscripts/RGCS_Earth_Root_V1_Manuscript.md"):
        flat = " ".join(_read(rel).split())
        assert " ".join(required.split()) in flat, rel


def _negation_context(lines, idx):
    """Is line ``idx`` inside a block that is explicitly disowning it?

    A banned phrase is fine when it is being forbidden. That can happen
    on the line itself ("OA is not disclosure"), or -- the common case --
    inside a fenced block introduced by "Do not use:". So walk back to
    the fence opener and check the prose immediately above it.
    """
    if re.search(r"\bnot\b|\bnever\b", lines[idx], re.I):
        return True
    fence = None
    for j in range(idx, -1, -1):
        if lines[j].lstrip().startswith("```"):
            fence = j
            break
    if fence is None:
        return False
    lead = " ".join(lines[max(0, fence - 3):fence])
    return bool(re.search(r"\bnot\b|\bnever\b|\bbanned\b", lead, re.I))


def test_no_document_claims_proof():
    """No document may assert proof except to disown the assertion."""
    banned = (r"\bproves that RGCS\b", r"\bis proven\b(?!,)",
              r"\bOA proves\b", r"\bOA is disclosure\b",
              r"\bOA validates\b")
    for rel in DOCS + ("README.md",):
        text = _read(rel)
        lines = text.splitlines()
        for pat in banned:
            for m in re.finditer(pat, text, re.I):
                idx = text[:m.start()].count(chr(10))
                assert _negation_context(lines, idx), \
                    f"{rel}:{idx + 1} asserts proof: {lines[idx].strip()!r}"


def test_the_proof_guard_actually_catches_a_bare_assertion():
    """Positive control: the guard must fail on an undisowned claim."""
    assert not _negation_context(["OA proves RGCS."], 0)
    assert _negation_context(["Do not use:", "```text", "OA proves RGCS."], 2)
    assert _negation_context(["OA does not prove RGCS."], 0)


def test_all_seven_blockers_appear_in_readme_and_manual():
    for rel in ("README.md", "docs/USER_MANUAL.md"):
        text = _read(rel)
        for n in range(1, 8):
            assert f"B0{n}" in text, f"{rel} is missing B0{n}"


def test_archive_exists_with_correction_banner():
    d = os.path.join(ROOT, "docs", "archive", "pre-r1059")
    assert os.path.isdir(d)
    files = [f for f in os.listdir(d) if f.endswith(".md")]
    assert files, "nothing archived"
    banner = _read("docs/archive/pre-r1059/README.md")
    assert "archived" in banner.lower()
    assert "R10.59" in banner


def test_codec_spec_path7_decompositions_are_exact():
    """Every PATH7 row in the codec spec is arithmetic, not assertion."""
    expected = {
        "165876523": ("170", "6114", "1706114"),
        "165892743": ("170", "6512", "1706512"),
        "165892763": ("170", "6512", "1706512"),
        "165892783": ("170", "6512", "1706512"),
        "167849523": ("200", "2270", "2002270"),
        "168930443": ("204", "3262", "2043262"),
    }
    spec = _read("docs/VARIABLE_LENGTH_CODEC.md")
    for word, (s8o, p12o, path7) in expected.items():
        v = int(word)
        assert (v >> 26) & 15 == 2                      # R4
        assert format((v >> 18) & 255, "03o") == s8o
        assert format((v >> 6) & 4095, "04o") == p12o
        assert s8o + p12o == path7
        assert path7 in spec, f"{path7} missing from the codec spec"


def test_depth_table_in_the_15km_doc_matches_the_code():
    doc = _read("docs/15KM_CELL_FIELD_ENVELOPE_MODEL.md")
    for depth, edge in ((9, 14.989), (10, 7.495), (11, 3.747)):
        assert kernel.cell_edge_km(depth) == pytest.approx(edge, abs=0.001)
        assert f"{edge}" in doc


def test_the_null_is_stated_wherever_the_cell_scale_claim_is():
    """A cell-scale claim without its null is the failure mode."""
    for rel in ("docs/15KM_CELL_FIELD_ENVELOPE_MODEL.md",
                "manuscripts/RGCS_Earth_Root_V1_Manuscript.md"):
        text = _read(rel)
        assert "1.046" in text
        assert "0.881" in text, f"{rel} quotes the hit without the null"
        assert "0.147" in text


# ------------------------------------------------------ certificates

def test_certificate_carries_frame_epoch_claim_and_blockers():
    c = certificate.address_certificate(165879243)
    assert c["frame"]["frame"]["frame_id"] == "RGCS_EARTH_ROOT_D_V1"
    assert c["frame"]["frame"]["display_convention"] == "SOUTH_UP"
    assert c["frame"]["epoch"]["structural_decode"] == "EPOCH_OPTIONAL"
    assert c["frame"]["epoch"]["dynamic_projection"] == "EPOCH_REQUIRED"
    assert c["frame"]["epoch"]["long_origin_candidate"] == "Ba-130"
    assert c["projection"]["is_located_target"] is False
    assert "CANDIDATE_NOT_LOCATED_TARGET" in c["claim_class"]
    assert {"V1-B01", "V1-B02", "V1-B03"} <= set(c["blockers"])
    assert c["not_final_physical_validation"] is True


def test_certificate_records_the_pinning_gap_not_just_one_number():
    c = certificate.address_certificate(165879243)
    assert c["projection"]["pinning_gap_km"] > 5000.0
    assert "operator_supplied_lat" in c["projection"]
    assert "v1_pinned_lat" in c["projection"]


def test_anchor_certificate_says_its_residual_is_not_evidence():
    c = certificate.address_certificate(165876523)
    assert c["projection"]["residual_is_evidence"] is False
    assert "TRAINING_EQUALITY" in c["claim_class"]


def test_envelope_rejection_never_truncates():
    for rec in ledger.GATED_WIDE_ENVELOPE:
        r = certificate.envelope_rejection(rec)
        assert r["admitted"] is False and r["never_truncated"] is True
        assert r["bits"] > kernel.WORD_BITS
        assert r["blocker"] == "V1-B07"


def test_receipt_bundle_round_trips_as_json():
    b = certificate.receipt_bundle()
    assert json.loads(json.dumps(b))["schema"] == \
        "rgcs.r1059.receipt-bundle.v1"
    assert len(b["certificates"]) == 7
    assert len(b["envelope_rejections"]) == 7
    assert set(b["verdicts"]) == set(lock.VERDICTS)


# ------------------------------------------------------- the path map

def test_three_independent_distance_formulas_agree():
    """Haversine, law of cosines, and Vincenty-on-a-sphere."""
    for a, b, c, d in ((42.1292, -80.0851, 43.6532, -79.3832),
                       (51.1789, -1.8262, 43.6532, -79.3832),
                       (50.8494, -0.9022, 45.8419, -72.6788),
                       (0.0, 0.0, 0.0, 90.0)):
        cc = pathmap.cross_check(a, b, c, d)
        assert cc["agree"], cc
        assert cc["max_disagreement_km"] < 1e-6


def test_quarter_circumference_is_exact():
    """A 90-degree separation must be exactly a quarter great circle."""
    cc = pathmap.cross_check(0.0, 0.0, 0.0, 90.0)
    assert cc["haversine_km"] == pytest.approx(
        math.pi * projector.EARTH_RADIUS_KM / 2, rel=1e-12)


def test_path_distances_match_the_recorded_pack_values():
    """The map's numbers are the pack's numbers."""
    r = pathmap.path_between(167849523, 168930443)
    assert r["distance_km"] == pytest.approx(178.847, abs=0.01)
    D = ledger.V1_PROJECTED["165879243"]
    r2 = pathmap.path_between(168930443, "165879243",
                              lat_lon_b=(D["lat"], D["lon"]))
    assert r2["distance_km"] == pytest.approx(582.465, abs=0.01)


def test_polyline_is_a_real_great_circle_not_a_lat_lon_lerp():
    """A straight line in lat/lon space would be visibly wrong."""
    r = pathmap.path_between(165876523, 168930443)
    A, B = r["endpoints"]
    mid = r["polyline"][len(r["polyline"]) // 2]
    naive = ((A["lat"] + B["lat"]) / 2, (A["lon"] + B["lon"]) / 2)
    # over 5600 km the two differ by hundreds of km
    assert projector.haversine_km(*mid, *naive) > 100.0
    # and the sampled midpoint is equidistant from both ends
    da = projector.haversine_km(A["lat"], A["lon"], *mid)
    db = projector.haversine_km(B["lat"], B["lon"], *mid)
    assert da == pytest.approx(db, rel=1e-6)


def test_polyline_endpoints_are_the_endpoints():
    r = pathmap.path_between(167849523, 168930443)
    A, B = r["endpoints"]
    assert r["polyline"][0] == pytest.approx([A["lat"], A["lon"]], abs=1e-9)
    assert r["polyline"][-1] == pytest.approx([B["lat"], B["lon"]], abs=1e-9)


def test_polyline_segments_sum_to_the_reported_distance():
    """Sampling density must not change the measured length."""
    r = pathmap.path_between(165876523, 168930443)
    pts = r["polyline"]
    total = sum(projector.haversine_km(*pts[i], *pts[i + 1])
                for i in range(len(pts) - 1))
    assert total == pytest.approx(r["distance_km"], rel=1e-6)


def test_bearing_is_correct_for_a_due_east_path():
    r = pathmap.cross_check(0.0, 0.0, 0.0, 10.0)
    assert r["agree"]
    assert projector.bearing_deg(0.0, 0.0, 0.0, 10.0) == pytest.approx(90.0)
    assert projector.bearing_deg(0.0, 0.0, 10.0, 0.0) == pytest.approx(0.0)


def test_path_reports_endpoint_source_and_never_claims_a_place():
    D = ledger.V1_PROJECTED["165879243"]
    r = pathmap.path_between(168930443, "165879243",
                             lat_lon_b=(D["lat"], D["lon"]))
    A, B = r["endpoints"]
    assert A["coordinate_source"] == "FIT_ANCHOR_TARGET"
    assert B["coordinate_source"] == "OPERATOR_SUPPLIED"
    assert A["is_located_target"] is False
    assert B["is_located_target"] is False
    assert r["path_is_verified_geometry"] is True
    assert r["endpoints_are_verified_places"] is False


def test_the_b01_disagreement_is_renderable_as_one_path():
    """The same vector at two admissible pinnings, 5122 km apart."""
    D = ledger.V1_PROJECTED["165879243"]
    r = pathmap.path_between("165879243", "165879243",
                             lat_lon_b=(D["lat"], D["lon"]))
    assert r["distance_km"] == pytest.approx(5121.7, abs=1.0)
    A, B = r["endpoints"]
    assert A["vector"] == B["vector"] == "165879243"
    assert A["octal10"] == B["octal10"]        # identical wire
    assert A["branch_octal"] == B["branch_octal"] == "117"


def test_path_map_html_is_self_contained_for_the_library(tmp_path):
    r = pathmap.path_between(167849523, 168930443)
    out = tmp_path / "p.html"
    pathmap.render_html(r, str(out))
    html = out.read_text("utf-8")
    assert "unpkg.com" not in html and "cdn." not in html
    assert 'src="vendor/leaflet.js"' in html
    assert "NOT final physical validation" in html or \
        "underdetermined" in html
    assert "L.polyline" in html
    assert f"{r['distance_km']:.3f}"[:6] in html or "distance_km" in html


def test_path_map_warns_when_tiles_fail_rather_than_showing_blank(tmp_path):
    r = pathmap.path_between(167849523, 168930443)
    out = tmp_path / "p.html"
    pathmap.render_html(r, str(out))
    html = out.read_text("utf-8")
    assert "tileload" in html and "warn" in html


def test_vendored_leaflet_is_present():
    # internal-docs moved to the private RGCS-private repository and
    # resolves here only through a local symlink on the dev machine.
    # A fresh public clone has no internal-docs at all, so absence is
    # an expected environment, not a defect.
    vd = os.path.join(ROOT, "internal-docs", "RGCS_R10_53_V1_EARTH_ROOT",
                      "maps", "vendor")
    if not os.path.isdir(vd):
        pytest.skip("private pack not present (internal-docs lives in "
                    "RGCS-private; local symlink only, expected on CI)")
    for f in pathmap.VENDOR_FILES:
        p = os.path.join(vd, f)
        assert os.path.exists(p) and os.path.getsize(p) > 10000, f


def test_cli_rejects_a_gated_record_with_exit_2(capsys):
    from r1053.__main__ import main
    assert main(["path", "1687293589323", "165876523"]) == 2
    err = capsys.readouterr().err
    assert "41 bits" in err and "V1-B07" in err
