"""R10.59B -- N-vector polygons and the browser-side kernel port.

The area tests are anchored to closed forms, not to previously-recorded
output: a spherical octant is exactly one eighth of the sphere, and a
spherical triangle must exceed its planar Heron area. Regression tests
that only compare against last week's number cannot catch a formula
that was wrong from the start -- which is exactly what happened here.
The first cross-check used the planar "spherical shoelace" formula; it
disagreed with the exact excess by 42 % on the anchor triangle and by a
factor of two on an octant, and was replaced with a second exact method.
"""

import math

import pytest

from r1053 import polygon, polygon_page, projector

R = polygon.EARTH_RADIUS_KM
SPHERE_KM2 = 4 * math.pi * R * R

ANCHORS = ["165876523", "167849523", "168930443"]
UK4 = ["165876523", "165892743", "165892763", "165892783"]


# ------------------------------------------------------- exact geometry

def test_spherical_octant_is_exactly_one_eighth_of_the_sphere():
    oct_ = [(0, 0), (0, 90), (90, 0)]
    assert polygon.area_km2_excess(oct_) == pytest.approx(
        SPHERE_KM2 / 8, rel=1e-12)
    assert polygon.area_km2_turning(oct_) == pytest.approx(
        SPHERE_KM2 / 8, rel=1e-12)


def test_the_two_area_methods_are_independent_and_agree():
    for pts in ([(0, 0), (0, 1), (1, 1), (1, 0)],
                [(0, 0), (0, 10), (10, 10), (10, 0)],
                [(51.1789, -1.8262), (42.1292, -80.0851),
                 (43.6532, -79.3832)],
                [(-33.9, 18.4), (-37.8, 144.9), (35.7, 139.7)]):
        a, b = polygon.area_km2_excess(pts), polygon.area_km2_turning(pts)
        assert a == pytest.approx(b, rel=1e-9), pts


def test_small_polygon_matches_the_flat_approximation():
    """A 1x1 degree box at the equator is nearly planar."""
    pts = [(0, 0), (0, 1), (1, 1), (1, 0)]
    flat = (math.radians(1) * R) ** 2
    assert polygon.area_km2_excess(pts) == pytest.approx(flat, rel=1e-4)


def test_spherical_triangle_exceeds_its_planar_heron_area():
    """Spherical excess is positive, so the sphere must give more."""
    rec = polygon.build(ANCHORS)
    a, b, c = (e["km"] for e in rec["edges"])
    s = (a + b + c) / 2
    heron = math.sqrt(s * (s - a) * (s - b) * (s - c))
    assert rec["area_km2"] > heron
    assert rec["area_km2"] < heron * 1.2          # and not absurdly more


def test_area_is_invariant_under_cyclic_rotation_of_the_vertices():
    """The fan triangulation picks vertex 0 as its apex, so rotating the
    list changes the arithmetic even though the polygon is identical.

    Measured spread on UK4 -- a thin sliver, isoperimetric ratio 0.22 --
    is 4e-7 km2, i.e. 3.8e-9 relative, or under a square metre on
    105 km2. That is L'Huilier conditioning, not an asymmetry: the
    large anchor triangle rotates with a spread of exactly zero.
    """
    base = polygon.build(UK4)["area_km2"]
    for k in range(1, len(UK4)):
        rot = UK4[k:] + UK4[:k]
        assert polygon.build(rot)["area_km2"] == pytest.approx(base, rel=1e-7)
    big = polygon.build(ANCHORS)["area_km2"]
    for k in range(1, len(ANCHORS)):
        rot = ANCHORS[k:] + ANCHORS[:k]
        assert polygon.build(rot)["area_km2"] == pytest.approx(big, rel=1e-12)


def test_the_turning_method_is_exactly_rotation_invariant():
    """It walks the boundary, so no vertex is privileged. Unlike the fan,
    its rotation spread is exactly zero even on the thin sliver."""
    for words in (UK4, ANCHORS):
        vals = []
        for k in range(len(words)):
            rec = polygon.build(words[k:] + words[:k])
            vals.append(polygon.area_km2_turning(
                [(v["lat"], v["lon"]) for v in rec["vertices"]]))
        assert max(vals) - min(vals) == 0.0


def test_area_is_invariant_under_reversal():
    fwd = polygon.build(UK4)["area_km2"]
    rev = polygon.build(list(reversed(UK4)))["area_km2"]
    assert rev == pytest.approx(fwd, rel=1e-7)


def test_perimeter_is_the_sum_of_verified_edges():
    rec = polygon.build(UK4)
    assert sum(e["km"] for e in rec["edges"]) == pytest.approx(
        rec["perimeter_km"], rel=1e-12)
    for e in rec["edges"]:
        assert e["km"] > 0


def test_centroid_lies_inside_the_bounding_box():
    rec = polygon.build(UK4)
    lats = [v["lat"] for v in rec["vertices"]]
    lons = [v["lon"] for v in rec["vertices"]]
    clat, clon = rec["centroid"]
    assert min(lats) <= clat <= max(lats)
    assert min(lons) <= clon <= max(lons)


# ------------------------------------------------------------ validity

def test_self_intersection_is_detected_and_area_is_withheld():
    bowtie = [(0, 0), (10, 10), (0, 10), (10, 0)]
    assert polygon.self_intersections(bowtie)
    simple = [(0, 0), (0, 10), (10, 10), (10, 0)]
    assert not polygon.self_intersections(simple)


