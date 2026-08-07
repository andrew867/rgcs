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

## Exports

WAV · recipe JSON (schema-validated, content-hashed) · session PDF
(recipe, carrier/beat table, segment timeline, layer table, render
stats, receipt hash) · YouTube title/description draft · bundle zip
with embedded MANIFEST and checksums.

Music-bed and voice-cue file import is a v1.1 feature; those layers are
skipped with a statement, never silently.

Experimental audio recipes. Use comfortable volume. Results vary.
