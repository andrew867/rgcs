# RGCS v2 Desktop Workbench — User Guide

Launch: `python -m rgcs_desktop` (optionally pass a workspace directory:
`python -m rgcs_desktop ~/rgcs_workspaces/my-project`). The packaged
binary is `rgcs-workbench` (see `tools/packaging/`).

The window: **left** navigator (workspaces, specimens, models, experiments,
sources, results), **center** tabbed panels, **right** inspector (properties,
classification badge, units, provenance of whatever tab is active),
**bottom** jobs/log/warnings dock. Press **Ctrl+K** for the command palette.
Layout (dock positions, window size) persists between sessions.

Classification badges appear on every claim-bearing display:
green = Established, blue = Derived, amber = Hypothesis,
purple = Source claim. Purple banners mark content reproduced verbatim
from source material.

Screenshots: `docs/screenshots/` (main window, specimen editor, spectrum,
pulse designer, experiment builder).

## Workflow 1 — Create/open a workspace

1. Ctrl+K → "Workspace: create…" → pick a directory, name it.
2. A workspace is a folder: `workspace.db` + `sources/ artifacts/
   manifests/ backups/ reports/ bundles/`. Reopening automatically writes a
   db backup into `backups/`.
3. The last workspace reopens on launch.

## Workflow 2 — Import reference documents and register citations

1. **Sources** tab → *Import file…*. The file is copied under its sha256
   into `sources/`; the checksum is recorded and shown.
2. Select the source, fill in citation key (e.g. RG-04), title, origin and
   a classification note → *Register citation*.
3. Everything imported here is labelled **Source claim** until promoted by
   the evidence process — the panel says so. Drive presets from source
   material appear at the bottom under a Source-claim banner.

## Workflow 3 — Add a crystal or spiral geometry

1. **Specimen editor** tab. Crystal sub-tab: L, D_w, D_n, N_f, angles
   (defaults 51.843°/60° are flagged as Source claim), density,
   diameter/angle modes, optional measured node and measured mass
   (measured mass is required later for run manifests).
2. *Compute derived quantities*: mass, volume, node positions (the
   measured-node field blank → the display reads **"not measured"** — the
   geometry prior is used and labelled as such), axial half-wave rendered
   as `mean ± σ [lo, hi] (1σ)`.
3. Right side: 2D projection preview and the OpenSCAD export text.
4. *Save specimen to workspace* — it appears in the navigator and in the
   experiment builder's specimen list.
5. Spiral sub-tab works the same (q, T, R_0, H, p_z, Ω_s; path length,
   compact-radius priors).

## Workflow 4 — Compute spectra and coupled modes

1. **Compact-mode spectrum** tab: set f_b, u(f_b), v_chi and its relative
   uncertainty, compact radius (the 100 mm default is a placeholder, D-21),
   n_max, parity, zero-mode toggle → *Compute*. Modes plot with 1σ bands;
   κ_χ shows as an interval; the badge reads Hypothesis (H-01).
2. **Avoided crossing** tab: drag the g slider; the hybrid branches, the 2g
   minimum splitting and the strong-coupling ratio update live.

## Workflow 5 — Define drive and experiment

1. **Pulse designer**: choose the exact-cycle family (2261 / 1508 / 1131),
   read exact ms timings and the phase residue (defined on cycle counts
   only). Set `pulses per carrier period` explicitly — it is an assumption,
   not a fact. Source presets sit under the purple banner.
2. **Experiment builder**: run id, protocol branch, hypothesis ids,
   control role, specimen (from workspace), drive type/timing, acquisition
   (sample rate, duration, **n_runs**, drive-off time — the post-drive
   ratio is computed for you), data CSV (sha256 recorded automatically).
3. *Build + validate manifest*. Schema errors and gate results display
   immediately. For `human_loading` the ethics block (review reference +
   no-energized-contact confirmation) is a **hard gate** — the manifest
   cannot be saved without it.
4. *Save experiment* writes `manifests/RUN-….json` atomically and registers
   the experiment object.

## Workflow 6 — Import time-series data

Time-series CSVs stay on disk and are referenced by manifests with their
sha256 (attach in the experiment builder). To retain a copy inside the
workspace, import the file via the Sources tab as well. Sample data lives
in `experiments/sample_data/` (e.g.
`golden_coherence/case_c_decaying_sinusoid.csv`, columns t_s, I, Q).

## Workflow 7 — Run coherence/phase analysis as a background job

1. **Coherence analyzer**: browse to the CSV; give either I/Q columns or a
   real signal column; window/hop default to the golden analysis
   parameters (2 ms / 0.5 ms).
2. *Run analysis (background job)* — the job runs in a separate process;
   watch progress in the bottom dock; cancel there if needed. Failures are
   preserved as error artifacts (Results tab).
3. Plots: C_w **with its noise baseline** (C, window, baseline always
   reported together), amplitude, instantaneous phase. Inspector shows
   C max, phase linearity, onset/decay times, input sha256.
4. The result is stored as a content-addressed artifact and result object.
5. **Claim gate:** load the run manifest in the gate box. The
   "coherence-claim candidate" action stays disabled unless the manifest
   shows post_drive_ratio ≥ 2.5 **and** n_runs ≥ 100. Analysis itself is
   never blocked — only claim workflows.

## Workflow 8 — Compare controls / model vs measured

**Model vs measured** tab: model spectrum with 1σ bands, measured peaks as
a comma list with their measurement uncertainty. Each peak gets ε, u(ε)
and a resonance class (u_eps is mandatory and supplied for you); the badge
carries the "engineering heuristic - not evidence" note. Control-role
bookkeeping lives in the run manifests (control_role field per run).

## Workflow 9 — Generate report and reproducibility bundle

1. **Report / export** tab → *Generate markdown report*: software versions,
   all objects with classifications and checksums, job history, export
   history. Written to `reports/`, recorded in export history.
2. *Export reproducibility bundle*: a zip of workspace.db, sources,
   artifacts, manifests, reports plus `CHECKSUMS.json` (sha256 of every
   member, verified immediately after writing) and `VERSIONS.json`.

## Troubleshooting

- **Headless/CI:** set `QT_QPA_PLATFORM=offscreen`.
- **A job never finishes:** check the Warnings tab; a crashed worker is
  failed automatically and its traceback is saved as an error artifact.
- **"schema_version … refusing"**: the manifest was written by a newer
  major schema; upgrade the app rather than editing the manifest.
- **"exists with different content"**: intentional — the workbench never
  silently overwrites; re-save with overwrite where the UI offers it, or
  use a new id.
