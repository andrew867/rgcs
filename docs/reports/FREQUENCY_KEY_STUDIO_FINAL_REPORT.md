# Frequency Key Studio (RGCS Sonic Lab) — final report

## Branch / commit

`research/frequency-key-studio-v1`, branched from `main` at `9e80740`
(v8.4.0 + final-report docs commit). Final implementation commit: see
`git log` — services `5c7c378`, UI `8ba522b`, docs `c490b75`/`212c15d`,
demo assets `e97a444`, ingest fix `846bcad`, this report follows.

## Summary

Frequency Key Studio (RGCS Sonic Lab) added to Design Studio: an audio
creation and recipe system for binaural, monaural, isochronic, and
layered-noise sessions with frequency-key carriers, Gateway-style
staged shapes, and Hemi-Sync-inspired *independent* composites — plus
WAV/JSON/PDF/bundle export and a metadata-only web/video ingest parser.
No official recordings, tape structures, narration, or branding are
reproduced; there is no audio downloader (enforced by test).

## Changed files (grouped)

- **schemas**: `experiments/schemas/{audio_layer, frequency_session,
  render_receipt, source_recipe}.schema.json` + registry entries +
  2 example templates.
- **data**: `rgcs_desktop/data/frequency_key_studio_recipes.json`
  (7 seed recipes), `frequency_key_studio_beats.json` (11 beat
  targets) — packaged via the existing `rgcs_desktop/data` entries in
  package-data and both PyInstaller specs (no spec change needed).
- **services**: `rgcs_desktop/services/{sonic_audio, sonic_timeline,
  sonic_recipes, sonic_exports, sonic_ingest, sonic_cli}.py`; new
  console script `rgcs-sonic` in pyproject.
- **UI**: `rgcs_desktop/viewers/{frequency_key_studio,
  sonic_new_session, sonic_recipe_library, sonic_web_corpus}.py`; home
  card in `services/design_studio.py`; panel registered in
  `app/main_window.py` (21 panels; smoke expected-set updated).
- **docs**: `docs/user/{FREQUENCY_KEY_STUDIO, SONIC_SESSION_BUILDER,
  BINAURAL_COMPANION, RECIPE_LIBRARY, YOUTUBE_RECIPE_CORPUS}.md`,
  `docs/developer/{SONIC_AUDIO_ENGINE, SONIC_INGEST_PIPELINE}.md`,
  README start-by-task row, docs index rows.
- **tests**: `tests/unit/test_sonic_{audio, timeline, recipes, ingest,
  exports}.py`, `tests/integration/test_sonic_golden_path.py`,
  `tests/ui/test_frequency_key_studio.py`, smoke set update, docs
  guard update.

## Tests

```text
full suite (final tree):
  python -m pytest -q --deselect tests/regression/...::test_generator_deterministic
  -> 8410 passed, 9 skipped, 1 deselected, exit 0  (2129.31 s)
  (v8.4.0 baseline was 8362 passed)

focused: 41 unit + 1 integration golden path + 7 UI studio tests +
  updated smoke — all green.
UI smoke: 21 panels constructed OK; background job succeeded.
```

Key acceptance rows (10_TESTS/ACCEPTANCE_TEST_MATRIX):
T001 binaural 102/4 → 100/104 ✔ · T002 valid PCM WAV with expected
duration ✔ · T003 peak ≤ 0.95 (normalization recorded) ✔ · T004 all 7
seed recipes schema-validate ✔ · T005 PDF contains carrier, beat,
duration, receipt hash ✔ · T006 528 + 6.3 extracted from the fixture
title ✔ · T007 no audio downloader (source-level test) ✔ · T008 studio
panel navigation ✔.

## Demo artifacts (`docs/assets/design-studio/demo/sonic/`)

- `RGCS-SCH-0001.wav` — 20 s, 48 kHz 16-bit stereo, 925 Hz carrier /
  7.83 Hz beat over brown noise; peak 0.564, RMS 0.328, not normalized.
- `RGCS-SCH-0001_session_sheet.pdf` — session sheet with receipt hash.
- `RGCS-SCH-0001.recipe.json` — schema-valid, content-hashed.
- `RGCS-SCH-0001_youtube.txt` — title/description draft.
- `RGCS-SCH-0001_bundle.zip` — 4 members, checksums verified OK.

Screenshot proof: `docs/assets/design-studio/screenshots/
09_frequency_key_studio.png` (live app; an in-app wizard render also
executed and recorded in the workspace ledger).

## Recipe count

7 seed recipes (RGCS-BIN-0001, RGCS-GWY-0001, RGCS-AST-0001,
RGCS-SCH-0001, RGCS-FKY-0925, RGCS-FKY-1337, RGCS-ISO-0001) and 11
beat targets (1.5–33 Hz), each carrying its status vocabulary
(standard_band / source_patent / source_lead / candidate / project).

## Ingest parser results

The 9 planned corpus queries (08_WEB_YOUTUBE_INGEST) parsed as fixture
titles: 9/9 records, 0 errors, 9 frequencies with correct roles
(528/925/963/1337 → carrier candidates; 4/5/6.3/7.83 → beat targets),
claimed-use tags correct after fixing a real substring bug found during
this run ("aura" fired inside "binaural", "sleep" inside "asleep" —
now word-boundary matched with a regression test).

## v1.1 / v1.2 completion (second pass, same branch)

On user instruction the v1.1 and v1.2 scope was completed before
release:

- **v1.1**: live preview playback (QtMultimedia, optional backend with
  stated degradation; spec keeps QtMultimedia), STFT spectrogram
  preview, Timeline Editor page (custom segments replace the standard
  shape when enabled; refusals stated), voice-cue/music-bed WAV import
  with start offsets (16/24/32-bit PCM, linear resample), multi-carrier
  stacks, RMS loudness normalization (peak-capped, recorded), batch
  render (UI + `rgcs-sonic batch` + manifest).
- **v1.2**: corpus builder (URL-deduped JSON store + CSV export),
  duplicate clustering (frequency signature + title similarity), and
  deterministic recipe recommendation with reasons, all wired into the
  Web Corpus page.
- 31 additional tests (15 service + 16 UI). Layer-mixer-as-a-page was
  folded into the wizard's layer controls rather than a separate panel.

## Blockers / honest list

- LM Studio vision/classifier integration (feature matrix FKS-011,
  "later") and any live web search remain out of scope: the corpus
  page parses metadata the user supplies and performs no network
  access.
- The linear resampler for voice cues is adequate, not
  mastering-grade, and says so in code and docs.

## Boundary

Independent engine (DR-001). Metadata-only ingestion (DR-004). Every
session export carries: "Experimental audio recipe. Use comfortable
volume. Results vary." Claimed uses are recorded from sources or user
intent — they are not verified outcomes.
