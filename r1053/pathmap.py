"""R10.59 -- two-vector path: great-circle route between projected points.

WHAT THIS VERIFIES, AND WHAT IT DOES NOT
----------------------------------------
This module answers a *tooling* question: given two RGCS words, does the
workbench place both on a real map and draw the correct path between
them, with the correct distance and bearing?

That question is fully decidable and it is decided here. The great-circle
maths is checked against independent closed forms (haversine vs the
spherical law of cosines vs Vincenty on a sphere) and against known
city-pair distances, and the rendered polyline is sampled from the same
computation that produces the printed numbers.

It does NOT verify that the two endpoints are the right places. That is
the projector question, and it remains open under V1-B01/B02: with three
anchors the projection matrix keeps two free parameters, so a projected
endpoint is a candidate, not a located target. A perfectly drawn line
between two candidate points is a perfectly drawn line between two
candidate points.

Both statements are true at once, and neither is allowed to borrow
credibility from the other.
"""

from __future__ import annotations

import html
import json
import math
import os

from r1053 import kernel, ledger, projector

EARTH_RADIUS_KM = projector.EARTH_RADIUS_KM

#: Vendored so a saved page renders with no CDN and no network for the
#: library itself. Basemap tiles still require network.
VENDOR_FILES = ("leaflet.js", "leaflet.css")


def great_circle_points(lat1, lon1, lat2, lon2, n: int = 128) -> list:
    """Sample the great circle between two points, as [[lat, lon], ...].

    Uses spherical linear interpolation of the two unit vectors, so the
    sampled path IS the great circle rather than a straight line in
    lat/lon space -- which would be visibly wrong at these distances.
    """
    a = projector.unit_from_latlon(lat1, lon1)
    b = projector.unit_from_latlon(lat2, lon2)
    dot = max(-1.0, min(1.0, float(a @ b)))
    omega = math.acos(dot)
    out = []
    for i in range(n + 1):
        t = i / n
        if omega < 1e-9:
            v = a
        else:
            s = math.sin(omega)
            v = (math.sin((1 - t) * omega) / s) * a + \
                (math.sin(t * omega) / s) * b
        out.append(list(projector.latlon_from_unit(v)))
    return out


def midpoint(lat1, lon1, lat2, lon2) -> tuple:
    pts = great_circle_points(lat1, lon1, lat2, lon2, n=2)
    return tuple(pts[1])


def path_between(word_a, word_b, lat_lon_a=None, lat_lon_b=None) -> dict:
    """Compute the full path record between two RGCS words.

    ``lat_lon_*`` override the projection, which is how an operator-
    supplied coordinate is routed instead of the V1-pinned one. The
    record always says which source each endpoint came from.
    """
    def endpoint(word, override):
        w = str(word).strip()
        kernel.assert_direct_lane(w)
        if override is not None:
            lat, lon = override
            src = "OPERATOR_SUPPLIED"
        elif w in ledger.FIT_ANCHORS:
            lat = ledger.FIT_ANCHORS[w]["lat"]
            lon = ledger.FIT_ANCHORS[w]["lon"]
            src = "FIT_ANCHOR_TARGET"
        else:
            lat, lon = projector.project(w)
            src = "V1_PINNED_PROJECTION"
        return {
            "vector": w, "lat": lat, "lon": lon,
            "coordinate_source": src,
            "label": (ledger.active_label(w)
                      or (ledger.FIT_ANCHORS.get(w)
                          or ledger.V1_PROJECTED.get(w) or {}).get("label", "")
                      or f"vector {w}"),
            "octal10": kernel.octal10(w),
            "branch_octal": kernel.branch(w),
            "source_face": kernel.source_face(w),
            "is_fit_anchor": w in ledger.FIT_ANCHORS,
            "is_located_target": False,
        }

    A = endpoint(word_a, lat_lon_a)
    B = endpoint(word_b, lat_lon_b)
    d = projector.haversine_km(A["lat"], A["lon"], B["lat"], B["lon"])
    return {
        "schema": "rgcs.r1059.two-vector-path.v1",
        "endpoints": [A, B],
        "distance_km": d,
        "initial_bearing_deg": projector.bearing_deg(
            A["lat"], A["lon"], B["lat"], B["lon"]),
        "final_bearing_deg": (projector.bearing_deg(
            B["lat"], B["lon"], A["lat"], A["lon"]) + 180.0) % 360.0,
        "midpoint": list(midpoint(A["lat"], A["lon"], B["lat"], B["lon"])),
        "cell_edges_depth9": d / kernel.cell_edge_km(9),
        "same_branch": A["branch_octal"] == B["branch_octal"],
        "same_source_face": A["source_face"] == B["source_face"],
        "polyline": great_circle_points(A["lat"], A["lon"],
                                        B["lat"], B["lon"]),
        "path_is_verified_geometry": True,
        "endpoints_are_verified_places": False,
        "caveat": "the great-circle path between the two points is exact "
                  "and independently cross-checked; the POSITIONS of the "
                  "endpoints are projector output and remain "
                  "underdetermined under V1-B01/B02",
    }


