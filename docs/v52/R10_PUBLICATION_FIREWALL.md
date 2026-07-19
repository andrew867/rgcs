# R10 P19 — Publication firewall, and what it found

**Module:** [`r10/firewall.py`](../../r10/firewall.py)
**Status:** live tree **CLEAN**; two **declared residual exposures**

---

## What it enforces

Private source material must never reach public Git history, packages,
docs, logs, fixtures, or release assets. Two design commitments:

**Git history is disclosure.** Committing a private file and deleting it
later does not remove it, so the scanner checks history, not just the
working tree — the working tree being the part that is already fine.

**`.gitignore` is not confidentiality.** An ignored directory inside the
repository is one `git add -f` from publication, and it still sits in
the backup and the search index. `private_root_is_outside()` therefore
requires the private root to be outside the worktree and does not accept
"but it's ignored".

**A leak report must not quote the leak.** Findings carry category,
path, line and surface — never an excerpt. A report that reproduces the
matched text is a second disclosure, typically to a wider audience than
the first.

## What it found on first run

**30 findings in the public repository.** All `PRIVATE_PATH`; no
credentials, no personal identity, no source material. The repository
has been public since 2026-07-15, so these were already disclosed.

| Surface | Findings | Action |
|---|---|---|
| Live docs and registry | 12 | **Repaired** — paths redacted to `<BUILD_ROOT>/` and `<USER_HOME>\` |
| `archive/v2.0.0/release/PROVENANCE.json` | 18 | **Declared** — see below |
| Git history | 49 | **Declared** — see below |

### R10-D-001 — why 18 findings were not repaired

They are build-environment paths inside a **checksummed, immutable
archive**. Editing them would invalidate the very provenance record the
archive exists to provide, and the release contract forbids rewriting
frozen history.

So they are reported, not fixed, by `frozen_surface_exposure()`, with a
severity assessment. **A clean live tree with history quietly excluded
is not an honest pass** — the exposure is declared instead, and a test
asserts the declaration exists rather than asserting a clean sweep.

### Why git history was not rewritten

Rewriting published history would break every existing clone, every
release tag's reachability, and the checksums that other documents
attest to. That is a destructive operation on public artefacts to remove
a low-severity path disclosure that is already public. The trade is not
worth it, and the release contract forbids it.

A test pins the exposure to the known category: if any **new** category
— a credential, a personal identity term, private channelling — ever
appears in history, it fails.

## Assessed severity: LOW

The disclosed content is:

- `/home/<name>/` — sandbox build directories from automated runs.
- `C:\Users\<name>\` — a local directory layout, and a username that is
  already public in `pyproject.toml`, `CITATION.cff`, and the commit
  author field.

No credential, personal record, transcript, or source material was
exposed. This is untidy rather than dangerous — but it is recorded at
its real size rather than rounded down to zero.

## The scanner is tested for power

A leak scanner that finds nothing because it looks for nothing is the
worst possible outcome. Six planted samples across five categories must
each be detected, and clean prose must not be flagged. If the detection
tests stop firing, the suite fails.

## The only route from private to public

`sanitized_export_record()` requires a source-private hash, a *different*
public output hash, a non-empty redaction list, a sanitizer version, and
a reviewer. It refuses an export with no redactions ("that is a copy,
not a sanitisation") and one whose hashes match ("nothing was changed").
