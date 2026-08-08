# v8.5.2 Final Report — Frequency Studio UX, Curated AHA/Halo, CI/CD

Plan pack: `RGCS_v8_5_2_Frequency_Studio_Curated_AHA_Halo_UI_CICD_Spec_Tests_Plans_2026-08-08`
Date: 2026-08-08

## Release identity

| Item | Value |
|---|---|
| Release commit | `09481e0` (main) |
| Tag | `v8.5.2` (annotated; release notes from the tag message) |
| Release workflow run | `31277365003` (validate → create-release → windows/linux/macos) |
| Gate catch | run `31276782572`'s validate gate refused the first tag: the factory manifest was hashed from CRLF working-tree bytes while Linux checks out LF — factory data is now pinned `eol=lf` and re-hashed |
| Local full-suite gate | **8551 passed, 9 skipped, 1 deselected** (policy D-V3-04 byte-equality node), 0 failed |
| Curated sessions installed | **61** binaural sessions (+ 61 step-format variants remain in the plan pack, deferred) |

## What shipped

1. **Curated AHA/Halo factory library** (61 sessions: astral/meditation,
   Schumann, sleep, focus/study/memory, creative, relaxation/emotional,
   chakra/pineal, stress buckets) as package data with a per-file-hash
   factory manifest (`rgcs_desktop/data/factory_manifest.json`:
   factory_id, sha256, version, install_policy). Every session passes
   both gates (frequency_session schema + timeline check) and renders
   through the unmodified engine. Claim boundary: source-language
   claimed uses are recorded, not endorsed; no session is a medical
   claim, and disease/pathogen/drug programs were excluded upstream.
2. **Session CRUD** — `SessionStore` service + full UI: File menu with
   New / Open / Open Recent / Save / Save As / Close / Duplicate /
   Delete (to workspace trash, never hard delete) / Import; stable
   session identity across previews; dirty-state prompts
   (Save/Discard/Cancel) on session close and workspace
   open/switch/close; recent-sessions list in settings; Session
   Library page with factory/user origin badges (factory read-only,
   duplicate-to-edit).
3. **Workspace lifecycle** — `Workspace.open_or_create` ends the
   "workspace already exists" first-run crash; a failed open/create
   leaves the current workspace usable instead of a
   closed-but-referenced husk; factory content syncs on every open.
4. **Idempotent factory sync** — add_if_missing / update_if_unmodified
   (hash-compared against the recorded install hash) /
   never_overwrite_user_file / deprecated_hide; workspace state file
   `library/factory_state.json`; repair restores missing files;
   re-runs converge; user-edited and unrecognized files are never
   touched.
5. **Export type selection** — Frequency Studio writes only the checked
   kinds (recipe JSON, session JSON, WAV preview/full, session PDF,
   YouTube draft, bundle) with the expected-file list shown before
   writing; a single selection produces exactly one file.
6. **Phryll v1 retired / v2 single-artifact exports** — v1 removed
   from panels, home cards, golden path, and screenshot tool (geometry
   service + docs kept for legacy exports); v2 exports any one of 12
   artifact kinds (cone/sleeve STL, 3MF, SCAD; axial/top SVG; winding
   DXF; build/compatibility PDF; design receipt JSON) without a
   bundle.
7. **PDF rule fix** — the shared pdf_sheets writer drew section and
   table-header rules 3 pt above the text baseline (striking through
   the letters on every sheet). Rules now sit below the baseline;
   a regression test parses the content streams and asserts every
   rule is below its text; all committed demo sheets regenerated
   (phryll v2 demo bundle re-checksummed and re-verified).
8. **CI/CD** — the tag-triggered release workflow gained a `validate`
   job (full suite + leak firewall, mirroring ci.yml's ubuntu leg)
   gating create-release and all three build jobs. Assets build and
   upload automatically: Windows portable zip + per-user Inno Setup
   installer, Linux tar.gz, macOS tar.gz, each smoke-checked,
   manifested, and SHA-256'd. All builds unsigned per project policy.

## Generated release assets (uploaded by the automation)

- `rgcs-workbench-v8.5.2-windows-x64.zip` (+ `.sha256`)
- `RGCS-Workbench-8.5.2-Windows-x64-Setup.exe` (+ `.sha256`)
- `rgcs-workbench-v8.5.2-linux-x64.tar.gz` (+ `.sha256`)
- `rgcs-workbench-v8.5.2-macos-arm64.tar.gz` (+ `.sha256`)

## Workspace migration behavior

Existing workspaces (any version) gain the curated library on next
open: the sync adds `library/frequency_sessions/factory/
aha_halo_curated/` (61 files) and records install hashes in
`library/factory_state.json`. Files the user edited after install are
detected by hash mismatch and left untouched (reported as
`kept_user_modified`); pre-existing files the installer never wrote
are treated as the user's. Deleting a factory file and running
Repair Workspace restores it. Re-running first run against an
existing folder opens it instead of crashing, and never overwrites
the workspace manifest or user library.

## Known limits

- The optional Level 2/3 corpus features (full 22k-row searchable
  index + on-demand import) are deferred: the full `s2d_aha_halo.zip`
  corpus is not part of this pack — only the 61 curated selections
  (and their step-format `rgcs.frequency_session/v1` variants, which
  use a sequential-steps format the desktop engine does not render).
- Crystal Validator keeps its existing single-button export set
  (4 small files); per-type selection there was not in the acceptance
  tests and is unchanged.
- Custom timelines round-trip through the Timeline Editor table; a
  loaded session's segments always enter the editor as a "custom"
  timeline even if they match the standard shape.
- The committed sonic demo WAV stays a 20 s render — the full-length
  render is ~264 MB and exceeds GitHub's 100 MB file limit.
- Unsaved-changes prompts cover session close and workspace
  open/switch/close (per the CRUD spec); quitting the app saves
  layout but does not prompt for unsaved sessions.

Designs, estimates, and audio recipes are model outputs and
reproducibility records. Measurements decide.