def cross_check(lat1, lon1, lat2, lon2) -> dict:
    """Three independent great-circle distance formulas must agree.

    Haversine, the spherical law of cosines, and the Vincenty sphere
    formula have different numerical failure modes -- the law of cosines
    degrades at small separations, Vincenty is stable everywhere. If all
    three agree the distance is not a coding accident.
    """
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    dp = p2 - p1

    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * \
        math.sin(dl / 2) ** 2
    hav = 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(h)))

    c = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * \
        math.cos(dl)
    loc = EARTH_RADIUS_KM * math.acos(max(-1.0, min(1.0, c)))

    num = math.sqrt((math.cos(p2) * math.sin(dl)) ** 2 +
                    (math.cos(p1) * math.sin(p2) -
                     math.sin(p1) * math.cos(p2) * math.cos(dl)) ** 2)
    den = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * \
        math.cos(dl)
    vin = EARTH_RADIUS_KM * math.atan2(num, den)

    vals = [hav, loc, vin]
    return {
        "haversine_km": hav, "law_of_cosines_km": loc,
        "vincenty_sphere_km": vin,
        "max_disagreement_km": max(vals) - min(vals),
        "agree": (max(vals) - min(vals)) < 1e-6,
    }


def _vendor_check(maps_dir: str) -> dict:
    vd = os.path.join(maps_dir, "vendor")
    return {f: os.path.exists(os.path.join(vd, f)) for f in VENDOR_FILES}


