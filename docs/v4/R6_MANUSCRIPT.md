# RGCS v4.9 R6 — Results

**Dynamic Helicity, Quartz Magnetochiral Response, Metric-Indexed
Witness Memory, Recursive Barycentric Mailbox Routing,
Information-Carrier Transduction, and Planetary Grid Audit**

Software implemented. Physically untested. No coil has been wound, no
crystal driven, no clock compared, no spin written or read, and no
geophysical dataset has ever been loaded into this repository.

---

## 1. What R6 was asked to settle

The originating corpus proposes an apparatus (crossed windings on a
quartz crystal, pulsed, vertically oriented, with a collector) and an
architecture (a decaying probabilistic memory whose exact address is
clock-attested, addressed through nested celestial reference frames).
A model interpretation then described that architecture as a
relativistic witness, a distributed spacetime sensor network,
sovereign navigation, and a protocol authority.

R6's job was to translate each claim into something testable, model
the ordinary mechanism first, and state the strongest conclusion the
evidence could ever support.

## 2. The central correction

> A decaying memory is not automatically a spacetime sensor.

Payload relaxation has at least twelve ordinary causes: intrinsic
relaxation, temperature, magnetic field, electric field, strain,
radiation, vibration, chemistry, read disturb, manufacturing
variation, clock drift, detector drift. A common environmental cause
can move payload decay and clock phase *together*, so even an observed
correlation between them does not license the inference.

This is enforced in code rather than in prose. `r6.witness.
infer_proper_time_from_payload()` always raises — and still raises
when all twelve causes have been characterized, because
characterizing them does not make a payload into a clock.

The only supported route to a metric statement is a comparison between
two characterized oscillators across a declared transfer link.

## 3. Results

### 3.1 The witness channel is real, and the platform decides

Modelling a caesium-referenced pair against the 1 m gravitational
redshift (Δf/f = gh/c² = 1.09 × 10⁻¹⁶):

| Platform | Averaging | Outcome |
|---|---|---|
| Caesium beam, 1e-13/√τ | 86 400 s | `PREDICTION_BELOW_RESOLUTION` |
| Optical, 1e-16/√τ | 10 000 s | `RELATIVISTIC_SHIFT_CONSISTENT` |

The architecture is not what makes relativistic geodesy work; the
oscillator is. This is the single most defensible thing in the
programme, and it is defensible precisely because optical-clock
geodesy is already published, real work that R6 models rather than
claims.

A comparison is also refused promotion when its nuisance channels are
unrecorded, even if the arithmetic happens to agree — a defect found
and fixed during the run (R6-D-002).

### 3.2 The alternating drive is not what the source says it is

The corpus specifies interleaved pulse trains:

```
Copper 1-0-1-0-1-0
Silver 0-1-0-1-0-1
```

and claims that alternating the structure "empowers the torsion
field". Decomposed into common and differential modes under the
unipolar 0/1 mapping the source actually describes:

- purely differential fraction: **0.0**
- mean common-mode current: **0.5** (in units of drive amplitude)
- mean absolute differential current: **0.5**

Every active slot carries an equal common-mode component, so the
arrangement produces a net axial field at half amplitude. It is *not*
a purely differential drive. Only a bipolar mapping — where `0` means
driven the other way rather than off — is purely differential. Both
are modelled; the distinction is a wiring decision the source does not
make explicit and which changes the field qualitatively.

"Torsion field" has no instrument in R6, so no quantity can be said to
be empowered.

### 3.3 The three source frequencies are not significant

Against a null matched in granularity to the candidate set (distinct
integers in Hz, 100–2000 Hz, 20 000 draws):

- statistic: mean fractional detuning to the nearest computed mode
- random triples fit at least as well in **13 241 of 20 000** draws
- **p = 0.662**

For any laboratory-scale specimen (L = 0.1 m, fundamental 28.6 kHz)
all three frequencies fall *below the fundamental entirely* — the
audit is reporting the absence of an assignment, not a poor one.
Tuning the specimen until 1496 Hz is the fundamental requires a 1.9 m
quartz bar, and at that length p = 0.531. The result did not move
under tuning.

### 3.4 Sovereign navigation is unsupported, by linear algebra and by bookkeeping

Two independent refutations.

**Observability.** A local clock-rate measurement has a Jacobian
∂(Δf/f)/∂r = g/c², a single row against three position unknowns: rank
1, two degrees of freedom unobservable. The measurement is moreover
constant over an equipotential surface, so it cannot distinguish
points on one.

A correction worth recording: the first implementation used an
absolute rank tolerance and reported rank **0**, i.e. that a clock
carries no position information at all. That overstates the refutation
and contradicts published optical-clock height measurements. Fixed to
a relative tolerance (R6-D-003).

**Dependencies.** Every candidate signal-denied method retains
external inputs:

