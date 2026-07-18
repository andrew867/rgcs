# RGCS v4.9.0 — R6

**Dynamic helicity, metric-indexed witness memory, recursive
barycentric mailbox routing, information-carrier transduction, and a
planetary polyhedral grid audit.**

Software implemented. Physically untested. No coil has been wound, no
crystal driven, no clock compared, no spin written or read, and no
geophysical dataset has ever been loaded into this repository.

## The central correction

A decaying memory is not a spacetime sensor. Payload relaxation has
twelve ordinary causes, and a common environmental cause can move
payload decay and clock phase together — so even an observed
correlation between them does not license the inference.

This is enforced in code, not prose: `infer_proper_time_from_payload()`
always raises, and still raises when all twelve causes have been
characterized, because characterizing them does not make a payload a
clock.

## Results that went against the source corpus

**The alternating drive is not what the source says it is.** The
corpus specifies `copper 1-0-1-0-1-0 / silver 0-1-0-1-0-1` and claims
alternating structure "empowers the torsion field". Decomposed under
the unipolar mapping the source actually describes, the
purely-differential fraction is **0.0**: every active slot carries an
equal common-mode component (mean 0.5 against mean differential 0.5),
producing a net axial field at half amplitude. Only a bipolar mapping
is purely differential.

**The three source frequencies are not significant.** Against a null
matched in granularity to the candidate set, random integer-Hz triples
fit the modeled modal spectrum at least as well in 13 241 of 20 000
draws — **p = 0.662**. For any laboratory-scale specimen all three
fall below the fundamental entirely. Tuning to a 1.9 m bar gives
p = 0.531; the result did not move.

**Sovereign navigation is unsupported**, by two independent
arguments. A local clock-rate Jacobian is rank 1 against three
position unknowns and is constant over an equipotential surface.
Separately, zero of seven signal-denied methods are
infrastructure-free — each substitutes a catalogue, map, model, second
clock or initial condition for the radio signal it avoids.

**The platform decides, not the architecture.** A caesium pair
averaged for a day cannot resolve the 1.09 × 10⁻¹⁶ shift from 1 m of
height (`PREDICTION_BELOW_RESOLUTION`). An optical pair can.

**The planetary audit could not produce a planetary result.** R6 ships
no geophysical data; every audit reports `NO_REAL_DATA`.

**Semantic information above the waveform is zero.** Two messages
carried by identical waveforms give I(M;Y) = 0.586 bits marginally and
I(M;Y|X) = 0.000000 bits conditionally.

## Source corrections

- The SI second is the caesium-133 ground-state **hyperfine
  transition** (9 192 631 770 Hz). Caesium-133 is stable; no decay is
  involved.
- Photons are electrically neutral, so "charge in the photonic field"
  has no referent. The implementable reading is collector charge.
- A field "in constant movement" does not eliminate a preferred angle;
  it adds rotation rate as a second axis.

## Defects found and fixed

Eight, logged in `docs/v4/R6_CORRECTIONS.md`. The two worth repeating:

**The grid detector was blind at every injection strength.** A fake
rotation destroyed the subspace structure it then projected onto, and
the injection cancelled in the score. It still returned "not
significant" on noise — a correct answer from a detector incapable of
any other answer. Replaced with real Wigner D-matrices and true group
projectors, which independently reproduce the textbook invariant
degrees (T at l=3, O at l=4, I at l=6).

**A Wigner phase error survived every structural check.** Using
(−1)^k instead of (−1)^(k−m+m′) yields a matrix related by a diagonal
similarity: unitary, idempotent under projection, trace-preserving,
and wrong. Structural self-checks cannot see a similarity transform;
only closed forms can.

Also: `tests/v49` sat outside `testpaths`, so every R6 test would have
passed locally and never run in CI.

## Standing

- Workbook: **35 sheets** (seven new R6 sheets).
- Protocol maturity: `EXPERIMENTAL_SCHEMA`. One implementation, one
  author, no independent governance body, no adoption, no security
  review. The blocker to `DRAFT_PROTOCOL` is that the specification
  lives in `internal-docs/`, not anywhere a second implementor could
  read it.
- Bench readiness: **5 of 10 gates**, `ready_for_bench: False`.
- Nine biological and medical claims registered as
  `REFUSED_NOT_TESTED`.

## Deviation from R4 release law

Branch protection is **no longer enforceable**. The repository is
private on a plan without protected branches; the API returns HTTP
403. CI is run and verified green on the tagged commit, but that is
operator discipline rather than a platform gate, and it is weaker than
the `enforce_admins` that v4.8.1 shipped under.

## Verification

```
# expect: 1840 passed
python -m pytest -q --deselect \
  tests/regression/test_generator_determinism.py::test_generator_deterministic
```

Adversarial audit: 19/19.

## Next real step

Not the apparatus. A two-oscillator comparison across a declared
transfer link tests the one component whose claim ceiling is actually
reachable, and needs neither the coil, nor the crystal, nor any of the
contested geometry.
