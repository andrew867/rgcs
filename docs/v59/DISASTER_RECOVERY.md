# Disaster Recovery — Export, Restore, and Verify

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** how to export a verifiable archive and prove a restored copy is faithful.
**Last verified commit:** v5.8.0 baseline (branch `v580-r10-10`).
**Prerequisites:** [CONTINUITY_HANDOFF](CONTINUITY_HANDOFF.md), [OPERATIONS_RUNBOOK](OPERATIONS_RUNBOOK.md).
**Related code / tests / schemas:** [`r10/continuity.py`](../../r10/continuity.py), [`tests/v52/test_r10_continuity.py`](../../tests/v52/test_r10_continuity.py); schema `ContinuityManifest`.
**Known limitations:** the manifest proves faithfulness of a *given* tree; it cannot prove that off-repository, geographically separate backups exist. That is an operational responsibility, not a software one.
**Next review trigger:** any change to the canonical artifact set, or a failed restore drill.

---

## The model

Disaster recovery here is a **manifest + verify** loop, not a magic
backup. The unit of truth is a deterministic, content-hashed manifest of
the canonical artifacts:

- `build_manifest(root, rel_paths)` — hashes each canonical file into a
  **sorted, reproducible** manifest. Same bytes → same manifest. A
  missing canonical file is an **error**, not a silent omission.
- `export_manifest(entries, dest, commit=...)` — writes the manifest
  (schema `rgcs.continuity_manifest.v1`) deterministically.
- `verify_restore(root, entries)` — checks a restored tree and **names
  every** missing or altered file; verdict `RESTORE_VERIFIED` or
  `RESTORE_INCOMPLETE`.
- `refuse_restore_on_mismatch(report)` — refuses to call a restore
  successful while any hash differs.

## The drill

1. Build and export a manifest of the canonical public tree at a known
   commit.
2. Build and export a **separate** manifest of the private repository
   (kept private; 0 remotes).
3. Simulate loss: restore each tree from its own backup.
4. Run `verify_restore` against the manifest. Every canonical hash must
   match; anything else is `RESTORE_INCOMPLETE` and must be resolved
   before declaring recovery complete.
5. Run the [successor drill](CONTINUITY_HANDOFF.md#the-successor-drill) on
   the restored public tree: it must clone, build, test green, regenerate
   docs, and reproduce one null — from the restored copy alone.

## Two responsibilities the software cannot discharge

- **Off-site backups.** Keep at least one copy of each repository on
  separate physical media/geography. The private repository is
  OneDrive-synchronized (a managed tenant); that is redundancy against
  local loss, not against account loss — keep an independent cold copy.
- **The private boundary survives restore.** A restored private archive
  must never be pushed to a public remote. Re-run the publication firewall
  ([`r10/firewall.py`](../../r10/firewall.py)) on any restored public tree
  before it is published.

`PHYSICAL_VALIDATION_NOT_CLAIMED`
