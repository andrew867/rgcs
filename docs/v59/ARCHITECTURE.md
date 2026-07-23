# Architecture — RGCS Software Layers

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** How the RGCS software is layered, and the discipline that binds it.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [START_HERE.md](START_HERE.md), [CURRENT_STATUS.md](CURRENT_STATUS.md)
**Related code / tests / schemas:** `rscs_core/`, `rgcs_core/`, `rscs2_core/`, `r10/`, `r7/`, `r8/`, `r9/`, `tests/`, `tools/`
**Known limitations:** This is a map of software modules only. No layer produces a physical measurement.
**Next review trigger:** A new core layer, or a change to the evidence-class or firewall discipline.

## Layered stack

The system is built bottom-up, each layer typed and provenance-checked:

- **`rscs_core/`** — the RSCS 1.0 typed-mathematics layer: relational coordinate
  records, typed roots with alias sets (retained, never silently collapsed),
  ordered reference-frame chains, periodic phase ambiguity, uncertainty, and
  provenance. Refusal is a first-class typed output here.
- **`rgcs_core/`** — the crystal-application layer built on RSCS 1.0.
- **`rscs2_core/`** — RSCS 2.0: the capability-aware multiphysics stack
  (anisotropic FEM + piezoelectric solver).
- **`r7/`, `r8/`, `r9/`** — earlier research packages (per-tranche investigations).
- **`r10/`** — the R9/R10 research modules (~50+ modules), each **defaulting to a
  refusal or a null**. Includes the firewalls (below).
- **`tests/`** — the verification suite (`v4`, `v51`, `v52` families and later).
- **`tools/`** — release tooling.

## Firewalls

Two firewalls enforce the public/private and safe/unsafe boundaries in code:

- **`r10/firewall.py`** — the **publication firewall**: private source material,
  session text, opening keys, and CW vector digits never enter the public tree.
- **`r10/claimfirewall.py`** — the **claim firewall**: dangerous source claims
  (alleged group-differential biology, medical predictions, financial tips) are
  preserved as source records and refused — held as UNSUPPORTED, never promoted,
  never acted on.

## Governing discipline

- **Evidence-class discipline.** Every result carries an evidence class. The
  software cannot emit a physical class — see [GLOSSARY.md](GLOSSARY.md) and
  [../../SCIENTIFIC_BOUNDARIES.md](../../SCIENTIFIC_BOUNDARIES.md).
- **No auto-promotion.** A claim never climbs to a stronger class on its own; a
  green suite does not turn a model into a measurement.
- **Nulls prove power.** A null result is only credible if the same code detects
  planted structure — see [DECISION_LOG_INDEX.md](DECISION_LOG_INDEX.md).

## What this architecture does not do

It does not drive hardware, emit signals, expose any human, or measure a
physical quantity. See [APPARATUS_ARCHITECTURE.md](APPARATUS_ARCHITECTURE.md).

PHYSICAL_VALIDATION_NOT_CLAIMED
