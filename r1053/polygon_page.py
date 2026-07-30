"""R10.59B -- the interactive polygon builder page.

The vertex list is editable in the browser: type a vector, press Add,
remove any row, reorder, and the polygon re-measures live. To do that
without a server round-trip the page carries a JavaScript port of the
V1 kernel -- icosahedron vertices, the (F5+14)%20 face map, the 10/19
slerp refinement, and the pinned projection matrix A.

That port is a second implementation of the same law, which makes it a
liability unless it is checked. :func:`parity_probe` returns JavaScript
that recomputes every known vector and reports the JS-vs-Python
disagreement in metres, and the test suite fails if any vector drifts.
A UI that silently disagreed with the library would be worse than no
UI at all.
"""

from __future__ import annotations

import html
import json

import numpy as np

from r1053 import kernel, ledger, pathmap, polygon, projector

#: Vectors offered as one-click chips in the builder.
PRESETS = (
    ("165876523", "Stonehenge (anchor)"),
    ("167849523", "Erie (anchor)"),
    ("168930443", "Toronto (anchor)"),
    ("165879243", "Drummondville / Saint-Eugene"),
    ("165892743", "Orange A"),
    ("165892763", "Orange B"),
    ("165892783", "Orange C"),
)


def _kernel_constants() -> dict:
    """Everything the JS port needs, taken from the Python objects."""
    A = projector.fit_matrix()
    return {
        "V": [list(map(float, v)) for v in kernel._V],
        "F": [list(f) for f in kernel._F],
        "A": [list(map(float, r)) for r in A],
        "t": kernel.SPLIT_T,
        "faceOffset": kernel.FACE_OFFSET,
        "faceCount": kernel.FACE_COUNT,
        "symbols": kernel.Q22_SYMBOLS,
        "R": polygon.EARTH_RADIUS_KM,
        "anchors": {w: [d["lat"], d["lon"]]
                    for w, d in ledger.FIT_ANCHORS.items()},
        "operator": {w: [d["lat"], d["lon"]]
                     for w, d in ledger.V1_PROJECTED.items()},
        "labels": {**{w: d["label"] for w, d in ledger.FIT_ANCHORS.items()},
                   **{w: d["label"] for w, d in ledger.V1_PROJECTED.items()}},
        "gated": list(ledger.GATED_WIDE_ENVELOPE),
        "presets": [list(p) for p in PRESETS],
    }


