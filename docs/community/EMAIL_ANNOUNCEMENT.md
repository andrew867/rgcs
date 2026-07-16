# Email Announcement (colleagues / mailing lists)

**Subject:** RGCS v3.0.0 released — reproducible resonance-research
framework with pre-registered falsification plan (MIT)

Hi all,

I've released RGCS v3.0.0, an open-source framework for resonance
research in engineered quartz geometries, now public and entering
community validation:

  https://github.com/andrew867/rgcs

In one paragraph: it's a typed, provenance-checked mathematics library
(17 coordinate types, 23 operators, machine-enforced claim
classification) plus a crystal application (anisotropic Christoffel
elastodynamics, coupled modes, an optical probe layer), safety-bounded
experiment schemas, a complete bench validation plan for its 30
registered hypotheses, and four manuscripts whose every number is
generated from tested code. The previous version is byte-frozen in the
repository and CI proves the new mathematics reproduces it wherever
they overlap.

Being upfront: none of the project's physical hypotheses is
experimentally confirmed — several are pre-registered *nulls* — and the
project states this everywhere. What I'm sharing is the framework and
the falsification plan, plus a methodology (claim labels as a type
system, frozen baselines, equation-level provenance) that I think
transfers to other research-software projects.

Where you could help, if inclined:
  • criticize the pre-registered statistics plan BEFORE bench data
    exists (docs/VALIDATION_PLAN.md) — that's the window where review
    is most valuable;
  • replicate any bench branch (docs/LAB_MANUAL.md) — negative results
    are first-class and get registered;
  • portability reports from platforms beyond the CI matrix.

Suite: 378 tests, ubuntu/windows/macos CI green. License: MIT.
Citation: CITATION.cff in the repo (Zenodo DOI to follow).

Questions and criticism very welcome — the FAQ handles the obvious
ones, including the one you're probably thinking.

Best,
Andrew
me@andrewgreen.ca
