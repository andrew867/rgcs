
# RGCS v4.8 R4 — Tetrahedral Spin-Addressed Codec: findings

**Status: SOFTWARE_VERIFIED, PHYSICAL_SPIN_UNTESTED.** No spin has been
written, read, or reset in any material. Quartz is BLOCKED. Every
physical gate in the stop matrix is open, and the programme continues
in simulation only.

## Gate Zero

Every claimed v4.7.1 fact was independently verified against the live
repository: tag commit `6b359c2`, main `341cd0b`, single post-tag sync
commit in ancestry, `enforce_admins` ON, 12 release assets, QA 19/19,
26 workbook sheets (remote workbook hash MATCH, R3 content verified by
cell values), 14 workbench panels. The reported 1153 tests reconcile
exactly: 1153 is the CI figure with `dist/` absent, and 1159 locally
where the 6 frozen-binary tests run instead of skipping.

## The exact answer, and what it is not

    64   = 8^2 = 4^3 = 2^6
    4096 = 8^4 = 4^6 = 2^12

Three quaternary symbols select one of 64 states; six select one of
4096. All 4096 keys round-trip through quaternary, octal and binary —
verified exhaustively, not sampled, because the space is finite.

**This contributes exactly zero compression.** The same twelve bits are
written in a different base. `refuse_radix_compression_claim()` raises,
and the benchmark carries a `RAW_QUATERNARY` baseline whose cost is
identical to flat binary by construction.

## Compression: what actually happened

Real compression must come from hierarchy, prototypes, residuals and
entropy coding, proven with **full bit accounting** (topology +
address + codebook + symbols + entropy model + residual) against fair
baselines. Two methodological defects were found and fixed while
running it:

1. **The rate-distortion curve swept only λ.** With the codebook pinned
   at k=16, fidelity saturated at the *codebook* bottleneck — 32
   distinct block values forced into 16 centroids gave an MSE floor of
   0.039 that no tree granularity could fix. A frontier must sweep
   every rate knob; the curve now sweeps λ **and** k, with a Pareto
   front.
2. **The HAL ablation pinned λ=1.0**, so the tree never split (the 265
   bits of child rate exceeded the distortion gain) and the study
   reported the payload variance as the codec's error. Same class of
   defect, same fix.

**The honest result after fixing both:**

| corpus | codec beats | notes |
|---|---|---|
| PIECEWISE_CONSTANT | flat float32, raw quaternary, uniform Q8, entropy Q8 | but **loses to zlib** (13049 vs 1624 bits) on exactly the data it is best at |
| SMOOTH_FIELD | nothing | uniform Q8 reaches MSE 8e-6; no codec point matches |
| SPARSE_EVENTS | nothing | |
| PHASE_RAMP | nothing | |
| RANDOM_UNIFORM (control) | nothing | correct |
| RANDOM_GAUSSIAN (control) | nothing | correct |

So: the hierarchy exploits blocky structure and beats quantizer
baselines there, is beaten by general-purpose DEFLATE on that same
data, and offers nothing on smooth, sparse or ramp payloads. **The
negative-control gate passes** — no gains on incompressible data,
which is what distinguishes structure exploitation from bookkeeping.

## Four states: the ontology that does the work

- **Four spin-1/2 directions are not four states.** The tetrahedral
  frame has pairwise overlap −1/3 and spans a 2-dimensional Hilbert
  space. `SICOutcome.as_storage_symbol()` raises: SIC outcomes are
  *informationally complete measurement statistics*, not memory. The
  frame identities (`n_i·n_j = −1/3`, `Σn_i = 0`, `Σn_i n_iᵀ = (4/3)I`)
  and the exact `p_i ↔ r` round trip are verified.
- **Spin-3/2 is the strongest native candidate** and its real
  limitation is recorded: common optical readout resolves |m_s| PAIRS,
  so the sign is ERASED. `optical_readout` returns an explicit
  `ERASURE` with 1 bit recovered, never a coin-flip; resolving the sign
  costs an extra operation that must be carried in the rate budget.
- **The write compiler refuses forbidden transitions.** Δm_s = ±1 only,
  so −3/2 → +3/2 has no direct pulse and compiles to three sequential
  allowed pulses.
- **Quartz is BLOCKED** with all ten stop-matrix gates open. The source
  narrative motivates the lane; it does not qualify the platform.
- **Classical four-domain cells are separated from the spin claim.**
  They carry quaternary symbols perfectly well and test the CODEC, not
  the hypothesis — which is why they are stage S0 of the bench.

## Bench: the honest stop

No apparatus exists, so **no stage is runnable** and the blocker is
explicit (`HARDWARE_SAFETY_BLOCKED`). The staging puts the cheapest
disqualifying test first (codec on a classical cell, no spin claim),
and compression-on-hardware (S4) is gated on standalone memory success
in S2/S3 per R48. Both protocols are preregistered with blinding,
fixed stopping rules, and — importantly — the four-state trial is
tested against the **50% pair-degenerate rate**, not just the 25%
chance rate, because resolving |m_s| alone is not four-state
discrimination.

## Release-process fix (R04/R65)

v4.6, v4.7.0 and v4.7.1 each needed a commit *after* the tag to sync
the committed workbook and manifest, so the tagged tree was never quite
the released tree. `tools/r4_release_gate.py` now refuses to let a tag
proceed unless the committed workbook matches a freshly generated one
and the committed manifest lists the current Windows-asset hashes. The
complete manifest (standard bundle + Windows assets) is generated at
publish time and uploaded — an upload is not repository content, so it
needs no commit. **v4.8.0 is the first release whose tag contains every
release-owned artifact.**

## What would change any of this

A calibrated four-state write/read/reset demonstration on a real
platform, under the preregistered protocol, with independent
replication. None exists.