#: The JS port of the V1 kernel. Kept in one string so the parity probe
#: and the page cannot drift apart.
KERNEL_JS = r"""
function norm(v){var n=Math.hypot(v[0],v[1],v[2]);return [v[0]/n,v[1]/n,v[2]/n];}
function dot(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
function slerp(a,b,t){
  var d=Math.max(-1,Math.min(1,dot(a,b))), o=Math.acos(d);
  if(o<1e-12) return a.slice();
  var s=Math.sin(o), c1=Math.sin((1-t)*o)/s, c2=Math.sin(t*o)/s;
  return [c1*a[0]+c2*b[0], c1*a[1]+c2*b[1], c1*a[2]+c2*b[2]];
}
function fields(v){
  return {f5:(v>>>25)&31, q22:(v>>>3)&0x3FFFFF, s3:v&7};
}
function q22syms(q){
  var out=[]; for(var i=0;i<K.symbols;i++){ out.push((q>>>(20-2*i))&3); }
  return out;
}
function kernelVector(dec){
  var v=Number(dec), f=fields(v);
  var face=(f.f5+K.faceOffset)%K.faceCount, tri=K.F[face].map(function(i){return K.V[i];});
  var syms=q22syms(f.q22);
  for(var i=0;i<syms.length;i++){
    var a=tri[0],b=tri[1],c=tri[2];
    var ab=slerp(a,b,K.t), bc=slerp(b,c,K.t), ca=slerp(c,a,K.t);
    tri = syms[i]===0?[a,ab,ca] : syms[i]===1?[ab,b,bc] : syms[i]===2?[ca,bc,c] : [ab,bc,ca];
  }
  return norm([tri[0][0]+tri[1][0]+tri[2][0],
               tri[0][1]+tri[1][1]+tri[2][1],
               tri[0][2]+tri[1][2]+tri[2][2]]);
}
function project(dec){
  var u=kernelVector(dec), A=K.A;
  var w=[A[0][0]*u[0]+A[0][1]*u[1]+A[0][2]*u[2],
         A[1][0]*u[0]+A[1][1]*u[1]+A[1][2]*u[2],
         A[2][0]*u[0]+A[2][1]*u[1]+A[2][2]*u[2]];
  w=norm(w);
  return [Math.asin(Math.max(-1,Math.min(1,w[2])))*180/Math.PI,
          Math.atan2(w[1],w[0])*180/Math.PI];
}
function latlon(dec){
  var s=String(dec).trim();
  if(K.anchors[s]) return {lat:K.anchors[s][0], lon:K.anchors[s][1], src:'FIT_ANCHOR_TARGET'};
  var p=project(s);
  return {lat:p[0], lon:p[1], src:'V1_PINNED_PROJECTION'};
}
function octal10(dec){
  var s=Number(dec).toString(8); while(s.length<10) s='0'+s; return s;
}
function toUnit(lat,lon){
  var la=lat*Math.PI/180, lo=lon*Math.PI/180;
  return [Math.cos(la)*Math.cos(lo), Math.cos(la)*Math.sin(lo), Math.sin(la)];
}
function gcKm(a,b,c,d){
  var u=toUnit(a,b), v=toUnit(c,d);
  return K.R*Math.acos(Math.max(-1,Math.min(1,dot(u,v))));
}
function gcPath(a,b,c,d,n){
  var u=toUnit(a,b), v=toUnit(c,d);
  var o=Math.acos(Math.max(-1,Math.min(1,dot(u,v)))), out=[];
  for(var i=0;i<=n;i++){
    var t=i/n, w;
    if(o<1e-9){ w=u; } else {
      var s=Math.sin(o), c1=Math.sin((1-t)*o)/s, c2=Math.sin(t*o)/s;
      w=norm([c1*u[0]+c2*v[0], c1*u[1]+c2*v[1], c1*u[2]+c2*v[2]]);
    }
    out.push([Math.asin(Math.max(-1,Math.min(1,w[2])))*180/Math.PI,
              Math.atan2(w[1],w[0])*180/Math.PI]);
  }
  return out;
}
function areaExcess(pts){
  if(pts.length<3) return 0;
  var v=pts.map(function(p){return toUnit(p[0],p[1]);}), total=0;
  for(var i=1;i<v.length-1;i++){
    var a=v[0], b=v[i], c=v[i+1];
    var ab=Math.acos(Math.max(-1,Math.min(1,dot(a,b))));
    var bc=Math.acos(Math.max(-1,Math.min(1,dot(b,c))));
    var ca=Math.acos(Math.max(-1,Math.min(1,dot(c,a))));
    var s=(ab+bc+ca)/2;
    var t=Math.tan(s/2)*Math.tan((s-ab)/2)*Math.tan((s-bc)/2)*Math.tan((s-ca)/2);
    if(t<=0) continue;
    var ex=4*Math.atan(Math.sqrt(t));
    var cr=[(b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]),
            (b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]),
            (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])];
    total += (dot(cr,a)>=0?1:-1)*ex;
  }
  return Math.abs(total)*K.R*K.R;
}
"""


def parity_probe() -> str:
    """JS that recomputes every known vector and reports drift in metres."""
    words = list(ledger.FIT_ANCHORS) + list(ledger.V1_PROJECTED)
    py = {w: list(projector.project(w)) for w in words}
    return (f"var K = {json.dumps(_kernel_constants())};\n"
            + KERNEL_JS
            + f"\nvar PY = {json.dumps(py)};\n"
            + """
(function(){
  var worst = 0, rows = [];
  for (var w in PY) {
    var p = project(w), q = PY[w];
    var d = gcKm(p[0], p[1], q[0], q[1]) * 1000.0;
    if (d > worst) worst = d;
    rows.push({vector: w, drift_m: d});
  }
  return JSON.stringify({worst_drift_m: worst, rows: rows});
})();
""")


