# Continuity Handoff — Bus-Factor-Zero Successor Guide

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** everything a clean-room successor needs to continue RGCS with no prior context, no chat logs, and no living author.
**Last verified commit:** v5.8.0 baseline (branch `v580-r10-10`).
**Prerequisites:** none — this is the entry point for a successor.
**Related code / tests / schemas:** [`r10/continuity.py`](../../r10/continuity.py), [`tests/v52/test_r10_continuity.py`](../../tests/v52/test_r10_continuity.py); release tooling `tools/v4x_release_metadata.py`, `tools/r4_release_gate.py`.
**Known limitations:** this document proves *what* a successor must be able to do; it cannot prove a specific human has done it, nor that off-repository backups exist. Nothing here is a physical measurement.
**Next review trigger:** any new tranche, any change to the release ritual, or any change to the public/private boundary.

---

## What RGCS is

An open, evidence-governed research framework that takes unusual source
material (personal/"lore" input) and translates each claim into **typed,
refutable software whose default output is a refusal or a null**. The
project's standard: *it appears possible — can it be proved, measured,
implemented, or honestly refused?* So far, for every physical claim, the
answer has been **refused** or **unmeasured**, and those results are the
bulk of the output.

## Established vs source-derived

- **Established / historical fact:** the postwar quartz-growth patent
  timeline (Brush, Clevite, Bell Labs) — see
  [QUARTZ_PATENT_HISTORY.md](QUARTZ_PATENT_HISTORY.md); conventional
  physics (nonlinear optics, Allan deviation, transmission lines).
- **Source-derived (hypotheses only):** that natural geological quartz is
  "required", the CW vectors, the 925 Hz / 13 MHz / 1604 / 1644 cues, the
  handshake. All are `SOURCE_CLAIM` / `SOURCE_REQUIREMENT`, none is
  promoted to evidence.

## Implemented vs modeled vs measured

- **Implemented and tested:** every `r10/*.py` module (software).
- **Modeled, not built:** all apparatus, benches, and experiments.
- **Measured:** **nothing.** No apparatus exists; hardware is deferred;
  `PHYSICAL_VALIDATION_NOT_CLAIMED` everywhere.

## The public/private boundary

The public repository carries verified history, math, software, nulls,
and documentation. A separate **private repository** (0 remotes, outside
the public worktree) holds raw Tier-A source text, personal journal and
location material, and the private interpretations. The publication
firewall [`r10/firewall.py`](../../r10/firewall.py) scans the committed
public tree; it must report zero findings before any release. Never place
personal names, private localities, the private repository's directory
name, or raw source text in the public tree.

## The exact next command

```bash
git clone https://github.com/andrew867/rgcs && cd rgcs
python -m venv .venv && . .venv/Scripts/activate   # Windows; use bin/ on POSIX
pip install -e ".[dev]"
pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
```

## Ten unresolved questions

1. Does natural geological quartz differ from hydrothermal synthetic on
   any ordinary endpoint, once trace elements/inclusions/water are
   controlled? (Untested — no specimens.)
2. Is there any preregistered codec under which the CW vectors carry
   content a matched null does not already produce? (None found.)
3. Do the 1604 / 1644 cues resolve to anything beyond arithmetic? (No —
   `NO_BETTER_THAN_CHANCE`.)
4. Can any prospective holdout (signal, EMI, sky, market) be scored, ever,
   in this environment? (Not yet — all `AWAITING_OUTCOME`.)
5. What would a real bench measurement of acoustic Q vs. provenance show?
6. Is the 925 Hz / 13 MHz relationship physically meaningful or a numeric
   coincidence? (Exact closures are arithmetic, not physics.)
7. Can hosted CI be restored (Actions minutes)? Until then the local
   suite is the gate.
8. Which of the 30 required public documents remain to be written? (See
   [DOC_SET_STATUS.md](DOC_SET_STATUS.md).)
9. Are there off-repository, geographically separate backups of the
   private archive?
10. Who, if anyone, has actually executed the successor drill end to end?

## The successor drill

Run the clean-room drill in [`r10/continuity.py`](../../r10/continuity.py)
(`successor_checklist()`): clone → environment → tests green → regenerate
docs → locate the private boundary → reproduce one null → commit one valid
change → restore an archive and verify it against its manifest. If any
step needs knowledge from a person's memory or a chat log, the drill has
failed and the gap must be documented here.

`PHYSICAL_VALIDATION_NOT_CLAIMED`
