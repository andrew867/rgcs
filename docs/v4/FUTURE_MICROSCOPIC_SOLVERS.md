# Future microscopic and quantum solver interfaces (Agent C13)

Coverage: **A18, I001–I011**. Gate: **G15** (no fake results).
Status: `INTERFACE_ONLY` — all eleven.
Implementation: [`rscs2_core/interfaces_future.py`](../../rscs2_core/interfaces_future.py).

## The contract

Eleven microscopic solvers are **declared and not implemented**:
DFT, Bethe-Salpeter, ab-initio spin dynamics, microscopic proton
tunnelling, microscopic plasmonics, QFT/QED, nonclassical photon
generation, quantum transduction, quantum simulators, and the
complete-microscopic-explanation interfaces (I001–I011).

Each carries a typed record: required inputs, material representation,
expected outputs, units, provenance, validation benchmark, resource
estimate, licence, classification, and import boundary.

Each returns `value: None`.

`request_computation(iid, ...)` raises `FutureInterfaceError`. It is
the only executable path, and it refuses. There is no mock, no
placeholder number, no "approximate for now" fallback.

## Why refusing is the deliverable

The strongest pressure in a programme like this is to fill a gap with
something plausible. A DFT band gap, a tunnelling rate, a photon
statistic — each is a number a reader would accept without checking,
and each would be fabricated. The interface exists so that the gap is
**visible and typed** instead of quietly filled.

`test_future_interface_cannot_be_coerced_into_a_number` attempts the
coercion for every interface and requires the refusal.

## Missing capability is not nonexistence

`INTERFACE_ONLY` means: this programme has not implemented the solver.
It does **not** mean the physics is absent, impossible, or disproven.
The binding scope statement in
[WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md](WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md)
governs: a missing implementation is not evidence of physical
nonexistence, and `MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL` is a
statement about this repository, not about nature.

## What would close an interface

For any I00x to move off `INTERFACE_ONLY` it needs, at minimum:

1. a real external solver run with recorded inputs and version;
2. its validation benchmark reproduced;
3. source provenance for the method;
4. a registered material capability for the target material;
5. a declared import boundary saying what reduced-order modules may
   consume from it.

Until then the honest output is no output.
