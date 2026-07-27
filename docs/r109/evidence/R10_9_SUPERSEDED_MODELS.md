# R10.9 Superseded Models Ledger

Preserved, retrievable, unusable in production. Machine-readable copy:
`R10_9_SUPERSEDED_MODELS_LEDGER.json`.

## 1. General affine canonicalization bridge (HISTORICAL_R10_8_AFFINE_CANONICALIZATION)

`y = (923*x + 550585316) mod 2^30`, inverse multiplier 953920147.
Origin: the archived Earth-alignment candidate (2026-07-26), where it
mapped variable-length payloads to compact packets
(`43789253 -> 165876523`, `72875493 -> 168930443`) and Montréal via
`165879243 -> 168500683`. Superseded because the source confirmed
`165879243` is itself a DIRECT compact packet (R109-MTL-01/02).
Historical replay still reproduces the archived arithmetic exactly but
only under the explicit profile id (`r109.superseded.historical_affine`);
production refuses it (`r109.codec.refuse_affine_bridge`), and a
regression test fails if that refusal is ever removed.

Retained note from the archive: `923 = 40*23 + 3` was logged as
retrospective arithmetic only, never used as proof.

## 2. Montréal transcription 168729543 (HISTORICAL_MONTREAL_TRANSCRIPTION)

The older Montréal wire value; V1's Montréal anchor. Preserved as
provenance (registry status SUPERSEDED, fit refused). Notable
preserved fact: its decimal terminal digit is 3 but its decoded S3 is
7 — kept visible by the shell-marker firewall.

## 3. Modulo-20 reserved-face promotion

The older face-folding reading ("`n % 20`; tokens 23, 43, 63, 83 all
select face 3", `cwatlas/r1082/decoder_candidates.py`) remains in the
frozen V1 candidate machinery for reproducibility, but the R10.9 typed
path refuses reserved-face promotion outright
(`refuse_reserved_face_promotion`); node 23 is a SIX-bit 64-state
selector, not a packet face (R109-FACE-01/03).

## 4. V1 Earth alignment (EARTH_ALIGNMENT_V1_LEGACY_CALIBRATED)

NOT superseded — preserved as the versioned legacy calibrated
candidate, byte-for-byte under `docs/r109/earth_v1/`, and still the
only fold-free operator. V2 documents the direct-Montréal tension; see
`R10_9_GLOBAL_DISTORTION_REPORT.md`.
