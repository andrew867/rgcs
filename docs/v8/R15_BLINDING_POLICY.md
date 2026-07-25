# R15 P09 — Blind Operator Mode Policy

**Phase:** P09 (Tranche T3, Experimental Execution)
**Module:** `r15/blinding.py`
**Tests:** `tests/v8/test_blinding.py`
**Verdict:** `BLIND_OPERATOR_MODE_ENFORCED`
**Claim class:** `SOFTWARE_IMPLEMENTED` — measured here: **nothing** — `PHYSICAL_VALIDATION_NOT_CLAIMED`

## Why blinding exists

An operator who can see which condition is active during acquisition or
analysis can steer a result toward what they expect without any
dishonesty: a knob held a moment longer, a marginal trace kept rather than
retaken, a fit re-run until it "settles". Blinding closes that expectancy
channel by removing the knowledge — the operator works against one-way
codes, not the assignment.

This phase reuses the R13 authorities rather than duplicating them:
condition masking is `r13.preregister.blind_labels` / `unblind`, the
sealed commitment is an `r13.preregister` seal, the data lock is
`r13.serialize.content_hash`, and the claim taxonomy / evidence ladder is
`r15.claims`. No sibling R15 phase module is imported.

## Roles

| Role | Sees | May unblind |
|------|------|-------------|
| `OPERATOR` | blinded packets only | no |
| `ANALYST` | blinded data only | no |
| `AUDITOR` | may verify machinery, never reveal | no |
| `CUSTODIAN` | holds sealed commitment + true assignment | **yes** |
| `UNBLINDER` | role delegated to lift the blind | **yes** |

`UNBLIND_AUTHORIZED_ROLES = {CUSTODIAN, UNBLINDER}`. An operator or analyst
who could unblind themselves would see the assignment during the very
acquisition or analysis the blind protects — `refuse_unauthorized_unblind`
refuses it.

## Masked facets

The blinded run packet hides every sensitive attribute behind a one-way
code keyed to the sealed commitment:

- `CONDITION_LABEL` — which condition is active
- `PREFERRED_FREQUENCY`
- `SPECIMEN_CLASS`
- `ORIENTATION_LABEL`
- `PREDICTED_OUTCOME`

`operator_packet(...)` and `ui_payload(...)` emit only codes, the study
mode, and a marker. `packet_hides_assignment(...)` and
`payload_leaks_assignment(...)` verify no real value rides along.

## The unblinding gate — no peeking

The legitimate order is **acquire → lock → analyse-while-blinded →
unblind**. `BlindOperatorSession.unblind(role, sealed_commitment, epoch)`
passes three gates, in order:

1. **Authority** — the role must be in `UNBLIND_AUTHORIZED_ROLES`
   (`refuse_unauthorized_unblind`).
2. **Locked data** — the acquired dataset must already be sealed with
   `session.lock(data, epoch)`; unblinding before the lock is peeking and
   is refused (`refuse_unblind_before_lock`). An analysis run after an
   early reveal is no longer blinded even if presented as such.
3. **Sealed commitment** — the commitment supplied must match the one the
   blinding was locked under; a wrong or tampered commitment reveals
   nothing.

## Broken blinds cost evidence

A blind that breaks is never silent — it is logged and it downgrades
evidence from the blinded level to the broken-blind floor.

- **Accidental disclosure** — `record_accidental_disclosure(...)` logs a
  `Disclosure(kind="ACCIDENTAL", ...)` and downgrades that run.
- **Emergency unblind** — `emergency_unblind(role, commitment, reason,
  epoch)` breaks the blind early for cause (safety stop, subject
  withdrawal). It does not require a lock, but still requires an
  authorized role and the sealed commitment, is always logged as
  `Disclosure(kind="EMERGENCY", ...)`, and downgrades evidence.

Evidence levels (from `r15.claims.EvidenceLevel`):

- `BLINDED_EVIDENCE_LEVEL = E6` — blinded holdout support (protocol ceiling)
- `BROKEN_BLIND_EVIDENCE_LEVEL = E1` — exploratory floor after a broken blind

`evidence_level_for(run_id)` returns the broken-blind floor for any run
touched by a disclosure and the blinded level otherwise.

## Exploratory is not confirmatory

Confirmatory standing means the hypothesis and analysis were sealed before
the data. A run opened `EXPLORATORY` made no such commitment.
`refuse_relabel_confirmatory` refuses promoting exploratory → confirmatory
after the fact; the reverse downgrade is always allowed.

## Determinism

Everything is hash-based and clock-free: codes are SHA-256 masks keyed to
the sealed commitment, the data lock is a canonical content hash, and
every epoch is passed in explicitly. `blinding_report()` is byte-stable
across runs.

## Negative results and non-claims

- Nothing is measured. Every label, facet, and dataset is a synthetic
  fixture; no condition, specimen, orientation, frequency, or predicted
  outcome here is real.
- Blinding is a statement about **what the operator can see and when the
  blind may be lifted** — not about any physical outcome.
- The strongest class this module reaches is `SOFTWARE_IMPLEMENTED`. No
  physical validation is claimed, and there is no `PHRYLL_DETECTED` state.

## Reopening test

This phase reopens if any of the following becomes false:

- An operator packet or UI payload contains a real assignment value.
- An unblind succeeds without an authorized role, a locked dataset, and
  the exact sealed commitment.
- A broken blind (accidental or emergency) is not logged, or does not
  downgrade the affected run's evidence.
- An exploratory run can be relabelled confirmatory.

## Acceptance checklist

- [x] `r15/blinding.py` implements roles, masked packets, gated unblind,
      broken-blind logging, and exploratory/confirmatory separation.
- [x] Reuses R13 (`preregister`, `holdout`, `serialize`) and `r15.claims`;
      no sibling R15 phase module imported.
- [x] Operator payload contains no assignment; analyst cannot unblind;
      emergency unblinding is logged and downgrades evidence; exploratory
      cannot be relabelled confirmatory.
- [x] Focused, negative, and determinism tests green
      (`tests/v8/test_blinding.py`, 25 tests).
- [x] Receipt `docs/v8/receipts/P09.json` conforms to
      `phase_receipt.schema.json`; privacy scan clean (synthetic fixtures
      only).
