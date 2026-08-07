# Sonic audio engine (developer)

Modules under `rgcs_desktop/services/`:

- `sonic_audio.py` — numpy generators (sine, binaural/monaural/
  isochronic, seeded white/pink/brown/surf noise), constant-power pan,
  fades, the no-clip mixer (normalizes above 0.95 peak, records it),
  and 16-bit PCM WAV I/O via the stdlib `wave` module. 48 kHz float32
  internally; no new dependencies.
- `sonic_timeline.py` — 8 segment kinds, 4 ramp curves; beat ramps are
  phase-integrated so frequency transitions are click-free;
  `render_session` mixes beat layers + noise beds; unsupported file
  layers are skipped with a statement.
- `sonic_recipes.py` — packaged seed recipes/beat targets
  (`rgcs_desktop/data/frequency_key_studio_*.json`), recipe → session
  conversion using the standard shape, search.
- `sonic_exports.py` — schema-valid render receipts, session PDF via
  the shared `pdf_sheets` writer, deterministic recipe JSON, YouTube
  metadata sheet, bundle zip with embedded manifest + verification.
- `sonic_cli.py` — the `rgcs-sonic` console script (list / beats /
  render).

Schemas: `experiments/schemas/{audio_layer, frequency_session,
render_receipt, source_recipe}.schema.json`, registered in the shared
registry with example instances under `experiments/templates/`.

Determinism: noise is seeded; recipe JSON is canonical (sorted keys,
NaN-free) and content-hashed; WAV bytes are deterministic for a given
session dict.

Packaging: the data files ride the existing `rgcs_desktop/data` entries
in `[tool.setuptools.package-data]` and both PyInstaller specs.
