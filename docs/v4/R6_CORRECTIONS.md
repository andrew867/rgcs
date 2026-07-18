# R6 Corrections and Defect Log

Defects found during the v4.9 R6 programme, and corrections applied to
source claims. Both are recorded because both are results.

## Defects found in the work itself

### R6-D-001 — `tests/v49` was outside `testpaths`

`pyproject.toml` pinned `testpaths` to an explicit list ending at
`tests/v4`. A new `tests/v49` directory is collected when named on the
command line but silently skipped by a bare `pytest` run — which is
what CI runs. Every R6 test would have passed locally and never
executed in CI.

Same failure family as the v4.8.1 workbook column loss: a mechanism
that reports success while covering less than it appears to.

**Fixed** by appending `tests/v49` to `testpaths`.

### R6-D-002 — `ComparisonResult.consistent` reported agreement from an untested comparison

`consistent` was a bare numerical check: `|measured − predicted| ≤ 2σ`.
It therefore returned `True` for a comparison whose witnesses were
uncalibrated or whose nuisance channels were unrecorded — a green light
by arithmetic coincidence from a comparison that had not put the
prediction at risk.

**Fixed**: agreement is reported only from a status meaning the
prediction was actually tested. Caught by my own test.

### R6-D-003 — navigation rank used an absolute tolerance, overstating the refutation

`_rank` used `tol = 1e-9`. A clock-rate Jacobian entry is `g/c² ≈
1e-16` per metre — physically meaningful and the entire basis of
relativistic geodesy, but far below that epsilon. The routine returned
rank 0 and the module reported that a clock carries *no* position
information at all.

That is wrong in the dangerous direction: it overstates R6's own
refutation and contradicts published optical-clock height
measurements.

**Fixed**: tolerance scales with the largest matrix entry. The honest
answer is rank 1 with two of three position degrees of freedom
unobservable.

### R6-D-004 — the planetary grid detector was blind at every injection strength

Two independent errors stacked:

1. `synthetic_field` injected symmetry by boosting *whole degrees*.
   The score is a power ratio *within* those degrees, so a uniform
   factor cancels exactly.
2. The rotation was a dense "Wigner-like" mixing rather than a real
   `D^l(R)`. It destroyed the subspace structure the audit then
   projected onto, so injected power was spread across all components.

Together these meant the audit could not detect a symmetry of any
strength. It still returned "not significant" on noise — a correct
answer produced by a detector incapable of any other answer.

**Fixed**: real Wigner D-matrices and real projectors
`P = (1/|G|) Σ_g D^l(g)` with group elements enumerated as unit
quaternions (`r6/wigner.py`), and injection performed *through the
projector*. The audit is now calibrated: blind at zero injection,
monotonic in strength, significant only when genuine symmetric power
is present.

### R6-D-005 — Wigner phase convention

The small-d sum used `(−1)^k` instead of `(−1)^(k−m+m′)`. The
resulting matrix is related to the correct one by the diagonal
similarity `S = diag((−1)^m)`, so it passed unitarity, idempotency,
and every invariant-dimension check while giving wrong individual
matrix elements.

Worth recording as a class: **structural self-checks cannot see a
similarity transform.** Only comparison against closed forms can.

**Fixed** and pinned against the textbook l=1 and l=2 entries.

### R6-D-006 — evidence classes and workbook fills are directly coupled

Registering the R6 Phryll-ladder rungs crashed workbook generation
with a `KeyError`: the dashboard indexes `EVIDENCE_FILL` directly, so
a class without a fill is a hard failure at generate time.

**Fixed** by adding the fills and a test asserting the two tables stay
in sync in both directions.

### R6-D-007 — `R6-SOURCE-FREQUENCY-AUDIT` was misclassified

Filed as `ORDINARY_CHANNEL_RESULT`, implying a channel measurement.
Nothing was measured; it is a statistic against a *modeled* modal
spectrum.

**Fixed** to `DERIVED_ARITHMETIC`.

### R6-D-008 — tests mutate tracked files (open)

Running the suite rewrites `docs/v4/baseline/*.json` and several
`evidence/v4/agent05/scratch/*.manifest.json` with the current branch
name and dirty-file list. `git status` is therefore dirty after any
test run.

Not fixed in R6. It is pre-existing, cosmetic today, but it is exactly
the kind of thing that will eventually make a release gate see a dirty
tree and either fail confusingly or be bypassed. Recorded so it is not
rediscovered a fourth time.

## Corrections applied to source claims

These are cases where the source corpus is wrong as stated. R6 records
the verbatim wording and the correction side by side rather than
silently reinterpreting.

### R6-C-101 — "epoch returned as the time of decay of the cesium clock source"

The SI second is defined by the caesium-133 ground-state **hyperfine
transition** frequency (9 192 631 770 Hz). Caesium-133 is stable;
there is no radioactive decay involved. "Time of decay of the caesium
source" describes no real process.

Implemented instead as a transition-referenced epoch with a declared
traceability chain.

### R6-C-008 — "anything that measure the electric charge in the photonic field"

Photons are electrically neutral, so "charge in the photonic field"
has no referent. The implementable reading is collector charge, which
is what the instrument actually measures.

### R6-C-007 — "the etheric field is a torsion field in constant movement"

Used in the source to dismiss Vogel's fixed critical rotational angle.
A field "in constant movement" does not eliminate a preferred angle;
it makes the response depend on rotation *rate* as well as angle. The
two claims are not alternatives. R6 models both axes.

## Null and negative results

These are findings, not failures.

| Claim | Result |
|---|---|
| R6-C-002 alternating drive "empowers the torsion field" | The source's unipolar 1-0-1-0 / 0-1-0-1 drive is **not purely differential**. Every active slot carries an equal common-mode component (mean common mode 0.5 vs mean differential 0.5, purely-differential fraction 0.0), producing a net axial field at half amplitude. Only a bipolar mapping is purely differential. |
| R6-C-006 the three source frequencies | **Not significant**, p = 0.662 against a granularity-matched null; random integer-Hz triples fit the modeled modal spectrum at least as well in 13 241 of 20 000 draws. For any laboratory-scale specimen all three fall below the fundamental entirely. Tuning the specimen to 1496 Hz (a 1.9 m bar) gives p = 0.531 — the result did not move. |
| R6-C-107 sovereign navigation | **Unsupported as absolute.** No examined method is infrastructure-free; every signal-denied technique substitutes a catalogue, map, model, second clock or initial condition for the radio signal it avoids. |
| Metric witness from decay | **Refused.** Twelve ordinary causes of relaxation; characterizing all twelve still does not make a payload a clock. |
| Caesium witness at 1 m height | **Below resolution.** A 1e-13/√τ beam averaged for a day cannot resolve 1.09e-16. Optical clocks can. The platform decides, not the architecture. |
| Planetary polyhedral symmetry | **No result possible.** R6 ships no geophysical data. The audit runs only on synthetic fields and always reports `NO_REAL_DATA`. |
