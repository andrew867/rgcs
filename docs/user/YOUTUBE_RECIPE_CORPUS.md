# Web / YouTube Recipe Corpus (metadata only)

The Web Corpus page turns public video/page **metadata** into
structured source-recipe records:

- frequencies extracted from titles and descriptions (Hz and kHz;
  100/104-style pairs also yield their difference)
- roles: carrier candidate (≥ 45 Hz), beat target candidate (< 45 Hz),
  description-only, ambiguous
- claimed-use tags from a fixed taxonomy (sleep, focus, meditation,
  astral projection, third eye, schumann, gateway-style,
  hemi-sync-inspired, healing claims, …)
- a recipe-type guess (binaural / monaural / isochronic / noise bed)

## What it never does

There is **no audio downloader** (decision DR-004, enforced by test).
The corpus records titles, descriptions, URLs, durations, and claimed
uses — claimed uses are recorded from source text and are not endorsed. Official Hemi-Sync tracks and reuploaded Gateway tapes are
out of scope entirely.

## Example

Title `528Hz + 6.3 Hz Astral Projection Binaural Beat` parses to
carrier candidate 528 Hz, beat target 6.3 Hz, claimed use
"astral projection", recipe type "binaural", status "source-language".
