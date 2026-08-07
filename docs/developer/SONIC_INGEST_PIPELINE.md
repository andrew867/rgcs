# Sonic ingest pipeline (developer)

`rgcs_desktop/services/sonic_ingest.py` — metadata-only parsing:

- `extract_frequencies(text)` — Hz/hertz/kHz/kilohertz regexes plus
  100/104-style pair detection (the pair difference is added as a beat
  candidate); values deduplicated; roles assigned by band
  (< 45 Hz beat target, otherwise carrier candidate, ≥ 20 kHz
  ambiguous).
- `extract_claimed_tags(text)` — fixed taxonomy in
  `CLAIMED_USE_TAXONOMY`; tags are recorded claims, never endorsements.
- `parse_video_metadata(record)` — builds a schema-valid
  `source_recipe` record; title hits keep their roles,
  description-only hits are tagged as such; requires url + title.
- `parse_corpus(records)` — batch parse with URL deduplication and
  per-record error strings.

Boundary (DR-004, tested): no downloader. The module contains no
network imports — `tests/unit/test_sonic_ingest.py::
test_no_audio_downloader_exists` greps the source for them.

Pipeline position (plan 08_WEB_YOUTUBE_INGEST): search → raw metadata →
frequency extraction → claimed-use tagging → dedupe → review → recipe
seed conversion. The search and review stages are human/manual; this
module is the extraction core.
