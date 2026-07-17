# Closed-loop resonator platform (Agents R01–R11)

Coverage: **R001–R104** (all R-lane IDs). Package:
[`resonator_platform/`](../../../resonator_platform/). Tests:
[`tests/v4/test_resonator_platform.py`](../../../tests/v4/test_resonator_platform.py)
(42 tests).

**Everything this platform has ever produced is synthetic.** No board
has been fabricated, no fixture machined, no laser exists, no
measurement taken. The synthetic flag is structural: it rides on the
ledger, every event, every session file, and every certificate,
including the QR payload.

## The loop (R01, addendum §1)

    DESIGN -> SIMULATE -> FABRICATE -> FIXTURE -> EXCITE -> MEASURE
    -> IDENTIFY MODE -> SELECT TRIM -> ABLATE -> VERIFY
    -> ACCEPT OR ITERATE

Implemented as a state machine with no force flag
(`records.Lifecycle`); every transition is a ledger event; illegal
transitions raise. `TRIM_EXECUTED` can only return to `FIXTURED` —
**you cannot measure without remounting, and you cannot accept
without a held-out verification.**

## The four frequencies (R005)

`predicted` (model) / `measured_peak` (raw grid) / `fitted`
(line-shape + uncertainty) / `accepted` (passed the preregistered
band). Four fields, constructor-enforced: accepting a prediction
raises. This is the platform's version of the targeted-vs-measured
rule, and every downstream document inherits it.

## The ledger (R004)

Append-only, hash-chained, deep-copied in and out. `verify()`
recomputes the chain; deleting or editing an event raises; tampering
with internals breaks the chain detectably. History is the evidence.

## The demonstration campaign (R008)

One run of `campaign.run_campaign()` exercises everything:

    predicted 1030.15 Hz -> preregistered target 1036.15 ± 3 Hz
    -> 2 trim iterations (symmetric pairs, dry-run executed on the
       twin with execution noise)
    -> guards evaluated after each trim
    -> held-out remeasure -> ACCEPTED at 1035.04 Hz
    -> signed certificate, 32-event intact ledger

Deterministic per seed; 12/12 seeds complete or guard-trip (both are
legal outcomes — a `GuardTripped` stop is the system working).

## Guards and irreversibility (R05, R040)

- Approval tokens bind operator + specimen + exact cell set.
- Physical execution additionally requires a **registered machine
  capability**, and registration requires fume-extraction and
  interlock evidence (S01: FR-4 fumes are genuinely hazardous). No
  machine is registered; the physical path is unreachable, which is
  the true state of the lab.
- Overshoot is treated as unrecoverable: the selector refuses any
  candidate whose predicted landing passes the target by more than
  half the band. Undershoot costs another iteration; overshoot costs
  the part.
- `check_guards` stops on mode loss, overshoot, or a realized shift
  inconsistent with prediction (sensitivity model wrong → stop, learn,
  do not retry blindly).

## Bidirectional and reversible tuning (R06)

Removal raises this family's frequency; addition lowers it; the two
sensitivities are independent empirical numbers. Reversible trial
actions (clip-on mass) run in a `ReversibleSession` with exact
rollback — **trial the correction before the laser**, mechanically
enforced (an irreversible action in a reversible session raises).

## Certificates (R07)

HMAC-signed, hash-chained to the ledger head, superseding never
overwriting. Refusals: no fitted value → no certificate; accepted
outside its own preregistered band → no certificate. Every
certificate prints the claims it does NOT make (therapeutic,
consciousness, anomalous field). The demo signing key is in-repo and
the certificates are synthetic; a production key ceremony is a
human-only step.

## Fixture, DAQ, design-for-trim (R03, R04, R02)

- Fixture: five boundary-condition concepts; the coupling model puts
  numbers on "the mount shifts the spectrum more than a trim step";
  remount repeatability is **measured** on the twin, and the rule is
  binding: a trim step below the remount scatter is unmeasurable and
  must not be attempted (quantified in `stats.minimum_detectable_
  shift`).
- DAQ: Lorentzian fits that return `fitted: None` with a reason
  rather than a fabricated centre; clipping/nonlinearity/drift
  detectors; sessions that refuse to load without the synthetic flag.
- Design-for-trim: five primitives, three zones, symmetric groups
  with zero balance moment, fiducials + witness coupons, sham-trim
  and randomized-pattern controls, and a three-band reference family
  with cross-checked Gerber/drill exports.

## Additive, MEMS, oscillator (R08–R10)

- Six process cards; **printed fused silica is enforced not to be
  crystalline quartz** (registration refuses).
- MEMS twin with gas/anchor/thermoelastic losses and trim-method
  budgets; the foundry handoff is INTERFACE_ONLY because no cleanroom
  exists.
- **A resonator is not an oscillator**: `is_oscillator()` requires a
  sustaining amplifier, a declared loop, and Barkhausen satisfied.
  Leeson phase noise, ALC, TCF, aging, and package stress complete
  the oscillator-side models.

## Composite modes (R11)

The neutron paper's mathematics only: displaced-pair coherent sums,
azimuthal decomposition, **parity selection verified by computation**
(>95% even content at phase 0, >95% odd at phase π), separation-
controls-distribution, and drive-pattern order selection for partial
arrays with the angular-Nyquist alias band reported. The transfer
firewall refuses neutron/OAM-beam claims in code.

## Hardware blockers (all human-only)

Board fabrication (vendor), fixture machining, laser/CNC + enclosure
+ extraction, instruments (DAQ, vibrometer), printer access, foundry
collaboration. None engaged; every path that would need them is
capability-gated and currently refuses.
