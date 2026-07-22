# RGCS R10.6 — Vortex Key, Base-10 Unpacking, Crystal Memory: Findings

**Status:** `SOFTWARE_VERIFIED` · `PHYSICAL_VALIDATION_NOT_CLAIMED`
**Baseline:** v5.5.0 (`f733763`)
**Evidence class:** `DERIVED_MATHEMATICS` and typed source records.
**Hardware:** deferred. **No apparatus built, no crystal driven.**

---

## Gate Zero

Repository truth at v5.5.0 / `f733763`, tree clean, clean-clone 2948,
both package lists equal. Private corpus and delta: no remote, outside
the public worktree, firewall zero findings.

## Source authority (private)

`SRC_JH` (Jen Han) and `SRC_LS` (The L's) are registered as **Tier-A
private sources** in the private repository, each with the public alias
`OMEGA_REGION_SOURCE` and a SHA-256 provenance hash. Tier A means
faithful attribution, chronology, wording, and uncertainty — **not**
scientific verification, and dual classification (source authority *and*
evidence status) is preserved with no automatic promotion.

The twelve-word Vortex Opening Key and the private hypothesis delta are
preserved byte-for-byte in the private repository with provenance hashes.
**None of that appears in the public tree** — the names, the key words,
and the operator journal stay private; the public repository sees only
the region-level alias and the anonymized mathematics.

---

## "Unpack it from your base 10 system" → NO_DECODER_IDENTIFIED

**Module:** [`r10/base10.py`](../../r10/base10.py)

The clue specifies no codec, and the tempting move — read the digits as
octal — is refused: octal is not even well defined here, because the
vectors contain the digits **8 and 9**. So the clue is treated as a
*reversible-view search*, five views implemented, each round-tripping the
five twelve-digit vectors byte-for-byte:

| View | Output | Round-trips |
|---|---|---|
| A symbol-preserving | 12 decimal symbols | ✓ |
| B four decimal triads | 000–999 × 4 | ✓ |
| C three decimal tetrads | 0000–9999 × 3 | ✓ |
| D packed → binary | 40 bits (2³⁹ < 10¹² < 2⁴⁰) | ✓ |
| E binary-coded decimal | 48 bits, invalid nibbles rejected | ✓ |

**The result is `NO_DECODER_IDENTIFIED`, and the reason is structural: a
reversible codec relocates information, it cannot create it.** So the
test is view-independent, and it is the R9 lesson again. A full-band null
makes the shared "16287" prefix look striking (p = 0.0001) — but that
prefix is just the five vectors sitting in a narrow band, a fact about
their *range*. Against a span-matched null that reproduces the
clustering, **no residual content survives (p = 0.86)**.

Band clustering is real and reported separately; content is not there.
The verdict is `NO_DECODER_IDENTIFIED`, **not** `NO_DECODER_POSSIBLE` — a
codec keyed to material this search does not contain, or one prospectively
predicted and confirmed, would be a different result.

---

## The phase frames are exact; the ratio match is not (P05)

**Module:** [`r10/phaseframes.py`](../../r10/phaseframes.py)

All of it is exact rational arithmetic:

- 4096 = 2¹²
- 20.48 = 512/25 exactly
- periods 244.140625 µs and 48.828125 ms — exact dyadic values
- q = 925/4096 = 0.225830078125 exactly

**The one place honesty is load-bearing is the "ratio match."** The delta
notes q⁻¹ = 4096/925 = 4.428108… is *close* to 8300/1876 = 4.424307…,
and the pack is explicit that the residual must always be shown:

```
4096/925 − 8300/1876 = 1649/433825 ≈ 0.086%   (exactly, not rounded)
```

`refuse_exact_ratio_claim()` refuses to call the two an identity. **A
coincidence at one part in a thousand is a coincidence; small is not
zero.** This is the entire difference between "close" and "equal" — the
difference this project exists to keep.

Other frozen facts: a 200-tooth reluctance wheel at 4096 Hz turns at
exactly 1228.8 rpm; a 24-fold slate division is exactly 15°; 925√3 is
labelled inexact because √3 is irrational.

---

## A fading crystal memory is indistinguishable from ordinary relaxation (P09)

**Module:** [`r10/crystalmem.py`](../../r10/crystalmem.py)

A fading write-trace that decays and disperses is a typed *hypothesis*,
not a measurement. The model is honest arithmetic: amplitude decays as
`A₀·exp(−t/τ)`, the retention window is `τ·ln(A₀/threshold)` (for τ = 1 s
and a 1% threshold, **4.605 s**), and a shift register combines decay
with pulse-spreading dispersion. With dispersion, the last readable stage
is **42**; without it, **46** — so dispersion strictly costs four stages,
the falsifiable claim that this register is *worse* than a single cell.

**The firewall is the point.** A decaying trace is exactly what ordinary
material relaxation looks like — acoustic ringdown, thermal relaxation,
trapped-charge decay. The module makes this concrete: the memory model
and an ordinary-relaxation null have the **same functional form**, and
sampled over 65 stage-times their curves are **point-for-point identical
(max difference 0)**. A fit to the decay curve cannot prefer either.

The only thing that separates them is **ordered delayed readout** — the
data returning in the right order after a controlled delay. The
relaxation null returns a fixed monotone shape *independent of what was
written* (it carries zero bits), while a genuine memory returns the
pattern. `refuse_memory_claim_without_delayed_readout()` raises: a
decaying resonance is presumed ordinary relaxation until ordered readout
is demonstrated, and that demonstration requires a bench test that does
not exist. Status `BENCH_TEST_REQUIRED`, hardware deferred.

---

## What R10.6 does not claim

- No apparatus built, no crystal driven, no frequency generated.
- The vectors are **not decoded**; base-N unpacking exposes no content a
  matched null does not already produce.
- The ratio match is approximate and carries its residual; it is not an
  identity and confers no exactness on anything built from it.
- The frozen frequencies are not physically privileged — 4096 = 2¹² is a
  property of the radix.
- No named person and no source text appears in the public repository;
  the Tier-A names, the Vortex key, and the journal stay private.

## Not executed

The astronomy/route phases (P06 roots-first Sun/Earth/Moon/Mars,
P07 solar-emission centroid and slate photogrammetry, P08 density-layer
routing and phase-conjugate return), the apparatus phases (mechanical
generation, field solving, distributed pickup, blinded experiments), and
the holdout reveals (P14 — no future vector, slate angle, or emission
interval exists yet to reveal against) were not executed in this tranche.
Hardware remains deferred.
