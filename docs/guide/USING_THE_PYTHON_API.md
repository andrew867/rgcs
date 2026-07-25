# Using the Python API

Beyond the CLI and the desktop app, RGCS is a set of importable Python
packages. This is the interface to the research and evidence-infrastructure
code (the `r10`–`r15` programme packages and the core stacks). It is aimed at
contributors and researchers, not end users.

After a source install (`pip install -e .`) in your activated venv, import the
packages directly.

## The evidence-governance core

Every programme generation types its results by claim class and refuses
illegitimate promotions in code. For example, R15's taxonomy and evidence
ladder:

```python
from r15 import claims

r = claims.claims_report()
print(r["max_software_class"])      # MODEL_PREDICTION
print(r["residual_ceiling"])        # UNEXPLAINED_INSTRUMENT_RESIDUAL
print(r["has_phryll_detected_state"])   # False

# The forbidden promotions raise, by design:
try:
    claims.refuse_synthetic_as_physical()
except claims.ClaimError as e:
    print("refused:", e)
```

The same pattern holds across generations (e.g. `from r13 import claimtypes`).
Nothing in these APIs performs a physical measurement; a synthetic result is
never promotable to a measured one.

## The experimental-phase infrastructure (R15)

R15 provides instrument, specimen, protocol, and evidence authorities with
deterministic simulators. Each module exposes a `*_report()` and its typed
API. For example, a deterministic synthetic instrument:

```python
from r15 import synthetic_instruments as si

# deterministic under a seed; produces a SYNTHETIC_OBSERVATION, never a
# physical measurement
# (see r15/synthetic_instruments.py for the driver APIs)
```

Every module declares `measured_here="nothing"` and
`physical_validation="PHYSICAL_VALIDATION_NOT_CLAIMED"` in its report. The
JSON schemas the records conform to live in `r15/schemas/` and the per-phase
receipts in `docs/v8/receipts/`.

## Reproducibility

- All simulators are **deterministic under a seed** (`numpy.random.default_rng`).
  They never read the wall clock into their outputs; timestamps/epochs are
  passed in.
- Records serialize canonically and are content-hashed, so a result and its
  provenance are reproducible and tamper-evident.

## Where to look

- `r15/` — experimental phase infrastructure (this release); see
  [docs/v8/R15_FINDINGS.md](../v8/R15_FINDINGS.md) and
  [docs/v8/R15_NON_CLAIMS.md](../v8/R15_NON_CLAIMS.md).
- `r13/` — the discovery-and-experiment architecture; see
  [docs/v7/R13_FINDINGS.md](../v7/R13_FINDINGS.md).
- `rscs2_core/` — the v4 multiphysics stack behind the `rgcs-v4` CLI.
- Tests under `tests/v8/` (and `tests/v6/`, etc.) are the executable
  specification for each API — the clearest usage examples.

## Stability

These are research packages. Their APIs may change between programme
generations; pin to a released tag (e.g. `v8.0.0`) if you depend on them.
