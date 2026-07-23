# Source Authority and Provenance

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** how source material is attributed, and why Tier-A attribution is never evidence.
**Last verified commit:** v5.8.0 baseline (branch `v580-r10-10`).
**Prerequisites:** [PUBLICATION_POLICY](PUBLICATION_POLICY.md), [SECURITY_PRIVACY_AND_SAFETY](SECURITY_PRIVACY_AND_SAFETY.md).
**Related code / tests / schemas:** [`r10/session.py`](../../r10/session.py), [`r10/claimfirewall.py`](../../r10/claimfirewall.py), [`r10/naturalsource.py`](../../r10/naturalsource.py); schema `SessionEvent`.
**Known limitations:** provenance records attest to *who said what, when*; they never attest that a claim is true.
**Next review trigger:** a new source, or any change to the attribution contract.

---

## Two Tier-A private sources

The source material is attributed to two distinct private Tier-A sources,
carried under a single public alias, `OMEGA_REGION_SOURCE`. Their real
identities are private and are not required for any analysis. **Tier A
means faithful attribution — accurate wording, chronology, and
uncertainty — not empirical verification.** A Tier-A record is never
promoted to evidence by virtue of its attribution.

## Source is not operator

Two provenance classes are kept rigorously separate and never merged:

- **Source records** (`SRC_JH`, `SRC_LS`) — what a source said.
- **Operator (AG) notes** — what the operator observed or inferred, in
  typed sub-classes (direct note, paraphrase, interpretive note,
  prior-media recall, no-look-ahead self-report, operator state).

`r10/session.py` refuses at construction to let a source record carry an
operator-note type, or vice versa, and the session log is **append-only**:
a correction is a new record that references the one it corrects; nothing
is overwritten.

## Evidence statuses (no automatic promotion)

`RAW_SOURCE_RECORD`, `SOURCE_CLAIM`, `OPERATOR_NOTE`, `PRIOR_MEDIA_RECALL`,
`NO_LOOKAHEAD_SELF_REPORT`, `MATHEMATICAL_TRANSLATION`, `HISTORICAL_FACT`,
`CONVENTIONAL_ENGINEERING_ANALOGUE`, `SOFTWARE_VERIFIED`,
`SOURCE_REQUIREMENT`, `PHYSICAL_HYPOTHESIS`, `PROSPECTIVE_PREDICTION`,
`MEASURED`, `REPLICATED`, `UNSUPPORTED`, `CONTRADICTED`, `UNRESOLVED`.

The claim ladder is climbed one rung at a time, with no jumps:

```
SOURCE_REQUIREMENT -> HISTORICAL_FACT -> MATHEMATICAL_DERIVATION ->
SOFTWARE_VERIFIED -> MATERIAL_DIFFERENCE_MEASURED ->
CONTROLLED_EFFECT_MEASURED -> INDEPENDENTLY_REPLICATED
```

## Public artifacts keep provenance without exposing raw text

Public records carry stable provenance IDs and hashes so a claim can be
traced, but the raw Tier-A text, the private interpretations, and personal
material stay in the private repository. The content firewall
[`r10/claimfirewall.py`](../../r10/claimfirewall.py) quarantines any
source claim in a harmful category (`UNSUPPORTED`, never promoted).

`PHYSICAL_VALIDATION_NOT_CLAIMED`
