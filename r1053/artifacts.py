"""R10.53 -- V1 map artifacts: GeoJSON, KML, CSV, interactive HTML, PNG.

Every artifact carries the V1 boundary in its own text, so a file that
travels on its own cannot be mistaken for a validated result. The
interactive maps reference online road/satellite tiles; the PNG files
are offline fallbacks drawn from the same coordinates.

Artifacts are written OUTSIDE the tracked tree by default, consistent
with the standing rule that bundles do not enter tracked source.
"""

from __future__ import annotations

import csv
import json
import math
import os
import xml.etree.ElementTree as ET

from r1053 import kernel, ledger, projector, residuals

BOUNDARY = ("RGCS V1 operational Earth-root projection. NOT final "
            "physical validation. Projector A retains two free "
            "parameters at three anchors; projected points for "
            "non-anchor words are candidates, not located targets.")

STYLES = {
    "fit_anchor": {"colour": "#1f77b4", "kml": "ff4477 1f", "marker": "o"},
    "v1_candidate": {"colour": "#d62728", "kml": "ff2827 d6", "marker": "*"},
    "projected_candidate": {"colour": "#ff7f0e", "kml": "ff0e7f ff",
                            "marker": "^"},
    "reference": {"colour": "#2ca02c", "kml": "ff02a0 2c", "marker": "s"},
}


def points() -> list:
    """Every V1 point, typed by role, with its label discipline attached."""
    out = []
    for vec, d in ledger.FIT_ANCHORS.items():
        out.append({"vector": vec, "label": d["label"], "lat": d["lat"],
                    "lon": d["lon"], "role": "fit_anchor",
                    "branch_octal": kernel.branch(vec),
                    "source_face": kernel.source_face(vec),
                    "note": "fits A; its residual is arithmetic, not "
                            "evidence"})
    for vec, d in ledger.V1_PROJECTED.items():
        out.append({"vector": vec, "label": d["label"], "lat": d["lat"],
                    "lon": d["lon"], "role": d["role"],
                    "branch_octal": kernel.branch(vec),
                    "source_face": kernel.source_face(vec),
                    "note": "projector output; candidate cell, not a "
                            "located target"})
    for name, d in ledger.REFERENCES.items():
        out.append({"vector": "", "label": name, "lat": d["lat"],
                    "lon": d["lon"], "role": "reference",
                    "branch_octal": "", "source_face": "",
                    "note": d["note"]})
    return out


def geojson() -> dict:
    return {
        "type": "FeatureCollection",
        "properties": {"schema": "rgcs.r1053.v1-points.geojson.v1",
                       "boundary": BOUNDARY,
                       "label_rule": ledger.LABEL_RULE},
        "features": [
            {"type": "Feature",
             "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
             "properties": {k: v for k, v in p.items()
                            if k not in ("lat", "lon")}}
            for p in points()],
    }


def kml() -> str:
    ns = "http://www.opengis.net/kml/2.2"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}kml")
    doc = ET.SubElement(root, f"{{{ns}}}Document")
    ET.SubElement(doc, f"{{{ns}}}name").text = "RGCS V1 Earth-root points"
    ET.SubElement(doc, f"{{{ns}}}description").text = BOUNDARY
    for role, st in STYLES.items():
        s = ET.SubElement(doc, f"{{{ns}}}Style", id=role)
        ic = ET.SubElement(s, f"{{{ns}}}IconStyle")
        ET.SubElement(ic, f"{{{ns}}}color").text = st["kml"].replace(" ", "")
    for p in points():
        pm = ET.SubElement(doc, f"{{{ns}}}Placemark")
        ET.SubElement(pm, f"{{{ns}}}name").text = p["label"]
        ET.SubElement(pm, f"{{{ns}}}description").text = (
            f"vector {p['vector'] or 'n/a'} | role {p['role']} | "
            f"branch {p['branch_octal'] or 'n/a'} | {p['note']}")
        ET.SubElement(pm, f"{{{ns}}}styleUrl").text = "#" + p["role"]
        pt = ET.SubElement(pm, f"{{{ns}}}Point")
        ET.SubElement(pt, f"{{{ns}}}coordinates").text = \
            f"{p['lon']},{p['lat']},0"
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            + ET.tostring(root, encoding="unicode"))


