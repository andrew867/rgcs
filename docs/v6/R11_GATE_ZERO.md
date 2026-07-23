# R11 Gate Zero Receipt

**Authority:** RGCS R11 / v6.0.0 (candidate)
**Scope:** the exact start-state proof required before any R11 change, and the one condition that could not be met.
**Last verified commit:** v5.9.0 baseline (branch `v590-r11`)
**Prerequisites:** none.
**Related code / tests:** [`r11/sources.py`](../../r11/sources.py), [`tests/v6/test_r11_sources.py`](../../tests/v6/test_r11_sources.py), [`r10/firewall.py`](../../r10/firewall.py)
**Known limitations:** condition 5 is waived and declared, not satisfied (see below).
**Next review trigger:** any change to the public/private boundary, or a decision to rewrite published history.

---

## Conditions checked

| # | Condition | Result |
|---|---|---|
| 1 | `main == d2381c6ff99496754be725bb78c6cf5b367e0a39` | **PASS** — exact match |
| 2 | tag `v5.9.0` points at the same commit | **PASS** |
| 3 | worktree clean | **PASS** |
| 4 | suite of record `3485 passed, 1 deselected, 0 failed` | **PASS** |
| 5 | no private identity / alleged communicator in tree **or Git history** | **WAIVED — DECLARED RESIDUAL** |
| 6 | private files ignored and untracked | **PASS** — the private operator delta is gitignored and untracked |

## Condition 5 — what was found

Identity strings for the alleged communicators are present in **7 tracked
files** in the public tree, and in **immutable history** reaching back to
the frozen **v2.0.0 baseline**. They are inside published release tags.

Satisfying the condition as literally written ("or Git history") would
require rewriting published history and re-cutting released tags. That
directly violates this project's standing release policy — *tags and
records never modified* — would invalidate published release assets and
DOI-referenced commits, and would not reach anyone who already cloned.

## Disposition

The operator reviewed this and elected **not** to rewrite history. It is
therefore recorded as a **`DECLARED_RESIDUAL_EXPOSURE`** in
[`r11/sources.py`](../../r11/sources.py) (`DECLARED_RESIDUAL`), by
*category* — the strings themselves are not repeated, because a leak
report must not restate the leak.

This follows the precedent already in the codebase:
`r10.firewall.frozen_surface_exposure()` records the absolute-path
disclosures baked into the immutable v2.0.0 archive the same way, on the
same reasoning — *recorded, not fixed; a real residual exposure rather
than a clean pass*.

**Forward rule (enforced in code):** R11 adds **no new** identity
strings. Public modules use the neutral aliases only, and
`sources.refuse_new_identity_exposure()` raises on any attempt to add
one. The declared residual is a record of the past, not a licence for
the future.

## Verdict

Gate Zero conditions 1, 2, 3, 4 and 6 **PASS**. Condition 5 is
**waived and declared**, not silently dropped. R11 proceeded on that
basis.

`PHYSICAL_VALIDATION_NOT_CLAIMED`
