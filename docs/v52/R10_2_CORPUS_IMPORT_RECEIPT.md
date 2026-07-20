# R10.2 — Corpus Import Receipt (public-safe)

**Date:** 2026-07-20
**Scope:** counts and provenance discipline only. **No source content,
no transcript text, no personal records, and no private paths appear in
this document or anywhere in the public repository.**

---

## Import

The private source corpus was imported into the private source root
(no Git remote, outside the public worktree). The detailed receipt with
per-file hashes lives in the **private** repository.

| | |
|---|---|
| Files considered | 70 |
| Byte-unique canonical files imported | **53** |
| SHA-256 verified against manifest | **53 / 53** |
| Hash mismatches | 0 |
| Exact duplicates skipped | 17 |
| Missing staged files | 0 |
| Private journal included | no |
| Generated project artifacts included | no |

Exact duplicates were skipped and are **not** counted as independent
corroboration — duplicated text is one source repeated, not two sources
agreeing.

## What is public, and what is not

- **Public:** two peer-reviewed academic papers (a firefly-brightness
  correction and the tetrahedron vertex-estimation paper), cited as
  conventional literature in [`r10/priorart.py`](../../r10/priorart.py);
  and the conventional-science chronology in
  [`r10/chronology.py`](../../r10/chronology.py).
- **Private:** the 68 source-media transcripts and reference inputs, and
  every date, quotation, name, and provenance detail derived from them.

## Publication boundary

The public firewall ([`r10/firewall.py`](../../r10/firewall.py)) reports
**zero findings** against the committed public tree. The corpus lives
entirely inside the private repository, which has no remote.

No real person is named, characterised, classified as nonhuman, or
associated with any lore species anywhere in the public repository.
