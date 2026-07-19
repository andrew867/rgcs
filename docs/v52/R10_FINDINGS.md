# RGCS R10 — Findings

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v5.2.1
**Evidence class:** arithmetic, literature values, and software.
**No physical measurement was performed by this project.**

---

## The headline: a p-value that moves from 1e-5 to 1.0

**Module:** [`r10/cwarith.py`](../../r10/cwarith.py)

The source material offers two relations among five integers:

```
1516 = 1496 + 20
2160 = 1516 + 644 = 1496 + 20 + 644
```

Both are **exactly true**, verified in integer arithmetic. The question
is whether being true is *surprising*, and that depends entirely on the
null:

| Null | What it models | p |
|---|---|---|
| Naive uniform | five unrelated integers of similar magnitude | **1e-5** |
| Selection-process | the partial-sum closure of three generators | **1.0000** |

The observed set **is** such a closure, exactly:

```
sorted(observed)                      == [20, 644, 1496, 1516, 2160]
sorted({a,b,c,a+b,a+b+c})  a=1496, b=20, c=644
                                      == [20, 644, 1496, 1516, 2160]
```

Identical — not approximately. The relations are therefore not a
property discovered *in* the set; they are the construction *of* the set
restated. A partial-sum closure contains its partial sums the way a list
of even numbers contains no odd ones.

**Verdict: `EXPLAINED_BY_CONSTRUCTION`.**

Two further corrections to the arithmetic's apparent weight:

- **Three relations are two facts.** Given the first two, the third
  follows by substitution. Presenting three inflates the evidence by
  half.
- **The 21-Hz branch misses by exactly 1**, which is what a one-unit
  change to an addend must do. Bookkeeping, not a second confirmation.

### What this does not say

It does not say the numbers are meaningless, arbitrary, or that the
source is mistaken. The relations are exactly true and stay true. It
says this arithmetic carries **no evidential weight about origin**,
because *any* three integers closed under partial sums exhibit it. If
the generators themselves mean something, that has to be established by
other means — this arithmetic cannot do it.

---

## CW is three things (P07)

**Module:** [`r10/cwontology.py`](../../r10/cwontology.py)

| Sense | Dimension | Has a frequency? |
|---|---|---|
| `CW_CODE_WORD` | dimensionless | no — it's an index |
| `CW_CONTINUOUS_WAVE` | modulation mode | no — it's a mode |
| `CW_CARRIER_WAVE` | frequency (Hz) | **yes** |

Programme contract rule 3 is now structural rather than a matter of
discipline: `TypedValue.same_as()` raises `UnitCollision` across
dimensions, so `144` the code word can never be silently equated with
`144` Hz. The R9 CW integers are typed `DIMENSIONLESS` /
`UNTYPED_DECIMAL`, because no unit was ever recorded for them.

---

## Energy categories (P17) and Unruh scales (P18)

**Modules:** [`r10/energyledger.py`](../../r10/energyledger.py),
[`r10/unruh.py`](../../r10/unruh.py)

`Energy` raises on addition across its five kinds — heat, work,
reservoir, stored, dissipation — so "there is energy in the reservoir"
cannot be silently added to "energy available as work". There is exactly
one place where categories legitimately meet, and it is named
`first_law_residual()`. `available_work_bound()` requires a sink
temperature, so an isothermal reservoir yields exactly 0 J whether it
holds 1 J or 10²⁴ J. The vacuum-energy category error is a type error,
not a warning.

Unruh: 4.055e-21 K per m/s². One kelvin needs 2.466e20 m/s²; the Rindler
horizon then sits 0.364 mm away. Earth gravity gives 3.98e-20 K.

**A conclusion we expected and did not get.** Bulk mechanical
acceleration falls short by ~2.5e14 — an ultracentrifuge reaches
4e-15 K. But a single electron at the record 1.1e23 W/cm² laser focus
reaches 1.6e26 m/s² and T_Unruh ≈ 6.5e5 K, computed from intensity →
field → eE/m rather than asserted. **That is not absurd**, so the
verdict is split into `bulk_verdict` and `single_charge_verdict` instead
of a blanket claim the arithmetic does not support.

The energy-source refusal is carried by the budget instead, where it
belongs: the driving field's energy density exceeds the bath it induces
by 2.7e10×, and the effect is frame-dependent.

---

## The publication firewall found 30 real disclosures (P19)

**Module:** [`r10/firewall.py`](../../r10/firewall.py) ·
**Report:** [R10_PUBLICATION_FIREWALL.md](R10_PUBLICATION_FIREWALL.md)

All `PRIVATE_PATH`; no credentials, no personal identity, no source
material. Twelve were in live docs and are **repaired**. Eighteen sit in
the checksummed v2.0.0 archive, where editing them would invalidate the
provenance the archive exists to provide — those are **declared** with a
severity assessment rather than fixed.

Git history was not rewritten. That would break every clone and tag to
remove a low-severity disclosure that is already public, and the release
contract forbids it. A test pins the exposure to that one category, so a
credential or identity term appearing later fails the suite.

**Severity: LOW**, stated at its real size — sandbox build paths and a
username already public in the package metadata.

---

## P06 is blocked, and stays blocked

**Record:** [R10_P06_BLOCKED.md](R10_P06_BLOCKED.md)

The private repository exists and is correctly isolated, but
`sources/raw/144000/` is empty. No frame, no timestamp, no URL, no
device context.

`144.000` therefore remains an **untyped decimal**. The locale reading
(`144.000` = 144 000) is the cheapest explanation and cannot be
excluded; choosing the 2 m amateur band without evidence would be
selecting the interesting hypothesis over the ordinary one, which is the
failure mode this programme keeps catching in its own work.

The refusal is enforced in code, so a later shortcut raises rather than
returning a plausible number.

---

## Defects

### R10-D-001 — `r10` was omitted from the hash and packaging lists

A new research package was added to the tree and not to the two lists
that govern build-freshness hashing and distribution. This is **R8-D-006
and R9-D-004 starting over**, one generation later, for the same reason.

The difference is that this time the guards caught it rather than a
release doing so — which is what those guards were added for.

---

## What R10 does not claim

- No physical measurement, no carrier detected, no detector operated.
- The CW vectors are **not decoded**, and the arithmetic explicitly
  cannot authenticate a source.
- `144.000` is not a frequency.
- Unruh radiation is not an energy source.
- No medical, biological, or consciousness claim of any kind.

CW attribution stays at region granularity — *from the omega region* —
and no analysis step depends on provenance.