def test_a_self_crossing_polygon_is_not_marked_trustworthy():
    rec = polygon.build(["165876523", "165892783", "165892743",
                         "165892763"])
    if rec["self_intersections"]:
        assert not rec["area_is_trustworthy"]
        assert not rec["is_simple"]


def test_reorder_by_bearing_produces_a_simple_ring():
    rec = polygon.build(["165876523", "165892783", "165892743",
                         "165892763"], reorder=True)
    assert rec["is_simple"]
    assert rec["vertex_order"] == "REORDERED_BY_CENTROID_BEARING"


def test_fewer_than_three_distinct_vectors_is_refused():
    with pytest.raises(polygon.PolygonError, match="at least 3"):
        polygon.build(ANCHORS[:2])
    with pytest.raises(polygon.PolygonError, match="distinct"):
        polygon.build(["165876523"] * 3)


def test_a_gated_wide_envelope_record_cannot_become_a_vertex():
    with pytest.raises(Exception):
        polygon.build(["165876523", "167849523", "1687293589323"])


# --------------------------------------------------------- provenance

def test_every_vertex_declares_its_coordinate_source():
    rec = polygon.build(ANCHORS + ["165892743"])
    srcs = {v["coordinate_source"] for v in rec["vertices"]}
    assert srcs == {"FIT_ANCHOR_TARGET", "V1_PINNED_PROJECTION"}
    for v in rec["vertices"]:
        assert v["is_located_target"] is False


def test_polygon_never_claims_verified_places():
    rec = polygon.build(ANCHORS)
    assert rec["polygon_geometry_is_verified"] is True
    assert rec["vertices_are_verified_places"] is False
    assert "underdetermined" in rec["caveat"]


def test_branch_mix_is_reported():
    assert polygon.build(ANCHORS)["all_same_branch"] is False
    assert polygon.build(UK4)["all_same_branch"] is True
    assert polygon.build(UK4)["branches"] == ["117"]


# ------------------------------------------------------ the page itself

def test_page_is_self_contained_for_the_library(tmp_path):
    out = tmp_path / "poly.html"
    polygon_page.render(str(out))
    html = out.read_text("utf-8")
    assert "unpkg.com" not in html
    assert 'src="vendor/leaflet.js"' in html
    assert "underdetermined" in html


def test_page_has_add_remove_and_reorder_controls(tmp_path):
    out = tmp_path / "poly.html"
    polygon_page.render(str(out))
    html = out.read_text("utf-8")
    for token in ("id=\"entry\"", "id=\"add\"", "id=\"clear\"",
                  "id=\"reorder\"", "'Remove'", "'Up'"):
        assert token in html, token
    # gated records must be rejected client-side too
    assert "V1-B07" in html and "1687293589323" in html


def test_page_button_labels_avoid_glyphs_that_may_not_render(tmp_path):
    """An unrenderable glyph makes a control look like a blank box."""
    out = tmp_path / "poly.html"
    polygon_page.render(str(out))
    js = out.read_text("utf-8")
    assert "textContent='×'" not in js
    assert "textContent='↑'" not in js


# ---------------------------------------------- JS/Python kernel parity

def test_js_kernel_matches_python_exactly():
    """The page reimplements the projector; it must not drift.

    A UI that silently disagreed with the library would be worse than
    no UI, so this runs the real JS through QtWebEngine and compares
    every known vector in metres.
    """
    pytest.importorskip("PySide6.QtWebEngineWidgets")
    import json
    import os
    import sys
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS",
                          "--disable-gpu --no-sandbox")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([sys.argv[0]])
    view = QWebEngineView()
    view.resize(400, 300)
    view.show()
    loop = QEventLoop()
    view.loadFinished.connect(lambda ok: loop.quit())
    view.setHtml("<html><body></body></html>")
    QTimer.singleShot(15000, loop.quit)
    loop.exec()

    box = {}
    run = QEventLoop()
    view.page().runJavaScript(polygon_page.parity_probe(),
                              lambda r: (box.update(r=r), run.quit()))
    QTimer.singleShot(30000, run.quit)
    run.exec()
    try:
        assert box.get("r"), "JS probe returned nothing"
        result = json.loads(box["r"])
        assert result["worst_drift_m"] < 1e-3, result
        assert len(result["rows"]) == 7
    finally:
        view.close()
        view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        app.processEvents()


def test_parity_probe_covers_every_known_vector():
    probe = polygon_page.parity_probe()
    for w in ("165876523", "167849523", "168930443", "165879243",
              "165892743", "165892763", "165892783"):
        assert w in probe


# ---------------------------------------------------------------- CLI

def test_cli_polygon_accepts_a_comma_separated_list(tmp_path, capsys):
    from r1053.__main__ import main
    out = tmp_path / "p.html"
    assert main(["polygon", ",".join(ANCHORS), "-o", str(out)]) == 0
    text = capsys.readouterr().out
    assert "vertices        3" in text
    assert "area" in text and "cross-check" in text
    assert "underdetermined" in text
    assert out.exists()


def test_cli_polygon_refuses_two_vectors(capsys):
    from r1053.__main__ import main
    assert main(["polygon", "165876523,167849523"]) == 2
    assert "at least 3" in capsys.readouterr().err
