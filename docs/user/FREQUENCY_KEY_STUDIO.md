# Frequency Key Studio (RGCS Sonic Lab)

A local-first audio lab for designing, rendering, exporting, and
documenting binaural, monaural, isochronic, layered-noise, and
frequency-key sessions.

## Quick start

1. Open Design Studio (`rgcs-workbench`).
2. Choose **Make binaural / frequency-key audio**.
3. In **New Session**: pick a type (binaural), a carrier (e.g. 528, 925,
   or 1337 Hz), and a beat target (4, 6.3, 7.83, or 10 Hz).
4. Add pink noise or surf if desired.
5. **Render WAV + export** — you get the WAV, recipe JSON, session PDF,
   YouTube metadata sheet, and a checksummed bundle zip in the
   workspace's `exports/design_studio/sonic/` folder.

Example: carrier 925 Hz with beat 7.83 Hz plays left 921.085 Hz /
right 928.915 Hz.

## Headless renders

```bash
rgcs-sonic list
rgcs-sonic render RGCS-SCH-0001 --duration 60 --out exports/
```

## Pages

- **New Session** — the wizard: playback preview, spectrogram,
  multi-carrier, voice cues, loudness ([details](SONIC_SESSION_BUILDER.md))
- **Timeline Editor** — custom segment timelines with validation
- **Recipe Library** — seed recipes with search + batch render
  ([details](RECIPE_LIBRARY.md))
- **Session Library** (v8.5.2) — factory + user sessions in the
  workspace with origin badges; open, duplicate, delete-to-trash.
  Ships with 61 curated AHA/Halo-derived binaural sessions
  ([details](SONIC_SESSION_BUILDER.md))
- **Web Corpus** — metadata-only ingestion, corpus store, clustering,
  recipe recommendations ([details](YOUTUBE_RECIPE_CORPUS.md))

## Note

Experimental audio recipes. Use comfortable volume. Use stereo
headphones for binaural sessions. Results vary. Claimed uses are
recorded from sources or user intent — they are not verified outcomes.
