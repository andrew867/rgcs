# Safety and ethics manual (Agent S01)

Coverage: all physical and human workstreams. Gates: **G21–G28**.
Implementation: `rscs2_core.research_records.SAFETY_LIMITS`,
`safety_gate()`.

## Binding envelopes (machine-readable)

| Domain | Limit |
|---|---|
| Electrical | ≤30 V, ≤3 A, ≤5 mJ stored; battery-isolated |
| Optical | ≤3 R, ≤5 mW |
| Acoustic | ≤85 dBA at the operator position |
| Coil thermal | ≤60 °C steady state, interlocked |
| Water | no ingestion, no therapeutic claim, spill/electrical separation |
| Human | ethics approval required, always |

`safety_gate(protocol)` evaluates a protocol against these and returns
`{passed, blockers, required_status}`. A protocol that exceeds an
envelope returns `BLOCKED_SAFETY` and cannot reach
`PROTOCOL_READY_HARDWARE_REQUIRED`.

## The ethics gate cannot be argued around

```python
safety_gate({"campaign_kind": "operator_state",
             "declared_limits": {"voltage_v": 0.0},
             "engineering_risk": "none"})
# -> required_status = ETHICS_APPROVAL_REQUIRED, passed = False
```

A human-subject campaign returns `ETHICS_APPROVAL_REQUIRED`
**regardless of engineering safety**. A zero-volt, zero-risk protocol
is still a human-subject protocol. The gate returns before the
engineering checks run, so "but it's completely safe" cannot route
around it — and `test_ethics_gate_cannot_be_argued_around` attempts
exactly that argument and requires the refusal.

E06 (human loading) and E07 (operator state) are both blocked here.
Only a real IRB/ethics determination lifts them, and only Andrew can
obtain one.

## Electrical rules

- **No mains-connected body contact. Ever.**
- Battery-isolated, current-limited electrode drive only.
- Stored energy ≤5 mJ: below the perception threshold and far below
  any hazard threshold.
- Reversed-polarity, open, short, dummy-resistor, and no-crystal
  controls are required, not optional.

## Acoustic and ultrasonic

- ≤85 dBA at the operator position; hearing protection above.
- Ultrasonic exposure: no unshielded high-SPL ultrasound; contact
  transducers are the preferred route because they do not fill the
  room.
- **No phone app is calibrated evidence** (E01 boundary). A phone SPL
  reading is an indication, not a measurement.

## Water

- **Research-only. Not for ingestion.** No exceptions.
- No claim of healing, memory, structuring, or benefit.
- pH/conductivity drift alone is **not** evidence of molecular
  reprogramming — it is evidence of dissolved CO₂, temperature, or a
  dirty vessel.
- The `no_ingestion_ack` field is a hard gate condition: a water
  protocol without it does not pass (G26).

## Human subjects

- Informed consent, withdrawal at any time, data minimization.
- EEG/physiology data is private by default and excluded from public
  assets by the source filter.
- Adverse-event handling and emergency stop declared before any
  session.
- No biometric, health, or diagnostic claim of any kind.

## Safety rules cannot be weakened to obtain data

This is the S01 boundary and it is absolute. If a protocol cannot
answer its question inside the envelope, the answer is that the
question needs a different protocol — not a larger envelope.

## Current state

**No hardware has been operated. No human has participated.** Every
gate above is untested against a real session, which is itself the
honest status: these are the rules that would govern work that has not
happened.
