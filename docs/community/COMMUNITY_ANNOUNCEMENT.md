# Community Announcement — RGCS v3.0.0 / RSCS 1.0

RGCS v3.0.0 is released, public, and entering its community-validation
phase: https://github.com/andrew867/rgcs

## What it is

A reproducible research framework for resonance studies in engineered
quartz geometries:

- **RSCS 1.0** — 17 typed coordinates + 23 operators with units,
  manifolds, provenance, and a machine-enforced claim firewall;
- **Crystal application** — anisotropic Christoffel propagation
  (which *explains* the old scalar model's ±5 % band as physical
  anisotropy), coupled modes, node menu, optical probe layer;
- **Experiment kit** — 13 JSON schemas, a binding low-energy safety
  envelope, ten-branch control matrices, seeded blinding;
- **Laboratory validation plan** — bench, calibration chain, and a
  per-hypothesis table (observable / expected / null / controls /
  confidence) for all 30 registered claims;
- **Four manuscripts** — every number generated from tested code;
- **CI evidence** — ubuntu/windows/macos × Python 3.11/3.13, green.

## What it is not

Not a confirmed effect. Not a healing-crystal project. Not a
free-energy project. **Nothing physical is confirmed**, several
directional hypotheses are pre-registered *nulls*, and the test suite
lints the vocabulary to keep it that way.

## Current evidence

Software and mathematics: machine-tested (378-test suite, conservative
extension verified against the frozen v2 baseline on every run).
Physics: the v2 bench work produced calibrations and registered
negative results; the v3 hypotheses await bench execution — the full
plan is in `docs/VALIDATION_PLAN.md`.

## How to contribute

- **Run the bench campaign** (or any branch of it) — negative results
  are first-class contributions.
- **Replicate the software claims** on your platform; portability
  reports welcome.
- **Build tranche T2+** (desktop panels over the tested services, FEA
  import, firmware) — see `CONTRIBUTING.md` and the contributor
  roadmap.
- **Steal the methodology** for your own project; that's what the MIT
  license is for.

Start at the README; the FAQ answers the first ten questions you'll
have, including "is this fringe physics?" (no — and here's the
machinery that keeps it that way).
