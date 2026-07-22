# RGCS v5.6.0 — Release Notes

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v5.5.0
**Licence:** MIT, unchanged. No relicensing.

R9: hidden neutral carrier feasibility, the omitted-antineutrino ledger,
segment-first CW decoding, the octave relation and the 1↔8 bridge, and
the vortex grammar.

Everything here is arithmetic, literature values, and software.
**No physical measurement was performed by this project.**

---

## Nothing in this release is novel

An adversarial prior-art review was run against every headline claim.
**Five for five came back established.** The vortex identification is
standard number theory; the ~202-octave figure is a two-constant
division published earlier; the beta-decay argument was settled between
1914 and 1934; the bench-neutrino infeasibility conclusion is decades
old; and the preregistration methodology is textbook.

The honest framing is **replication and correct exposition, not
discovery**, and the modules now say so in their own `novelty` and
`prior_art` fields rather than only in a review document.

## Results

- **A 100 g quartz crystal sees ~0.06 solar-neutrino interactions per
  year** — one every sixteen years. But the binding obstacle is prior to
  the rate: a quartz resonator has no channel that can register a single
  sub-keV recoil. NUCLEUS runs a **10 g** target, so the barrier is
  **readout, not mass**.
- **The CW vectors yield no recoverable content** in any of three
  framings. Their clustering is real and is reported under a separate
  verdict, so it can never be presented as a decoding.
- **The antineutrino cannot be omitted.** A two-body decay predicts a
  monoenergetic electron; the measured spectrum is continuous.
- **The vortex cycle is the multiplicative order of 2 mod 9**, and it is
  base-dependent — base 12 excludes nothing at all.
- **The octave is exact; "infinite" is true as arithmetic and false as
  physics** (~202 octaves fit between the physical bounds).

## Adversarial review found three tests that could not fail

The suite was green at 129/129. That was the problem.

The CW bit stage computed `agree - forced` with *forced* taken from the
sample's own min and max — which are members of the sample — so both
counters always stopped at the same bit. It returned **0 for every
possible input**, verified over 200,000 samples. The published claim
that three framings "could have disagreed and did not" was **false when
written**. Three further registered tests were gated behind a hardcoded
`informative=False` or bounded below the significance threshold.

Of eight advertised tests, **five can actually fire**, and the verdict
now says five. The register is audited for power against planted
structure.

Physics corrections: cross-sections were all multiplied by nucleon count
despite having three different denominators (the module reported inverse
beta decay in quartz, which has no free protons); the solar rate applied
a 1 MeV cross-section to a 0.267 MeV spectrum and was 10× high, now
anchored to Borexino; the Super-K validation asserted raw S/B > 1 and
was wrong in principle, since Super-K runs at ~10⁻⁴ and works by event
reconstruction; and "four independent conservation laws" is cut to the
honest two.

## Packaging defect affecting three prior releases

`pip install` of **v4.9.0, v5.0.0 and v5.1.0 shipped none of r6, r7 or
r8** — the headline research packages of those very releases. The
packaging `include` list stopped at `r4`, and working from a clone hid it
completely because `pythonpath = ["."]` makes the tree importable whether
or not packaging agrees.

The R8-D-006 coverage guard could not see it either: it detected packages
by the presence of `__init__.py`, and those were PEP 420 namespace
packages. Both are fixed and pinned by tests that compare the two lists
directly.

Anyone who installed r6/r7/r8 from PyPI-style installs of those tags
should reinstall from v5.2.0.

## Why v5.2.1 supersedes v5.2.0

`tests/v52/test_r9_packaging.py` imported `setuptools` at module level.
That is a build-system requirement, not a runtime or test one, and it is
absent from CI's portable job — so the module failed to collect on
ubuntu, macos and windows while passing locally, where the venv happens
to have it. **v5.2.0's CI is red for this reason.**

A packaging guard that cannot run in CI is not a guard, and this is the
same shape as the defect it was written to catch: something that works
from a developer's tree but not from a clean install. Declared in the
dev extra now, and imported via `importorskip` so a missing build tool
skips the file rather than erroring collection.

The v5.2.0 tag is immutable and stays as cut. All 10 CI jobs are green
at v5.2.1.

## Verification

```bash
git clone https://github.com/andrew867/rgcs && cd rgcs
pip install -e ".[dev]"
pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 3014 passed
```

The deselected node is a byte-equality test requiring the archived
v2.0.0 build environment (Python 3.11.15, numpy 2.4.4, scipy 1.17.1 and
its libm). Hosted CI deselects exactly that node id per policy D-V3-04;
its portable sibling `test_generator_numerically_equivalent` runs
everywhere.

## What this release does not claim

- No carrier was detected, and none was searched for. This programme
  owns no particle detector.
- The CW vectors are **not decoded**.
- No medical, biological, or consciousness claim of any kind.
- Nothing establishes that the source material's interpretations are
  correct. Where its arithmetic is correct, that is recorded; where its
  significance claims fail, that is recorded too.

CW vector provenance is kept at region granularity — *from the omega
region* — and no analysis step depends on it.

See [R9_FINDINGS.md](R9_FINDINGS.md) for the full analysis and the
complete defect log.