def _leaflet(title, centre, zoom, subset, extra_html="") -> str:
    """A self-describing Leaflet page with road and satellite layers."""
    data = json.dumps([p for p in points() if p["role"] in subset])
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
 body{{margin:0;font:14px/1.5 system-ui,sans-serif}}
 #map{{height:78vh}}
 header{{padding:10px 14px;background:#111;color:#eee}}
 h1{{font-size:16px;margin:0 0 4px}}
 .b{{font-size:12px;color:#f7b0b0}}
 footer{{padding:10px 14px;font-size:12px;color:#444;background:#f4f4f4}}
</style></head><body>
<header><h1>{title}</h1><div class="b">{BOUNDARY}</div></header>
<div id="map"></div>
<footer>{extra_html}<br><b>Label rule:</b> {ledger.LABEL_RULE}</footer>
<script>
var map=L.map('map').setView([{centre[0]},{centre[1]}],{zoom});
var road=L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{maxZoom:19,attribution:'&copy; OpenStreetMap'}}).addTo(map);
var sat=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{maxZoom:19,attribution:'Esri World Imagery'}});
L.control.layers({{'Road':road,'Satellite':sat}}).addTo(map);
var C={json.dumps({k: v["colour"] for k, v in STYLES.items()})};
{data}.forEach(function(p){{
  L.circleMarker([p.lat,p.lon],{{radius:p.role==='v1_candidate'?9:7,
    color:'#fff',weight:2,fillColor:C[p.role]||'#888',fillOpacity:.95}})
   .addTo(map)
   .bindPopup('<b>'+p.label+'</b><br>vector: '+(p.vector||'n/a')
     +'<br>role: '+p.role+'<br>branch: '+(p.branch_octal||'n/a')
     +'<br>'+p.lat.toFixed(6)+', '+p.lon.toFixed(6)+'<br><i>'+p.note+'</i>');
}});
</script></body></html>"""


def interactive_maps() -> dict:
    d = ledger.V1_PROJECTED["165879243"]
    city = ledger.REFERENCES["Drummondville_city"]
    sc = residuals.drummondville_report()
    return {
        "rgcs_great_lakes_drummondville_triangle_interactive.html":
            _leaflet("RGCS V1 - Erie / Toronto / Drummondville triangle",
                     (44.3, -76.0), 6,
                     {"fit_anchor", "v1_candidate", "reference"},
                     "Erie and Toronto are FIT ANCHORS - they define the "
                     "projector and cannot confirm it. Drummondville is "
                     "projector output."),
        "rgcs_drummondville_corridor_interactive.html":
            _leaflet("RGCS V1 - Drummondville / Saint-Eugene corridor",
                     ((d["lat"] + city["lat"]) / 2,
                      (d["lon"] + city["lon"]) / 2), 11,
                     {"v1_candidate", "reference"},
                     f"Projected point is {sc['city_centre_km']:.3f} km "
                     f"from the Drummondville city label, bearing "
                     f"{sc['rows'][-1]['bearing_from_reference_deg']:.0f} deg "
                     f"= WSW; nearest recorded reference is "
                     f"{sc['nearest_reference']} at "
                     f"{sc['nearest_km']:.3f} km."),
        "rgcs_uk_orange_stonehenge_interactive.html":
            _leaflet("RGCS V1 - UK orange triplet and Stonehenge",
                     (50.9, -0.7), 8,
                     {"fit_anchor", "projected_candidate"},
                     "Stonehenge is a FIT ANCHOR. The orange triplet are "
                     "projector outputs in octal branch 117."),
    }


def _static_png(path, pts, title, pad=0.35):
    """Offline PNG fallback. Matplotlib only; no tiles, no network."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    lats = [p["lat"] for p in pts]
    lons = [p["lon"] for p in pts]
    sp = max(max(lats) - min(lats), max(lons) - min(lons), 0.05)
    fig, ax = plt.subplots(figsize=(9, 7), dpi=130)
    for p in pts:
        st = STYLES.get(p["role"], STYLES["reference"])
        ax.scatter(p["lon"], p["lat"], s=190 if p["role"] == "v1_candidate"
                   else 110, c=st["colour"], marker=st["marker"],
                   edgecolors="white", linewidths=1.4, zorder=3,
                   label=p["role"])
        ax.annotate(p["label"], (p["lon"], p["lat"]),
                    textcoords="offset points", xytext=(8, 6), fontsize=7.5)
    ax.set_xlim(min(lons) - sp * pad, max(lons) + sp * pad)
    ax.set_ylim(min(lats) - sp * pad, max(lats) + sp * pad)
    ax.set_aspect(1.0 / max(math.cos(math.radians(sum(lats) / len(lats))),
                            1e-6))
    ax.grid(alpha=.3, linestyle=":")
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.set_title(title, fontsize=11)
    h, l = ax.get_legend_handles_labels()
    seen = dict(zip(l, h))
    ax.legend(seen.values(), seen.keys(), fontsize=7.5, loc="best")
    fig.text(0.5, 0.012, BOUNDARY, ha="center", fontsize=6.6,
             wrap=True, color="#a11")
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(path)
    plt.close(fig)
    return path


def write_all(outdir: str) -> dict:
    """Emit the full manifest. Returns {filename: bytes written}."""
    os.makedirs(outdir, exist_ok=True)
    written = {}

    def put(name, text):
        p = os.path.join(outdir, name)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        written[name] = os.path.getsize(p)

    put("rgcs_v1_projected_points.geojson",
        json.dumps(geojson(), indent=2) + "\n")
    put("rgcs_v1_projected_points.kml", kml() + "\n")

    csv_path = os.path.join(outdir, "rgcs_v1_points.csv")
    cols = ["vector", "label", "lat", "lon", "role", "branch_octal",
            "source_face", "note"]
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(points())
    written["rgcs_v1_points.csv"] = os.path.getsize(csv_path)

    for name, html in interactive_maps().items():
        put(name, html)

    pts = points()
    sets = {
        "rgcs_great_lakes_drummondville_triangle_static.png":
            ([p for p in pts if p["role"] in
              ("fit_anchor", "v1_candidate", "reference")
              and p["lon"] < -60],
             "RGCS V1 - Erie / Toronto / Drummondville"),
        "rgcs_drummondville_corridor_static.png":
            ([p for p in pts if p["lon"] < -60 and p["lat"] > 45],
             "RGCS V1 - Drummondville / Saint-Eugene corridor"),
        "rgcs_uk_orange_stonehenge_static.png":
            ([p for p in pts if p["lon"] > -60],
             "RGCS V1 - UK orange triplet and Stonehenge"),
    }
    for name, (subset, title) in sets.items():
        if subset:
            p = _static_png(os.path.join(outdir, name), subset, title)
            written[name] = os.path.getsize(p)
    return written
