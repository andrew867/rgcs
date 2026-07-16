# V4 Baseline Authority Map (Agent B0)

Baseline commit: `2fed8fd` on `v4-dev` (see V4_REPO_INVENTORY.json for
head, tags, remotes, worktrees, dirty state at scan time).

## Authoritative documents (resolved by content, not filename age)

| domain | authority | status |
|---|---|---|
| Programme instructions | `internal-docs/plans-v4/` prompt pack (24 files, SHA256SUMS in pack) | CURRENT — this programme |
| Prior v4 execution record | `docs/PROGRAMME_PROGRESS.md` rows v4-A00..A13 + `docs/plans-v4/AGENT_*_HANDOFF.md` | AUTHORITATIVE for what v4.0.0 contains |
| v4.0.0 release | tag `v4.0.0` @ `2fed8fd`, GitHub release w/ 9 assets | FROZEN (DV4C-002) |
| Frozen math registries | RGCS-M.* / RSCS-C.* / RSCS-O.* (v2/v3) + `rscs2_core/registry/rscs2_registry.yaml` (v4.0.0, append-only) | FROZEN / APPEND-ONLY |
| v3 source provenance | `references/source_registry.yaml`, `references/equation_provenance.yaml` | FROZEN (DV4C-006) |
| FEM numerical authority | `rscs2_core/fem.py` at v4.0.0; commits 9165594, 7962817, 3fcb0d7 all reachable (verified) | CORE_VALIDATED |
| Proof bundle | `proof_bundle_110mm/` @ v4.0.0 (verdict CONVENTIONAL_NODE_FOUND) | current; M9 EXPANDS, never falsifies |
| Decision authority | `docs/plans-v4/V4_DECISION_LOG.md` (prior) + `docs/v4/V4C_DECISION_LOG.md` (this programme) | append-only |

## Conflicts detected and resolutions

1. Pack repo path vs real path → DV4C-001.
2. Pack target tags v4.0.0-rc1/v4.0.0 already exist and are published
   → programme releases v4.1.0-rc1/v4.1.0 (DV4C-002).
3. Pack-required sources absent locally → metadata-only registration
   policy (DV4C-003).
4. Two plans-v4 directories exist: `docs/plans-v4/` (prior programme,
   public) and `internal-docs/plans-v4/` (this pack, gitignored).
   They are different artifacts, not duplicates; no merge.

## Protected refs and checksums

`V4_FROZEN_ARTIFACT_CHECKSUMS.json` records tree hashes for
v2.0.0/v3.0.0/v3.0.1/v4.0.0(+alpha,rc1), the `archive/v2.0.0` tree
object, release SHA256SUMS digests, and the current proof-bundle
manifest digest. Later no-regression comparisons diff against these.