| Method | External dependencies |
|---|---|
| Inertial | initial position, velocity, attitude; gravity model; periodic external fix |
| Clock geodesy | second clock; transfer link; geopotential model; frequency standard |
| Gravity gradient | gradient map; survey data; attitude reference |
| Geomagnetic | IGRF/WMM; secular variation; anomaly map; space weather |
| Celestial | star catalogue; ephemerides; accurate time; line of sight |
| Terrain | elevation map; altimeter |
| Optical flow | visual map; scale from another sensor |

Zero methods are infrastructure-free. Every signal-denied technique
substitutes a catalogue, map, model, second clock or initial condition
for the radio signal it avoids. Verdict:
`SOVEREIGN_NAVIGATION_UNSUPPORTED`.

Fusion *can* make position observable — and the fused report inherits
the union of all those dependencies, which is the honest cost.

### 3.5 The mailbox names destinations; it does not reach them

Key paths use R4's exact 4096 radix; barycentric coordinates are
`Fraction`s so that "sums to one" is a fact rather than a
floating-point aspiration. Sun-centre and solar-system barycentre are
kept as **separate roots** with a time-dependent transform between
them, because they are physically different points — the barycentre
wanders by more than a solar radius as Jupiter orbits.

Asked for that offset, R6 refuses: it ships no ephemeris and will not
invent one.

A certificate can be fully valid, name a star, and still route only to
a local endpoint. `refuse_nonlocal_delivery()` enforces it. Writing a
destination into an address field is a string in a database.

### 3.6 The planetary grid audit ran, and could not produce a planetary result

R6 ships no gravity model, no geomagnetic snapshot, no topography.
Every audit therefore reports `NO_REAL_DATA`, and synthetic fields are
labelled as measuring the detector rather than Earth.

The machinery is nonetheless real, and getting it real was the largest
correction in the programme. The first implementation scored symmetry
through a dense "rotation-like" mixing that destroyed the very
subspace structure it then projected onto — so it could not detect
injected symmetry at **any** strength. It still returned "not
significant" on noise: a correct answer from a detector incapable of
any other answer (R6-D-004).

Replaced with genuine Wigner D-matrices and true projectors
P = (1/|G|) Σ_g D^l(g), group elements enumerated as unit quaternions.
The projectors independently reproduce the textbook lowest invariant
degrees — tetrahedral at l = 3, octahedral at l = 4, icosahedral at
l = 6 — which is the check that both the group enumeration and the
D-matrices are correct.

The audit is now calibrated: blind at zero injection, monotonic in
injection strength, significant only when genuine symmetric power is
present. Its controls are the point of the module: random rotations,
alternative groups, degree-matched random subspaces, a selection null
that repeats the *entire search including the orientation
maximization* on phase-randomized surrogates, and Holm–Bonferroni
across groups.

Becker–Hagens is carried as an overlay, never as a point group.
Archaeological site coordinates are held apart from geophysics, with
their confounds enumerated: rivers and harbours concentrate
settlement, trade routes follow terrain, arid ground preserves
selectively, funding biases discovery.

## 4. What R6 refuses to test

Nine biological and medical claims — DNA repair, chromosomes,
regeneration, reduced food requirements, chakras, gamma brainwaves,
bodily harvesting, water programming, disease treatment — are
registered as `REFUSED_NOT_TESTED` so the refusal is inspectable data
rather than an absence. No human or animal exposure, treatment,
diagnosis or therapeutic recommendation is permitted. A future
biological lane would require an independent medical and ethics
programme with institutional oversight.

There is no `PHRYLL_DETECTED` state, no
`SPACETIME_FABRIC_DIRECTLY_READ`, and no state above
`CANDIDATE_NEW_MECHANISM`. A test greps the package for each.

## 5. Corrections to the source corpus

| Claim | Correction |
|---|---|
| "epoch returned as the time of decay of the cesium clock source" | The SI second is the caesium-133 ground-state **hyperfine transition** (9 192 631 770 Hz). Caesium-133 is stable. No decay is involved. |
| "measure the electric charge in the photonic field" | Photons are electrically neutral. The implementable reading is collector charge. |
| "the etheric field is a torsion field in constant movement" | Used to dismiss a fixed critical angle, but motion does not remove a preferred angle — it adds rotation rate as a second axis. Both are modelled. |

## 6. Standing

Protocol maturity is `EXPERIMENTAL_SCHEMA`. There is one
implementation, one author, no independent governance body, no
adoption, no security review, and no patent or licensing review.
Authority follows adoption and governance; it is never asserted by
authorship.

Bench readiness: **5 of 10 gates open**, `ready_for_bench: False`. The
five shut gates — calibration plan, preregistration, safety review,
operator competence, data management — all require objects, people or
institutions that do not exist.

The cheapest genuinely informative next experiment is not the
apparatus. It is a two-oscillator comparison across a declared
transfer link: it tests the one component whose claim ceiling is
actually reachable, and it needs neither the coil, nor the crystal,
nor any of the contested geometry.
