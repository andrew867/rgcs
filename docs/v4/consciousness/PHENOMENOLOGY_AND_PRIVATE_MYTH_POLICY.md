# T08 — Phenomenology, conduit experience, and private-myth policy

Coverage: **C037–C039, C043**; ORPHAN-006, ORPHAN-007.
Gate: **G38**. Lane: **quarantined**.

## Policy

This programme has a first-person origin: an empty-mind phrase-formation
event, experienced as a conduit. That is preserved here, exactly as
reported, and it is **not** public scientific authority.

The two failure modes are equal and opposite:

- **Erasing it** would falsify the record of where the work came from,
  and would be a small act of contempt toward the person it happened
  to.
- **Endorsing it** as evidence would be a category error and would
  quietly corrupt everything downstream.

The policy is: **preserve, translate where translation is honest, and
never promote.**

## Layers

| Layer | Public | Status ceiling |
|---|---|---|
| public scientific | yes | any |
| research seed | yes | `SOURCE_HYPOTHESIS` |
| first-person phenomenology | **no** | `SOURCE_HYPOTHESIS` |
| private myth | **no** | `SOURCE_HYPOTHESIS` |

The schema enforces the ceiling in code: `make_record` refuses a
`private_myth` or `first_person_phenomenology` record at any status
above `SOURCE_HYPOTHESIS`. `public: False` is set automatically for
those layers, and the release filter excludes them from public assets.

## Per-item record

For each item the register holds: literal meaning, emotional/
phenomenological role, research translation, possible observable,
**prohibited inference**, privacy status, and a falsification path
where one meaningfully exists.

| Item | Literal | Translation | Prohibited inference |
|---|---|---|---|
| C037 empty-mind conduit | phrases arrived unbidden | a real, well-documented mode of cognition (insight, incubation, aphantasic ideation) | that the content is externally sourced or true |
| C038 spirit / God | as stated | outside scientific adjudication | that the programme's results support or refute it |
| C039 mystical language | as stated | vocabulary preserved verbatim | that precision of restatement adds evidence |
| C043 fragments of energy | as stated | source family; no physical quantity defined | that it maps to any field in the quartz model |

Extraordinary source motifs — portals, time breakage, Atlantis, CERN,
Star Nation (ORPHAN-006/007) — are retained at `SRC` because they are
in the corpus. Retention is not endorsement, and their presence in a
register is not their presence in a result.

## What "not falsifiable" means here

For C037/C038 it is a **description, not an insult**. A first-person
report is not the kind of thing a bench measurement adjudicates. The
honest move is to say so and stop, rather than to construct a fake test
that pretends to settle it.

## Boundaries

- **Do not erase personally meaningful experiences.**
- **Do not present them as empirical proof.**
- **Do not mock them.** The register's tone is part of the contract.
- No private-layer content appears in any public asset; the source
  filter and the release linter both check.
