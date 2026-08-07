# Sonic Session Builder (New Session wizard)

## Steps

1. **Type** — binaural, monaural, isochronic, noise bed, or composite.
2. **Carrier / frequency key** — the carrier family includes the RGCS
   frequency keys (925, 963.026, 1337, …) plus common audio carriers.
3. **Beat / modulation target** — chosen from the beat-target list;
   each entry carries its status (standard band, source patent/lead,
   candidate, project).
4. **Layers** — check noise/ambient beds (pink, brown, white, surf).
5. **Duration** — sessions follow the standard shape: fade in, settling
   period, cosine ramp to the target beat, hold, return/fade out.
   Minimum 10 seconds.
6. **Preview recipe** — the full session JSON with left/right
   frequencies shown live.
7. **Render WAV + export** — 48 kHz 16-bit stereo PCM, never clipped
   (the mixer normalizes above 0.95 peak and records it in the
   receipt).

## v1.1 features

- **Live playback** — "Play 12 s preview" renders a short session and
  plays it (QtMultimedia; if no audio backend exists the app says so
  and you can open the WAV in any player).
- **Spectrogram preview** — an STFT view (0–2 kHz) of the preview
  render, so you can see the carrier and beds before a full render.
- **Multi-carrier** — extra carriers (comma separated) stack additional
  binaural pairs on the same beat at lower gain.
- **Voice cue** — attach a 16/24/32-bit PCM WAV and a start offset;
  it is resampled to the session rate (linear; not mastering-grade).
  Music beds work the same way through session layers. A file layer
  without a file is skipped with a statement, never silently.
- **Loudness normalization** — normalize to a target RMS (dBFS);
  peak-capped at 0.95 and recorded in the render stats.
- **Timeline Editor** — edit segments (kind, duration, beat ramp,
  curve) directly; when enabled, your custom timeline replaces the
  standard shape. Invalid timelines are refused with the reason.
- **Batch render** — from the Recipe Library ("Batch render shown") or
  headless: `rgcs-sonic batch --duration 60 --out exports/`.

## Exports

WAV · recipe JSON (schema-validated, content-hashed) · session PDF
(recipe, carrier/beat table, segment timeline, layer table, render
stats, receipt hash) · YouTube title/description draft · bundle zip
with embedded MANIFEST and checksums · batch manifest for batch runs.

Experimental audio recipes. Use comfortable volume. Results vary.
