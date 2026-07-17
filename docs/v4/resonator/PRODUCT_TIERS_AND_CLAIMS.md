# Product platform, calibration tiers, and claims (Agent P01)

An honest product architecture. Each tier's permitted claims are tied
to the evidence that tier actually carries — and the certificate
schema enforces the wording (`certificate.py` refuses out-of-band
acceptance and lists claims-not-made in every document).

## Tiers

### Tier 0 — Decorative geometry
Objects generated from the RGCS geometry families with **no
measurement of any kind**.

- Permitted: "generated from a logarithmic-spiral / cymatic-disk
  design", dimensions, material.
- Required wording: **"decorative; no measured or implied resonance
  properties."**
- Forbidden: any frequency number at all. A target frequency on a
  decorative object reads as a measured one; that confusion is the
  whole reason tiers exist.

### Tier 1 — Engineering-calibrated resonator
A physical object that has been through the closed loop: fixtured,
measured, (optionally) trimmed, verified, certified.

- Permitted: the certificate contents — fitted frequency with
  uncertainty, Q, acceptance band, trim history, fixture and
  environment at measurement.
- Required wording: "frequency as measured under the stated fixture
  and environment; changes with mounting and temperature."
- Forbidden: therapeutic, wellness, consciousness, or energy claims
  (the certificate's `claims.not_made` list, printed on the
  document).

### Tier 2 — Research specimen
Objects entering preregistered studies.

- Permitted: everything in Tier 1 plus study participation records.
- Required: chain of custody, immutable raw data, preregistration id.

## Targeted is not measured

The load-bearing distinction of the whole platform (R005): a design
FREQUENCY TARGET is an intention; a MEASURED frequency is an event;
a FITTED frequency has an uncertainty; an ACCEPTED frequency passed a
preregistered band. Product copy may only use the strongest word the
record supports. **No physical RGCS object exists today, so no
product copy above Tier 0 is currently supportable — and Tier 0 copy
must say "decorative".**

## Symbolism policy

Symbolic/aesthetic meaning is real to people and may be described AS
symbolism ("inspired by", "in the tradition of"). The boundary:
symbolic language may never borrow measurement language ("tuned",
"calibrated", "resonant with") unless the certificate substantiates
the physical sense of the word.

Status: policy document, binding on any future product copy;
enforced at certificate level in code, at claim level by the Q07
wording audit.
