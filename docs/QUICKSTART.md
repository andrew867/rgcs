# Quickstart

Five minutes from clone to a map on screen.

```text
The tool verifies geometry. It does not verify that a candidate vertex is
physically true.
```

---

## 1. Install

```bash
python -m pip install -e .
```

Python 3.11+. The map lane needs `numpy`; the interactive builder needs a browser.

## 2. Check it runs

```bash
python -m r1053 --help
```

```
{path,polygon,parse,map,certificate,serve,serve-maps}
  path         two-vector great-circle path map
  polygon      N-vector polygon: area, perimeter, centroid
  parse        structural receipt for one vector
  map          one-vector map
  certificate  typed address certificate
  serve        serve generated maps over loopback
```

## 3. Parse a vector

```bash
python -m r1053 parse 168930443
```

```
vector          168930443
lane            DIRECT_30BIT  (30-bit direct word)
binary30        001010000100011010110010001011
octal10         1204326213
branch          120  (North American)
F5 / Q22 / S3   5 / 144785 / 3   (S3 is the check digit, not geometry)
source face     19  = (F5 + 14) % 20
Q22 path        0 0 2 0 3 1 1 2 1 0 1
active label    Toronto hard anchor
V1 projection   43.653200, -79.383200
claim class     EXACT_ARITHMETIC, TRAINING_EQUALITY, NOT_EVIDENCE_FITS_THE_MAP
blockers        V1-B01, V1-B02, V1-B05
```

Note `TRAINING_EQUALITY`: Toronto is one of the three anchors that *define* the
projector, so it lands correctly by construction.

## 4. Draw a path between two vectors

```bash
python -m r1053 path 167849523 168930443
```

```
distance        178.846 km (11.93 depth-9 cell edges)
initial bearing 18.41 deg
midpoint        42.891736, -79.738486
cross-check     3 formulas agree: True (spread 2.67e-11 km)
map written     .../rgcs_path_167849523_168930443.html
```

## 5. Build a polygon from three or more

```bash
python -m r1053 polygon 165876523,165892743,165892763,165892783
```

```
vertices        4  (AS_SUPPLIED)
perimeter       77.330 km
area            105.268 km2
  cross-check   105.268 km2 (rel diff 7.19e-11)
centroid        51.282952, -1.970409
branches        117  (all same: True)
```

## 6. View the maps

A `file://` page cannot load basemap tiles. Serve them:

```bash
python -m r1053 serve
```

Then open <http://127.0.0.1:8791/> and pick a generated `.html`. Loopback only.

The polygon page is a **live builder** — type a vector and press Add, Remove any row,
reorder with Up, or press **Order by bearing**. Everything recomputes as you edit.

## 7. Run the tests

```bash
pytest tests/test_r1053_v1.py tests/test_r1059_docs.py tests/test_r1059_polygon.py -q
```

```
79 passed
```

---

## Try these

Example vector lists live in [`examples/`](../examples/):

```bash
python -m r1053 path $(tr '\n' ' ' < examples/path_erie_toronto.txt)
python -m r1053 polygon "$(paste -sd, examples/polygon_orange_stonehenge.txt)"
```

| file | what it shows |
|---|---|
| `vectors_basic.txt` | the seven known vectors |
| `path_erie_toronto.txt` | two fit anchors, 178.846 km |
| `path_toronto_drummondville.txt` | 582.465 km, Kingston–Montréal corridor |
| `polygon_orange_stonehenge.txt` | four branch-117 vectors over Wiltshire |
| `polygon_b01_contradiction.txt` | the same vector under two admissible pinnings |

---

## Next

- [User Manual](USER_MANUAL.md) — full walkthrough with screenshots
- [Map, path and polygon guide](MAP_PATH_POLYGON_GUIDE.md) — how the geometry is computed and checked
- [Claim boundaries](CLAIM_BOUNDARIES.md) — what is and is not verified
- [Blockers B01–B07](BLOCKERS_B01_B07.md) — the open problems, unsoftened
