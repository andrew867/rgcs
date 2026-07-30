# Map, path and polygon guide

```text
Vertex POSITIONS are projector output and remain underdetermined under V1-B01/B02.

Path, polygon, distance, perimeter, centroid, and area geometry are exact for the
selected vertices.

The tool verifies geometry.
It does not verify that a candidate vertex is physically true.
```

---

## 1. One vector — `map`

```bash
python -m r1053 map 168930443
python -m r1053 serve
```

Writes a single-vertex map and opens the polygon builder seeded with that vector. The
position comes from one of three sources, always named in the output:

| source | meaning |
|---|---|
| `FIT_ANCHOR_TARGET` | the recorded anchor coordinate — this word helped *define* the projector |
| `V1_PINNED_PROJECTION` | projector output under the recorded pinning rule |
| `OPERATOR_SUPPLIED` | a coordinate passed in with `--latlon` |

A `FIT_ANCHOR_TARGET` landing correctly is not a success. It fits because it was
fitted.

---

## 2. Two vectors — `path`

```bash
python -m r1053 path 167849523 168930443
```

```
distance        178.846 km (11.93 depth-9 cell edges)
initial bearing 18.41 deg
midpoint        42.891736, -79.738486
cross-check     3 formulas agree: True (spread 2.67e-11 km)
```

### The distance is cross-checked three ways

Haversine, the spherical law of cosines, and Vincenty-on-a-sphere have different
numerical failure modes — the law of cosines degrades at small separations, Vincenty
is stable everywhere. All three must agree to < 1e-6 km. A 90° separation must come
out at exactly a quarter of the circumference.

### The drawn line is a real great circle

The polyline is 128 points of spherical linear interpolation between the two unit
vectors — **not** a straight line in lat/lon space, which would be visibly wrong at
these distances. Two properties are asserted:

- the sampled midpoint is **equidistant** from both endpoints;
- the segment lengths **sum to** the reported distance.

Over Erie→Toronto the great-circle midpoint differs from the naive lat/lon mean by
358 m; over Stonehenge→Toronto, by more than 100 km.

### The B01 example

```bash
python -m r1053 path 165879243 165879243 --b-latlon 45.8418969,-72.6788251
```

This draws **one vector at two admissible pinnings**: same decimal, same octal word
`1170616713`, same branch `117` — 5121.7 km apart, one on the English south coast and
one in Quebec. Both fit all three anchors to machine precision.

This is the clearest single picture of why endpoint positions are not verified. See
[BLOCKERS_B01_B07.md](BLOCKERS_B01_B07.md).

---

## 3. Three or more vectors — `polygon`

```bash
python -m r1053 polygon 165876523,167849523,168930443
python -m r1053 polygon 165876523 165892743 165892763 165892783 --reorder
```

Comma- or space-separated. The generated page is a **live builder**: type a vector and
press Add (or paste a comma-separated list), **Remove** any row, **Up** to reorder,
**Order by bearing**, **Clear all**, or use the preset chips. Everything recomputes on
each edit.

### How the area is computed

Two **independent exact** methods must agree:

1. **L'Huilier's theorem** over a fan triangulation from vertex 0. Numerically stable
   for the thin slivers RGCS vector sets often produce.
2. **The Gauss–Bonnet turning-angle identity**, walked around the boundary:
   `Area = R²·(2π − Σ exterior turning angles)`. It never forms an interior triangle,
   so agreement with method 1 is a real check rather than the same arithmetic twice.

A spherical octant comes out at **exactly ⅛ of the sphere** under both.

### Why the planar shoelace was removed

The first cross-check used the planar "spherical shoelace" approximation,
`R²/2·|Σ(λ₂−λ₁)(2 + sinφ₁ + sinφ₂)|`. Anchored against closed forms it was wrong by:

- **a factor of two** on a spherical octant (pole-vertex degeneracy);
- **42 %** on the three-anchor triangle — 513,257 km² against the correct 299,098 km².

It was removed rather than kept as a weak second opinion. A regression test comparing
against previously-recorded output would not have caught this, so the area tests are
anchored to closed forms instead: the octant identity, and the requirement that a
spherical triangle exceed its planar Heron area (299,098 > 278,899 km² for the
anchors).

### Self-crossing polygons report no area

A ring that crosses itself has **no well-defined interior**. Printing a number for it
would be worse than printing nothing, so the area is withheld and the crossing edge
pairs are named. Great-circle segment intersection is tested directly, not approximated
in the plane.

### Vertex order matters

A polygon is defined by its vertex **sequence**, not its vertex set. The same points in
a different order enclose a different region, or none at all. Every record states which
ordering was used:

| value | meaning |
|---|---|
| `AS_SUPPLIED` | the order you gave, used verbatim |
| `REORDERED_BY_CENTROID_BEARING` | sorted by bearing from the centroid — produces a simple ring for star-shaped point sets |

Reordering is **offered, never applied silently**.

### Numerical conditioning, recorded

The fan triangulation privileges vertex 0, so rotating a thin sliver's vertex list
moves the area by **3.8e-9 relative** — under a square metre on 105 km². The turning
method walks the boundary and is **exactly** rotation-invariant. Both facts are
asserted by test rather than smoothed over.

---

## 4. The browser kernel

The polygon builder carries a JavaScript port of the V1 kernel — icosahedron vertices,
the `(F5+14)%20` face map, the 10/19 slerp refinement, and the pinned matrix `A` — so
any typed vector projects without a server round-trip.

That port is a **second implementation of the same law**, which makes it a liability
unless it is checked. `test_js_kernel_matches_python_exactly` runs the real page
JavaScript through a browser and fails if any known vector drifts by more than a
millimetre.

**Current drift: 0.000000 m on all seven known vectors.**

---

## 5. Basemap tiles and offline behaviour

Leaflet is **vendored** into `maps/vendor/`, so the pages need no CDN. Basemap tiles
are fetched from OpenStreetMap / Esri and **do** require network.

- A `file://` page **cannot** load the basemap. Serve the pages:
  `python -m r1053 serve`
- If tiles fail, the page shows a banner saying so rather than a blank pane. The
  markers, path, polygon and all measurements are computed **locally** and remain
  correct.
- Static PNG maps (matplotlib, no network) ship as offline fallbacks.

---

## 6. Reading the outputs

| field | meaning |
|---|---|
| `distance_km` | great-circle distance, cross-checked three ways |
| `cell_edges_depth9` | distance ÷ 14.989 km — the RGCS depth-9 cell scale |
| `area_km2` | exact spherical area for the vertices **as ordered** |
| `area_methods_agree_rel` | relative disagreement between the two exact methods |
| `area_is_trustworthy` | false if the ring self-crosses or the methods disagree |
| `is_simple` | no self-intersections |
| `centroid` | unit-vector mean of the vertices, back-projected |
| `branches` / `all_same_branch` | octal branch mix; `117` British, `120` North American |
| `coordinate_source` | where each vertex position came from |
| `vertices_are_verified_places` | **always false** |

Exports: GeoJSON, KML and CSV are written alongside the HTML maps, and
`certificate.receipt_bundle()` emits the full typed receipt set as JSON.
