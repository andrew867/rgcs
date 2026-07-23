# Roadmap — Now / Next / Later

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** What is being done now and what is gated on data that does not yet exist.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [CURRENT_STATUS.md](CURRENT_STATUS.md), [APPARATUS_ARCHITECTURE.md](APPARATUS_ARCHITECTURE.md)
**Related code / tests / schemas:** `r10/`, `tools/`, [../../CHANGELOG.md](../../CHANGELOG.md)
**Known limitations:** Every "Next" and "Later" item is gated on hardware, specimens, or datasets that do not exist. Nothing here is a schedule or a promise.
**Next review trigger:** Acquisition of any specimen or dataset, or restoration of hosted CI.

## Now

- Build and maintain the r10 software modules, each defaulting to a refusal/null.
- Publish nulls and refusals as the primary science.
- Documentation and **continuity** work — reducing the bus-factor-zero risk (see
  [CONTINUITY_HANDOFF.md](CONTINUITY_HANDOFF.md)).
- Keep the local suite green on the exact release commit (the verification of
  record while hosted CI is down).

## Next (gated)

- **If matched specimens are acquired:** run the matched natural-vs-synthetic
  quartz protocol — synthetic quartz as the mandatory control. Currently
  **BLOCKED_NO_SPECIMENS**. See
  [NATURAL_VS_SYNTHETIC_QUARTZ.md](NATURAL_VS_SYNTHETIC_QUARTZ.md).
- **Restore hosted CI** once GitHub Actions minutes are available again, so
  verification is not local-only.

## Later (gated)

- Any **prospective holdout scoring** — pre-registered, paper-only until a real
  data source exists.
- **Independent replication** — the strongest evidence class, and one no amount
  of internal work can produce.

## The gate

Everything past "Now" depends on **hardware, specimens, or measured data that
does not exist yet**. Until then the honest output stays a refusal or a null.
See [../../SCIENTIFIC_BOUNDARIES.md](../../SCIENTIFIC_BOUNDARIES.md).

PHYSICAL_VALIDATION_NOT_CLAIMED
