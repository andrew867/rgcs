# No-omission certificate (P02)

Issued by the v4.2.1 completeness audit. Generated evidence:
[ORPHAN_IDEA_REGISTER.md](ORPHAN_IDEA_REGISTER.md),
[V4X_COVERAGE_LEDGER.md](V4X_COVERAGE_LEDGER.md),
`V4X_COVERAGE_LEDGER_STRICT.json`,
[V4X_PROMPT_PACK_DELIVERABLE_CROSSWALK.md](V4X_PROMPT_PACK_DELIVERABLE_CROSSWALK.md).

## What is certified

**268 items** carry an explicit owner, artifact, status, documentation
path, test or falsification condition, blocker, and next action:

| Source | Count |
|---|---|
| Fixed master ledger (A/F/G/E/S/W/H/C/I) | 248 |
| Orphans discovered by the P02 sweep | 20 |
| **Total** | **268** |

All seven strengthened gates pass: **G42A** (ID coverage), **G42B**
(artifact existence — every path exists, every symbol imports),
**G42C** (source/equation provenance), **G42D** (test or falsification
per row), **G42E** (documentation per row), **G42F** (status legal for
the delivered depth), **G42G** (blocker and next action on every
blocked row).

Enforced by `tests/v4/test_v4x_coverage_gates.py` — release-blocking.

## What is NOT certified

This certificate does **not** claim that every idea in the corpus has
been found. It claims that:

1. the fixed 248-item ledger is fully disposed;
2. a deterministic sweep over the available corpus (124 files scanned)
   and the repository surfaced 20 further ideas, each now disposed;
3. **no item was deleted for sounding implausible.**

A sweep is not a proof of exhaustiveness. It is a proof that the
specific searches ran and that what they found was kept. If a further
idea surfaces, the honest response is a new `ORPHAN-*` row, not a
revision of this certificate.

## The 248 was never a completeness proof

The v4.2.0 release reported "coverage ledger 248/248" as though the
number were the finding. It was the **input**: 248 was the count of
rows someone had already written down. The P02 sweep — the agent whose
entire job was to check that number against reality — **was never
run**.

Running it moved the count to 268. That is a 8% undercount in a
document whose purpose was to prove nothing had been missed, and it is
exactly why "100% of the ledger" and "nothing omitted" are different
claims.

## Dispositions

Every orphan has one of ten legal dispositions, and each is recorded
with its reason:

| Disposition | Count | Meaning |
|---|---|---|
| `quarantined_translation` | 3 | term retained; translated where honest |
| `translated_to_protocol` | 5 | operationalized into an experiment |
| `translated_to_model` | 1 | mapped to implemented mathematics |
| `translated_to_null` | 1 | registered with its null model |
| `quarantined_private` | 2 | private myth layer, unendorsed |
| `quarantined_source` | 1 | seller claim, held at SRC |
| `rejected` | 2 | **rejected on evidence**, with the number cited |
| `preserved_distinct` | 1 | distinct values not merged |
| `preserved_null` | 1 | null preserved (G48) |
| `preserved_contradiction` | 1 | contradiction preserved, not averaged |

Two rejections, both citing evidence rather than taste:

- **ORPHAN-009** (cusp "singularity") — rejected because the
  arc-length-weighted concentration is **10.576×**: a real focusing
  effect, and a *finite* one. A singularity diverges under refinement;
  this does not.
- **ORPHAN-010** (454 Ω as a frequency) — rejected because a
  resistance is not a frequency.

## The rule that governed the sweep

> **No orphan may be deleted because it sounds implausible.** It may be
> translated, quarantined, or rejected on evidence.

Phryll, portals, Atlantis, CERN, Star Nation, torsion, vortices, and
density bridges are all still here. None was deleted. None was endorsed.
The private-myth items are retained, marked non-public, and excluded
from public assets — preserved and unendorsed at the same time, which
is the only honest way to hold them.

## Signature

Certified against commit `HEAD` of the v4.2.1 closeout. Regenerate:

```bash
python tools/v4x_orphan_sweep.py --rescan
python tools/v4x_coverage_gates.py
python tools/v4x_prompt_pack_crosswalk.py
```
