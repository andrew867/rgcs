# Publication and Claim Policy

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** what may be published, what stays private, and the claim ladder.
**Last verified commit:** v5.8.0 baseline (branch `v580-r10-10`).
**Prerequisites:** none.
**Related code / tests / schemas:** [`r10/firewall.py`](../../r10/firewall.py), [`r10/claimfirewall.py`](../../r10/claimfirewall.py); [SECURITY_PRIVACY_AND_SAFETY](SECURITY_PRIVACY_AND_SAFETY.md).
**Known limitations:** policy is enforced by firewalls plus human review; neither alone is sufficient.
**Next review trigger:** any new claim class or source category.

---

## Public

Verified patents and history; crystallographic axis facts; specimen
ontology and controls; reversible codec mathematics; coordinate software;
nulls and failures; public manuscripts; and continuity documentation.

## Private

Raw Tier-A source text; personal journal and synchronicity material; the
source's private personal-identity and global-heart meaning; private
locations and experiences; and narrative material. Public artifacts keep
stable provenance IDs and hashes without exposing the raw text.

## The claim ladder (no automatic jumps)

```
SOURCE_REQUIREMENT -> HISTORICAL_FACT -> MATHEMATICAL_DERIVATION ->
SOFTWARE_VERIFIED -> MATERIAL_DIFFERENCE_MEASURED ->
CONTROLLED_EFFECT_MEASURED -> INDEPENDENTLY_REPLICATED
```

Current position: **`SOFTWARE_VERIFIED`**. Every rung from
`MATERIAL_DIFFERENCE_MEASURED` on is empty.

## Three standing statements every public artifact must respect

1. **Natural quartz is source-required but experimentally unresolved.**
2. **Synthetic quartz is a mandatory control**, not a rival to dismiss.
3. **Corporate/defense chronology does not prove classified provenance.**

And, everywhere: **`PHYSICAL_VALIDATION_NOT_CLAIMED`.**

## Release gate

No release ships while the publication firewall reports any finding on the
committed tree, or while any documented test count disagrees with the
measured count. See [RELEASE_PROCESS](RELEASE_PROCESS.md).

`PHYSICAL_VALIDATION_NOT_CLAIMED`