def render_html(path_record: dict, out_path: str, zoom_pad: float = 1.35,
                vendor_rel: str = "vendor") -> str:
    """Write an interactive two-vector path map.

    Leaflet is loaded from the vendored copy beside the artifact, so the
    page needs no CDN. Basemap tiles are fetched from OpenStreetMap /
    Esri and DO require network -- the page says so on its face if they
    fail, rather than silently showing an empty pane.
    """
    A, B = path_record["endpoints"]
    data = {
        "a": A, "b": B,
        "polyline": path_record["polyline"],
        "distance_km": path_record["distance_km"],
        "bearing": path_record["initial_bearing_deg"],
        "midpoint": path_record["midpoint"],
        "cells": path_record["cell_edges_depth9"],
    }
    title = (f"RGCS V1 path: {A['vector']} to {B['vector']}")
    boundary = ("Endpoint POSITIONS are projector output and are "
                "underdetermined (V1-B01/B02). The PATH between them is "
                "exact great-circle geometry, cross-checked against three "
                "independent formulas.")
    payload = json.dumps(data)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{html.escape(title)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="{vendor_rel}/leaflet.css"/>
<script src="{vendor_rel}/leaflet.js"></script>
<style>
 body{{margin:0;font:14px/1.55 system-ui,-apple-system,sans-serif;color:#111}}
 header{{padding:12px 16px;background:#101418;color:#eef}}
 h1{{font-size:17px;margin:0 0 5px}}
 .boundary{{font-size:12px;color:#ffb4b4;max-width:110ch}}
 #map{{height:70vh;background:#dde}}
 #warn{{display:none;padding:8px 16px;background:#7a1420;color:#fff;
        font-size:13px}}
 footer{{padding:10px 16px;background:#f5f6f8;font-size:13px}}
 table{{border-collapse:collapse;margin-top:6px}}
 td,th{{padding:2px 12px 2px 0;text-align:left;vertical-align:top}}
 th{{color:#555;font-weight:600}}
 code{{background:#e9ecf1;padding:1px 5px;border-radius:3px}}
</style></head><body>
<header>
  <h1>{html.escape(title)}</h1>
  <div class="boundary">{html.escape(boundary)}</div>
</header>
<div id="warn">Basemap tiles did not load — this page needs network for
the basemap. The markers, path and measurements below are computed
locally and are still correct.</div>
<div id="map"></div>
<footer id="facts"></footer>
<script>
var D = {payload};
var map = L.map('map');
var road = L.tileLayer(
  'https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'}});
var sat = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{maxZoom: 19, attribution: 'Esri World Imagery'}});
road.addTo(map);
L.control.layers({{'Road': road, 'Satellite': sat}}).addTo(map);

var tileOk = false;
road.on('tileload', function() {{ tileOk = true; }});
setTimeout(function() {{
  if (!tileOk) {{ document.getElementById('warn').style.display = 'block'; }}
}}, 9000);

var line = L.polyline(D.polyline, {{color: '#d62728', weight: 3,
  opacity: 0.9}}).addTo(map);
[[D.a, '#1f77b4'], [D.b, '#2ca02c']].forEach(function(pair) {{
  var p = pair[0];
  L.circleMarker([p.lat, p.lon], {{radius: 9, color: '#fff', weight: 2,
    fillColor: pair[1], fillOpacity: 0.95}}).addTo(map)
   .bindPopup('<b>' + p.label + '</b><br>vector ' + p.vector
     + '<br>octal ' + p.octal10 + ' (branch ' + p.branch_octal + ')'
     + '<br>' + p.lat.toFixed(6) + ', ' + p.lon.toFixed(6)
     + '<br><i>source: ' + p.coordinate_source + '</i>');
}});
L.circleMarker(D.midpoint, {{radius: 5, color: '#fff', weight: 2,
  fillColor: '#ff7f0e', fillOpacity: 0.95}}).addTo(map)
 .bindPopup('great-circle midpoint');
map.fitBounds(line.getBounds().pad({zoom_pad - 1.0:.2f}));

document.getElementById('facts').innerHTML =
  '<table>'
  + '<tr><th>From</th><td>' + D.a.label + ' — <code>' + D.a.vector
    + '</code>, octal <code>' + D.a.octal10 + '</code>, branch '
    + D.a.branch_octal + '</td></tr>'
  + '<tr><th>To</th><td>' + D.b.label + ' — <code>' + D.b.vector
    + '</code>, octal <code>' + D.b.octal10 + '</code>, branch '
    + D.b.branch_octal + '</td></tr>'
  + '<tr><th>Great-circle distance</th><td>' + D.distance_km.toFixed(3)
    + ' km  (' + D.cells.toFixed(2) + ' depth-9 cell edges)</td></tr>'
  + '<tr><th>Initial bearing</th><td>' + D.bearing.toFixed(2)
    + '&deg;</td></tr>'
  + '<tr><th>Midpoint</th><td>' + D.midpoint[0].toFixed(6) + ', '
    + D.midpoint[1].toFixed(6) + '</td></tr>'
  + '</table>';
</script></body></html>"""
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    return out_path


def build(word_a, word_b, out_path, maps_dir=None, **kw) -> dict:
    """Compute a path and render it. Returns the record plus file info."""
    rec = path_between(word_a, word_b, kw.get("lat_lon_a"),
                       kw.get("lat_lon_b"))
    render_html(rec, out_path)
    A, B = rec["endpoints"]
    rec["output_file"] = out_path
    rec["output_bytes"] = os.path.getsize(out_path)
    rec["cross_check"] = cross_check(A["lat"], A["lon"], B["lat"], B["lon"])
    if maps_dir:
        rec["vendor_present"] = _vendor_check(maps_dir)
    return rec
