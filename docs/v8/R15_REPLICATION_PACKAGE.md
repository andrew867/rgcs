# R15 P35 — Replication Package and External Handoff

A deterministic, public-only replication manifest (module hashes, schemas, receipts, seeds) is assembled for external replication.

- **Module:** `r15/replication_package.py`
- **Tests:** `tests/v8/test_replication_package.py`
- **Claim cap:** nothing measured; `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Negative results

- A package file containing private content is refused; only public, synthetic-fixture code, schemas, receipts, and seeds ship.
- The manifest is a deterministic content hash; it carries no physical result.