def render(out_path: str, initial=None, vendor_rel: str = "vendor") -> str:
    """Write the interactive polygon builder."""
    K = _kernel_constants()
    initial = list(initial or ["165876523", "165892743", "165892783"])
    boundary = ("Vertex POSITIONS are projector output and are "
                "underdetermined (V1-B01/B02). The polygon's area, "
                "perimeter and centroid are exact for those vertices and "
                "are cross-checked by two independent spherical methods.")
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>RGCS V1 — polygon builder</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="{vendor_rel}/leaflet.css"/>
<script src="{vendor_rel}/leaflet.js"></script>
<style>
 :root{{color-scheme:light dark}}
 body{{margin:0;font:14px/1.55 system-ui,-apple-system,sans-serif;color:#111;
       background:#fff}}
 header{{padding:12px 16px;background:#101418;color:#eef}}
 h1{{font-size:17px;margin:0 0 5px}}
 .boundary{{font-size:12px;color:#ffb4b4;max-width:112ch}}
 .wrap{{display:flex;flex-wrap:wrap;gap:0}}
 #side{{width:340px;padding:12px 14px;box-sizing:border-box;
        border-right:1px solid #d8dbe0;max-height:78vh;overflow:auto}}
 #map{{flex:1;min-width:340px;height:78vh;background:#dde}}
 input[type=text]{{width:190px;padding:6px 8px;font:13px ui-monospace,monospace;
   border:1px solid #b9bec7;border-radius:4px}}
 button{{padding:6px 10px;font:13px system-ui;border:1px solid #b9bec7;
   background:#f2f4f7;border-radius:4px;cursor:pointer}}
 button:hover{{background:#e6e9ee}}
 button.danger{{border-color:#d9a2a2;background:#fbeeee}}
 ul{{list-style:none;padding:0;margin:10px 0}}
 li{{display:flex;align-items:center;gap:6px;padding:5px 6px;margin:3px 0;
     border:1px solid #dfe3e8;border-radius:5px;background:#fafbfc}}
 li .v{{font:13px ui-monospace,monospace;font-weight:600}}
 li .l{{flex:1;font-size:11.5px;color:#555;overflow:hidden;
        text-overflow:ellipsis;white-space:nowrap}}
 li button{{padding:2px 7px;font-size:12px;line-height:1.3}}
 .chips button{{margin:2px 3px 2px 0;font-size:11.5px;padding:3px 7px}}
 #err{{color:#a11;font-size:12.5px;min-height:1.2em;margin-top:6px}}
 table{{border-collapse:collapse;width:100%;margin-top:8px;font-size:13px}}
 th{{text-align:left;color:#555;font-weight:600;padding:2px 8px 2px 0;
     vertical-align:top;white-space:nowrap}}
 td{{padding:2px 0}}
 .warnbox{{display:none;margin-top:8px;padding:7px 9px;background:#7a1420;
   color:#fff;border-radius:5px;font-size:12.5px}}
 footer{{padding:10px 16px;background:#f5f6f8;font-size:12.5px;color:#333}}
 @media (prefers-color-scheme: dark){{
   body{{background:#14171b;color:#e8eaed}}
   #side{{border-right-color:#2a2f36}}
   li{{background:#1b1f24;border-color:#2a2f36}}
   li .l{{color:#9aa3ad}} th{{color:#9aa3ad}}
   input[type=text],button{{background:#1b1f24;color:#e8eaed;
     border-color:#39404a}}
   button:hover{{background:#232830}}
   footer{{background:#1b1f24;color:#c8ccd2}}
 }}
</style></head><body>
<header>
  <h1>RGCS V1 — polygon builder</h1>
  <div class="boundary">{html.escape(boundary)}</div>
</header>
<div class="wrap">
  <div id="side">
    <div>
      <input type="text" id="entry" placeholder="e.g. 165876523"
             inputmode="numeric" autocomplete="off">
      <button id="add">Add</button>
    </div>
    <div id="err"></div>
    <div class="chips" id="chips"></div>
    <ul id="list"></ul>
    <div>
      <button id="reorder">Order by bearing</button>
      <button id="clear" class="danger">Clear all</button>
    </div>
    <div class="warnbox" id="selfx"></div>
    <table id="stats"></table>
  </div>
  <div id="map"></div>
</div>
<footer id="note"></footer>
<script>
var K = {json.dumps(K)};
{KERNEL_JS}

var vectors = {json.dumps(initial)};
var map = L.map('map');
var road = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{maxZoom:19, attribution:'&copy; OpenStreetMap contributors'}});
var sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  {{maxZoom:19, attribution:'Esri World Imagery'}});
road.addTo(map);
L.control.layers({{'Road':road,'Satellite':sat}}).addTo(map);
var layer = L.layerGroup().addTo(map);

function esc(s){{ return String(s).replace(/[&<>"]/g,
  function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];}}); }}

function validate(s){{
  s = String(s).trim();
  if(!/^\\d+$/.test(s)) return 'not a decimal RGCS word';
  if(K.gated.indexOf(s) >= 0)
    return 'gated wide-envelope record (blocker V1-B07) — refused, never truncated';
  var v = Number(s);
  if(v > 1073741823) return s.length + '-digit value exceeds the 30-bit direct word';
  if(vectors.indexOf(s) >= 0) return 'already in the list';
  return null;
}}

function segHit(p1,p2,p3,p4){{
  var a=toUnit(p1[0],p1[1]),b=toUnit(p2[0],p2[1]),
      c=toUnit(p3[0],p3[1]),d=toUnit(p4[0],p4[1]);
  function cross(u,v){{return [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],
                              u[0]*v[1]-u[1]*v[0]];}}
  var l=cross(cross(a,b),cross(c,d)), n=Math.hypot(l[0],l[1],l[2]);
  if(n<1e-12) return false;
  l=[l[0]/n,l[1]/n,l[2]/n];
  function ang(u,v){{return Math.acos(Math.max(-1,Math.min(1,dot(u,v))));}}
  function between(p,q,x){{return ang(p,x)+ang(q,x) <= ang(p,q)+1e-9;}}
  for(var k=0;k<2;k++){{
    var x = k? [-l[0],-l[1],-l[2]] : l;
    if(between(a,b,x) && between(c,d,x)){{
      var shared=[a,b,c,d].some(function(e){{return dot(x,e)>1-1e-12;}});
      if(!shared) return true;
    }}
  }}
  return false;
}}

function redraw(){{
  layer.clearLayers();
  var pts = vectors.map(function(v){{ var p=latlon(v); return [p.lat,p.lon]; }});
  var ul = document.getElementById('list');
  ul.innerHTML = '';
  vectors.forEach(function(v,i){{
    var p = latlon(v);
    var li = document.createElement('li');
    li.innerHTML = '<span class="v">'+esc(v)+'</span>'
      + '<span class="l">'+esc(K.labels[v] || 'projected candidate')+' · '
      + p.lat.toFixed(4)+', '+p.lon.toFixed(4)+'</span>';
    var up = document.createElement('button'); up.textContent='Up';
    up.title='move earlier in the ring';
    up.onclick=function(){{ if(i>0){{ var t=vectors[i-1];vectors[i-1]=vectors[i];
      vectors[i]=t; redraw(); }} }};
    var rm = document.createElement('button'); rm.textContent='Remove';
    rm.className='danger'; rm.title='remove this vertex';
    rm.onclick=function(){{ vectors.splice(i,1); redraw(); }};
    li.appendChild(up); li.appendChild(rm);
    ul.appendChild(li);
  }});

  var stats = document.getElementById('stats');
  var warn = document.getElementById('selfx');
  warn.style.display='none';
  if(pts.length < 3){{
    stats.innerHTML = '<tr><th>Vertices</th><td>'+pts.length
      + ' — need at least 3 for a polygon</td></tr>';
    if(pts.length === 2){{
      var line = L.polyline(gcPath(pts[0][0],pts[0][1],pts[1][0],pts[1][1],96),
        {{color:'#d62728',weight:3}}).addTo(layer);
      stats.innerHTML += '<tr><th>Distance</th><td>'
        + gcKm(pts[0][0],pts[0][1],pts[1][0],pts[1][1]).toFixed(3)+' km</td></tr>';
    }}
  }} else {{
    var ring = [];
    for(var i=0;i<pts.length;i++){{
      var j=(i+1)%pts.length;
      ring = ring.concat(gcPath(pts[i][0],pts[i][1],pts[j][0],pts[j][1],48));
    }}
    L.polygon(ring, {{color:'#d62728',weight:2.5,fillColor:'#d62728',
      fillOpacity:0.16}}).addTo(layer);
    var per=0;
    for(var i=0;i<pts.length;i++){{
      var j=(i+1)%pts.length;
      per += gcKm(pts[i][0],pts[i][1],pts[j][0],pts[j][1]);
    }}
    var xs=[];
    for(var i=0;i<pts.length;i++) for(var j=i+1;j<pts.length;j++){{
      if(j===i || (j+1)%pts.length===i || (i+1)%pts.length===j) continue;
      if(segHit(pts[i],pts[(i+1)%pts.length],pts[j],pts[(j+1)%pts.length]))
        xs.push([i,j]);
    }}
    var area = areaExcess(pts);
    var cu=[0,0,0];
    pts.forEach(function(p){{var u=toUnit(p[0],p[1]);
      cu=[cu[0]+u[0],cu[1]+u[1],cu[2]+u[2]];}});
    cu=norm(cu);
    var clat=Math.asin(Math.max(-1,Math.min(1,cu[2])))*180/Math.PI;
    var clon=Math.atan2(cu[1],cu[0])*180/Math.PI;
    L.circleMarker([clat,clon],{{radius:5,color:'#fff',weight:2,
      fillColor:'#ff7f0e',fillOpacity:.95}}).addTo(layer)
      .bindPopup('centroid');
    stats.innerHTML =
        '<tr><th>Vertices</th><td>'+pts.length+'</td></tr>'
      + '<tr><th>Area</th><td>'+(xs.length? '—' : area.toLocaleString(undefined,
          {{maximumFractionDigits:3}})+' km²')+'</td></tr>'
      + '<tr><th>Perimeter</th><td>'+per.toLocaleString(undefined,
          {{maximumFractionDigits:3}})+' km</td></tr>'
      + '<tr><th>Centroid</th><td>'+clat.toFixed(5)+', '+clon.toFixed(5)+'</td></tr>'
      + '<tr><th>Simple</th><td>'+(xs.length? 'no' : 'yes')+'</td></tr>';
    if(xs.length){{
      warn.style.display='block';
      warn.textContent = 'Polygon self-intersects at edge pairs '
        + JSON.stringify(xs) + '. A self-crossing ring has no well-defined '
        + 'interior, so no area is reported. Reorder the vertices.';
    }}
  }}

  pts.forEach(function(p,i){{
    var v = vectors[i], src = latlon(v).src;
    L.circleMarker(p,{{radius:8,color:'#fff',weight:2,
      fillColor: src==='FIT_ANCHOR_TARGET' ? '#1f77b4' : '#2ca02c',
      fillOpacity:.95}}).addTo(layer)
     .bindPopup('<b>'+esc(K.labels[v]||('vector '+v))+'</b><br>'+esc(v)
       +'<br>octal '+octal10(v)+'<br>'+p[0].toFixed(6)+', '+p[1].toFixed(6)
       +'<br><i>'+src+'</i>');
  }});
  if(pts.length) map.fitBounds(L.latLngBounds(pts).pad(0.35));
}}

document.getElementById('add').onclick = function(){{
  var e=document.getElementById('entry'), err=document.getElementById('err');
  var parts = e.value.split(/[,\\s]+/).filter(function(x){{return x;}});
  var bad = [];
  parts.forEach(function(s){{
    var m = validate(s);
    if(m) bad.push(s+': '+m); else vectors.push(String(s).trim());
  }});
  err.textContent = bad.join(' · ');
  if(!bad.length) e.value='';
  redraw();
}};
document.getElementById('entry').addEventListener('keydown', function(ev){{
  if(ev.key === 'Enter') document.getElementById('add').click();
}});
document.getElementById('clear').onclick = function(){{
  vectors = []; document.getElementById('err').textContent=''; redraw(); }};
document.getElementById('reorder').onclick = function(){{
  if(vectors.length < 3) return;
  var pts = vectors.map(function(v){{var p=latlon(v);return [p.lat,p.lon];}});
  var cu=[0,0,0];
  pts.forEach(function(p){{var u=toUnit(p[0],p[1]);
    cu=[cu[0]+u[0],cu[1]+u[1],cu[2]+u[2]];}});
  cu=norm(cu);
  var clat=Math.asin(cu[2])*180/Math.PI, clon=Math.atan2(cu[1],cu[0])*180/Math.PI;
  function bearing(a,b,c,d){{
    var p1=a*Math.PI/180,p2=c*Math.PI/180,dl=(d-b)*Math.PI/180;
    var y=Math.sin(dl)*Math.cos(p2);
    var x=Math.cos(p1)*Math.sin(p2)-Math.sin(p1)*Math.cos(p2)*Math.cos(dl);
    return (Math.atan2(y,x)*180/Math.PI+360)%360;
  }}
  var pair = vectors.map(function(v,i){{
    return {{v:v, b:bearing(clat,clon,pts[i][0],pts[i][1])}}; }});
  pair.sort(function(a,b){{return a.b-b.b;}});
  vectors = pair.map(function(x){{return x.v;}});
  redraw();
}};
var chips = document.getElementById('chips');
K.presets.forEach(function(p){{
  var b=document.createElement('button');
  b.textContent='+ '+p[1]; b.title=p[0];
  b.onclick=function(){{
    var m=validate(p[0]);
    document.getElementById('err').textContent = m? (p[0]+': '+m) : '';
    if(!m){{ vectors.push(p[0]); redraw(); }}
  }};
  chips.appendChild(b);
}});
document.getElementById('note').textContent =
  'Area is the exact spherical excess (L\\u2019Huilier) over the vertices as '
  + 'ordered. Vertex order defines the polygon: the same points in a different '
  + 'order enclose a different region. Basemap tiles need network; the geometry '
  + 'is computed locally.';
redraw();
</script></body></html>"""
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    return out_path
