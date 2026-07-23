# CW Codebook V2 — Packed-Decimal / Mixed-Radix Codec

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** The second-generation reversible codec for the twelve-digit CW vectors, with exact packing, a null window, and a collision audit.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [COORDINATE_SPACE.md](COORDINATE_SPACE.md) (why a codec number is not a coordinate)
**Related code / tests / schemas:** [../../r10/cwcodec2.py](../../r10/cwcodec2.py), [../../r10/base10.py](../../r10/base10.py) (V1); tests/v52/test_r10_cwcodec2.py, tests/v52/test_r10_base10.py
**Known limitations:** This codec relocates information; it does not decode meaning. It carries forward R10.6's `NO_DECODER_IDENTIFIED`. No CW vector digits appear in this document. Nothing here recovers a message.
**Next review trigger:** An independently supplied padding rule for null positions, an independently supplied codebook, or any evidence a codec view beats a matched null.

## The premise, restated

    A reversible codec RELOCATES information; it cannot CREATE it.

V1 (`base10.py`) asked whether any reversible base-N *view* of the
twelve-digit vectors exposes structure a matched null does not. The
answer was **NO_DECODER_IDENTIFIED**. V2 does not re-open that question.
It hardens the machinery: it makes the packing, the mixed-radix layout,
and the injectivity **exact and auditable**, and it adds a discipline V1
lacked — a *null window*.

## Exact packing

- **40-bit packed decimal is minimal** for a twelve-decimal-digit value,
  because `2³⁹ < 10¹² < 2⁴⁰`. Thirty-nine bits cannot hold every
  twelve-digit number; forty can. The bound is arithmetic, not a choice.
- The layout offers a **4-bit header + 36-bit octal path** (twelve octal
  digits), an exact mixed-radix reframing with a declared inverse. Every
  bit out was already in.

A clean **round-trip is necessary but never sufficient** to claim a
decoding. The round-trip proves the frame is lossless and proves nothing
about content: a perfectly reversible codec over meaningless input yields
perfectly reversible meaningless output.

## The null window

When some digit positions are genuinely UNKNOWN, the honest
representation leaves them `None`. The null window keeps unknown digits
**NULL until a padding rule is independently supplied** — it never
invents a filler value to complete a pretty round-trip. Padding that is
not independently justified is the exact move this project exists to
refuse.

## Collision audit

The module audits injectivity: distinct inputs must map to distinct
codewords across the declared field ranges. A collision would mean the
"reversible" view is not reversible, and the audit fails loudly rather
than reporting a false round-trip.

## No retrofit

V2 does **not** retrofit V1's results or re-label the prior null result.
The reversible-view search concluded `NO_DECODER_IDENTIFIED`; hardening
the codec machinery does not change that conclusion. A better frame is
still just a frame.

See [COORDINATE_SPACE.md](COORDINATE_SPACE.md): even a perfect codec
output is not a position until it is bound to a frame, epoch, and
uncertainty.

PHYSICAL_VALIDATION_NOT_CLAIMED
