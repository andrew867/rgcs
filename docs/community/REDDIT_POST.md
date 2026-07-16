# Reddit Post (r/opensource, r/Python, r/labrats — adapt title per sub)

**Title:** I spent a project making it *mechanically impossible* to
overclaim — a research framework where "hypothesis" is a compiler-level
label, several experiments are pre-registered to find nothing, and the
README opens with what ISN'T proven

**Body:**

The awkward part first: this project's questions come from crystal
folklore. A historical practice log full of specific frequencies,
timing recipes, and a special point inside the crystal called "the
eye." I know exactly how that sounds.

So the entire engineering effort went into making it impossible for
the project to fool itself (or you):

- Every scientific statement in the code carries one of five labels
  (Established / Derived / Hypothesis / Source claim / Engineering) as
  an actual decorator. The **test suite fails** if a function is
  missing one, or if a "solid" result is computed from unproven
  inputs. Overclaiming doesn't compile.
- "The eye" became eight competing measurable definitions, each with a
  pre-registered failure condition. Whichever survives measurement
  wins; whichever fails gets retired, in writing.
- The optical direction-dependence experiments are pre-registered
  **nulls**: standard physics says passive quartz is reciprocal, so
  the official prediction is "we will see nothing," with statistics
  (equivalence testing) to *accept* the null properly.
- The previous version is byte-frozen in the repo, and CI proves on
  every commit that the new math reproduces the old numbers wherever
  they overlap.
- Zero confirmed physics so far. That's in the README, the release
  notes, the manuscripts, and the citation file. There's a
  forbidden-vocabulary lint so nobody (including me) can sneak in
  therapeutic or free-energy language.

What you actually get: a tested Python framework (378 tests, 3-OS CI),
real anisotropic quartz acoustics (textbook Christoffel theory — with
a neat result where the old model's ±5 % fudge band turns out to be
exactly the physical anisotropy spread), lab-ready experiment schemas
with hard safety limits, and a full bench validation plan anyone can
run. Negative results are explicitly first-class contributions.

MIT licensed: https://github.com/andrew867/rgcs — the FAQ's first
question is "is this a fringe-physics project?" and I'd honestly
rather you read that answer than take my word here.
