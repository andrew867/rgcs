# RGCS v2 Desktop Workbench — Architecture

**Author:** Sub-Agent 05. **Date:** 2026-07-14.
Stack: PySide6 (Qt 6), pyqtgraph, SQLite (stdlib), multiprocessing (spawn),
jsonschema/referencing, PyYAML. `rgcs_desktop` depends on `rgcs_core`;
never the reverse.

## 1. Module diagram

```
rgcs_desktop/
├── __main__.py                 python -m rgcs_desktop
├── app/
│   ├── main.py                 entry point, --smoke-check, freeze_support
│   ├── context.py              AppContext: workspace + JobManager + settings
│   ├── main_window.py          docks, tabs, sidebar, actions, layout persist
│   ├── command_palette.py      Ctrl+K fuzzy action list
│   ├── inspector.py            properties/classification/units/provenance
│   └── jobs_panel.py           bottom dock: jobs table, log, warnings
├── workspaces/workspace.py     SQLite + files; atomic saves; backups;
│                               migrations; content-addressed artifacts
├── jobs/
│   ├── manager.py              JobManager (QObject; spawn processes; poll())
│   └── workers.py              worker functions (no Qt): trivial, failing,
│                               coherence_analysis, spectrum
├── services/                   non-UI logic (all unit-testable headless)
│   ├── formatting.py           UncertainValue/node rendering, badge colors
│   ├── schemas.py              loads experiments/schemas/validate.py by path;
│   │                           shared registry; major-version refusal
│   ├── gates.py                coherence-claim + ethics gates
│   ├── manifests.py            run-manifest builders
│   ├── scad.py                 OpenSCAD text export
│   ├── registry.py             model_registry.yaml reader
│   ├── report.py               markdown report
│   └── bundle.py               repro zip + verification
├── widgets/badges.py           ClassificationBadge, SourceClaimBanner,
│                               UncertainValueLabel
├── plots/uncertainty.py        pyqtgraph helpers (1σ bands)
├── viewers/                    13 Panel subclasses (one per tab)
└── settings/settings.py        QSettings wrapper
```

Dependency direction: `viewers → services/widgets/plots → workspaces/jobs →
rgcs_core`. Panels never touch SQLite directly; they go through `Workspace`.
`services/` and `workspaces/` import no Qt widgets (only `jobs/manager.py`
uses QObject signals), so all invariants are testable without a display.

## 2. Workspace store

One workspace = one directory:

```
workspace.db   SQLite: meta(schema_version, name), objects, files, jobs,
               export_history
sources/       imported files stored as sources/<sha2>/<sha256><ext>
artifacts/     content-addressed JSON artifacts (results AND errors)
manifests/     run manifests (RUN-<id>.json)
backups/       workspace-<ts>.db copy taken on every open
reports/       generated markdown
bundles/       reproducibility zips
```

Objects are JSON payloads with kind ∈ {specimen, model, experiment, source,
result, note, figure}; each row stores the sha256 of its canonical JSON
(`rgcs_core.provenance.sha256_of_jsonable`), so integrity is checkable and
"identical write" is distinguishable from "conflicting write".

### Data safety

- **Atomic saves:** every file write is temp-file-in-same-dir +
  `os.replace` (`atomic_write_text/bytes`); bundle zips finalize by rename.
  SQLite writes are transactional (`with conn`).
- **Backup on open:** `Workspace.open` copies the db to `backups/` before
  first use.
- **No silent destructive overwrite:** rewriting an object id with
  *different* content raises `WorkspaceError` unless `overwrite=True`;
  same for manifests. Identical content is a no-op.
- **Deterministic artifact ids:** `result-<sha256[:16]>` of the canonical
  JSON — same content, same id, same path; artifacts are immutable.
- **Checksums:** every imported file is stored under its sha256 and the
  hash is recorded in `files`.

### Schema migration

`meta.schema_version` (currently 1) is read on open. Newer-than-build →
refuse to open. Older → step through `_MIGRATIONS[from_version]` hooks
inside a transaction, bumping the row each step (hook table is present and
tested for the refuse path; no v0 legacy format exists yet, so the dict is
empty by design).

## 3. Background-job architecture

```
UI thread                      spawn process (per job)
─────────                      ───────────────────────
JobManager.submit ──────────▶  run_worker(worker_name, params, queue, job_id)
   │  QTimer(150 ms) → poll()      │ ctx.progress(f) / ctx.log(msg)
   │  drains one shared Queue  ◀───┤ ("result", jsonable) on success
   │  updates JobRecord            └ ("error", traceback) on failure
   ├─ job_updated / job_finished signals → panels, jobs dock
   ├─ result → workspace artifact (content-addressed) + result object
   ├─ error  → workspace *error artifact* (traceback + params + log)
   └─ cancel(job_id) → process.terminate() → status=cancelled
```

- **Spawn context** everywhere (Qt-safe on POSIX, required on Windows,
  compatible with PyInstaller via `freeze_support()` in `main()`).
- Workers live in `jobs/workers.py`, are module-level (picklable), import
  no Qt, and receive params as plain dicts — inputs are recorded verbatim
  in the job row, outputs become immutable artifacts (versioned by content
  hash); reruns with identical output converge on the same artifact id.
- `poll()` needs no event loop: the app drives it with a QTimer; tests call
  it directly (`JobManager.wait`). Dead processes without a result are
  detected via exit codes and failed with a preserved error.
- The UI thread performs no long calculation. Inline computations in panels
  (geometry, spectrum, two-mode algebra) are sub-millisecond closed forms;
  everything data-sized (coherence analysis) runs in a worker process.

## 4. Schema validation and gates

`services/schemas.py` imports `experiments/schemas/validate.py` **by file
path** and reuses its `build_registry()` — the desktop app and the QA gates
validate with the identical registry, including the `rgcs://` $id scheme
that does not URL-join (schemas are registered under bare relative names
too). The manifest gate order is: (1) refuse unknown major
`schema_version`, (2) JSON-schema validation, (3) UI gates
(`services/gates.py`): coherence-claim gate (post_drive_ratio ≥ 2.5,
n_runs ≥ 100 — blocks claim workflows, not analysis) and the human-loading
ethics gate (hard error).

## 5. Presentation invariants

- `format_uncertain` is the only path from `UncertainValue` to screen text;
  it always renders `mean ± σ [lo, hi] (1σ)`.
- `format_node_mm(None)` → `"not measured"`; NaN is treated as absent and
  can never render.
- `ClassificationBadge` maps the four policy labels to fixed colors; the
  right inspector shows the badge for whatever panel is active.
- Spectrum plots draw modes with `ErrorBarItem` 1σ bands; measured overlays
  are visually distinct (horizontal lines).

## 6. Testing

- `tests/ui/test_smoke.py` (13): window/panels/palette, trivial job through
  the queue, cancellation, failed-job error artifact, badge and interval
  rendering rules, claim gate, schema-major refusal, layout persistence.
- `tests/integration/test_vertical_slice.py` (10): the full scripted slice
  against real app objects, plus data-safety assertions.
- All run headless with `QT_QPA_PLATFORM=offscreen` (set in conftest).

## 7. Packaging

`tools/packaging/rgcs_desktop.spec` (one-dir; bundles experiment schemas +
validate.py, model_registry.yaml, policy docs). `build_linux.sh` builds and
smoke-checks the frozen binary — including a real spawn-based background
job inside the frozen executable. `build_windows.md` documents the Windows
procedure honestly (unverified: no Windows machine in this environment).
