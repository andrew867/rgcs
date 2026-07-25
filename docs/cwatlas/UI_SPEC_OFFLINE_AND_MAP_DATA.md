# UI Spec — CW Atlas Offline Mode and Map-Data Strategy (P60)

**Phase:** T08 / P60 (Application, Documentation, and Release)
**Status:** SPEC. Offline mode and the tile/terrain data strategy are delivered
as an implementation specification for the P58 (2D) and P59 (3D) frontends
against the P57 backend service API. The engine is built and tested in
`cwatlas/`; no browser or tile-bundling code ships here.
**Depends on:** P58, P59, P57 (service), P02/P55 (privacy and export separation).

> `SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED`
> `PHYSICAL_VALIDATION_NOT_CLAIMED`

---

## 1. Scope and principle

The CW Atlas coordinate engine is **basemap-independent**. Every transform,
encode, decode, uncertainty, and refusal is pure arithmetic on declared
conventions in `cwatlas/`; **none of it needs a network, a tile server, or a
map image**. The basemap is only a backdrop for the operator's eye. This
document specifies how the app runs fully offline and how it sources map tiles
and terrain **without leaking a single private query**.

Governing principle: **no private data leaves the device.** A coordinate the
operator clicks or a vector they paste is a potentially sensitive input; the app
must never send it to a third-party tile server, an analytics endpoint, or any
remote host. Coordinate work is local; the basemap is the only thing that may be
remote, and only for public, non-identifying tile requests the operator has
opted into.

## 2. Two data planes — keep them separate

| Plane | What flows | Where it may go |
|-------|------------|-----------------|
| **Coordinate plane** | clicks, pasted vectors, addresses, decodes, receipts, exports | **device-local only** (the P57 service, run locally or self-hosted). Never a third-party host. |
| **Basemap plane** | raster/vector map tiles, terrain, hillshade | a configurable tile source, or a pre-downloaded offline bundle. Public, non-identifying requests only. |

The coordinate plane and the basemap plane must never be crossed: a tile request
must never carry a coordinate query parameter, a vector, a receipt, or any
device identifier. Tile URLs are of the form `.../{z}/{x}/{y}.pbf` — the tile
index, and nothing about what the operator is doing.

## 3. Offline mode

Offline mode is a first-class, testable state, not a degraded afterthought.

- **Coordinate operations are 100% available offline.** Map click → address,
  address → vector, decode canonical, decode legacy, alias sets, regions,
  heatmaps, refusals, URI build/parse, and GeoJSON/KML/CSV export/import all run
  against a **locally hosted** P57 service (or an in-browser WASM build of the
  same tested `cwatlas` functions). No feature that produces a coordinate result
  requires a network.
- **The basemap degrades gracefully.** With no network and no offline bundle,
  the globe/map renders a neutral graticule (a plain lon/lat grid on the selected
  body's ellipsoid) instead of imagery. Pins, polygons, regions, and heatmaps
  still render on the graticule; the receipt is unchanged. The UI shows a small,
  honest "basemap unavailable — coordinate engine fully operational" notice.
- **An explicit offline toggle** disables all outbound basemap requests. When on,
  the app makes **zero** network calls beyond the local service origin.

## 4. Offline map-data bundle

For field use the operator may pre-download a basemap bundle:

- **Format** — MBTiles or PMTiles (a single self-contained tile archive), plus an
  optional terrain-quantized-mesh set for the 3D globe (P59).
- **Provisioning** — the bundle is downloaded and placed on the device **once, by
  the operator, from a source they choose**. Downloading a bundle is an explicit
  operator action (it is a file download); the app does not fetch bundles
  silently.
- **Serving** — the local P57 service (or a local static file server) serves tiles
  from the bundle. Tile requests stay on the device origin.
- **Scope selection** — the operator picks the geographic extent and zoom range to
  bundle. The extent is a public region selection, not a coordinate result, and
  is never derived from a pasted private vector.

## 5. Tile sources and licensing

The app ships **no** basemap by default; the tile source is **configured by the
operator**. The configuration UI must:

- require an explicit, operator-entered tile source URL or a selected offline
  bundle — there is no baked-in default provider;
- display the **attribution and licence** required by the chosen source
  (e.g. an ODbL/OSM-derived source needs its attribution shown on the map), and
  keep that attribution visible;
- record the chosen source and licence in the app's settings so an exported
  screenshot or bundle can carry correct attribution;
- warn if a source's terms forbid offline caching before enabling a bundle for
  it.

Licence compliance is the operator's responsibility for the source they choose;
the app's job is to make the source, its terms, and its attribution **explicit
and visible**, never hidden.

## 6. No telemetry, no tracking

- **No analytics, no telemetry, no crash-reporting-to-remote** by default. The app
  ships with these **off and with no endpoint configured**.
- **No coordinate ever enters a URL or query string** sent off-device (this
  mirrors the privacy rule in `cwatlas/privacy.py` and the export separation in
  `cwatlas/export_separation.py`). A tile request carries only `{z}/{x}/{y}`.
- **No third-party fonts, sprites, or CDN assets** that would beacon the
  operator's presence; the app bundles its own fonts and glyphs.
- **The CW URI is share-only and local.** `share.format_cw_uri` builds a
  `cw://…?frame=…&epoch=…` string for the operator to copy; the app never
  transmits it anywhere on its own.

## 7. Privacy boundary at the network edge

The frontend must enforce, at the fetch layer, an allowlist:

- the **local P57 service origin** (coordinate plane) — always allowed;
- the **operator-configured tile origin** (basemap plane) — allowed only for
  `{z}/{x}/{y}` tile paths, and only when offline mode is off;
- **everything else** — blocked.

Any attempt to send a coordinate, vector, receipt, or device identifier to a
remote host is a bug, not a feature. Exports are produced **on device** and go
only where the operator saves them; they pass
`export_separation.build_public_export` / `assert_export_clean`, which refuse a
record that scans as private (`privacy.refuse_private_in_public`). All fixtures
and examples in the app are synthetic.

## 8. Degradation matrix

| Condition | Coordinate engine | Basemap | UI behaviour |
|-----------|-------------------|---------|--------------|
| Online, source configured | full | imagery/vector tiles | normal |
| Online, no source configured | full | graticule | prompt to configure a source |
| Offline, bundle present | full | bundled tiles | normal, no network calls |
| Offline, no bundle | full | graticule | "basemap unavailable — engine operational" |
| Offline toggle on | full | bundle or graticule | zero outbound requests beyond local origin |

The coordinate engine column is **"full" in every row**. That is the point: the
science of the atlas never depends on a map image.

## 9. Non-claims

- A rendered basemap is a **backdrop**, not evidence; drawing a pin on satellite
  imagery does not make a source vector's location real.
- Offline availability is about **privacy and field robustness**, not about any
  physical or extraordinary capability.

## 10. Acceptance (spec-level)

- All coordinate operations function with the network fully disabled.
- No coordinate, vector, or receipt ever appears in an off-device request.
- Tile requests carry only `{z}/{x}/{y}`; a fetch allowlist blocks all other
  origins.
- The basemap degrades to a graticule without breaking any coordinate result.
- Tile source, licence, and attribution are operator-configured and visible.

```text
GREEN_R10_8_1_P60_OFFLINE_MODE_AND_MAP_DATA_STRATEGY (SPEC)
```
