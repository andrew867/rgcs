# V4 Completion Programme — Orchestrator Decision Log

Decisions by the master orchestrator (per 01_MASTER_ORCHESTRATOR: the
orchestrator alone resolves document conflicts and records them).
Append-only.

## DV4C-001 — Repository path

The pack states repository `/home/claude/rgcs-work/rgcs-v2`. That path
does not exist in this environment. Evidence-based resolution: the
real repository is the working tree at
`C:\Users\andrew\OneDrive - Green O365\Documents\GitHub\RGCS`
(remote `https://github.com/andrew867/rgcs`, branch `v4-dev`, HEAD
`2fed8fd` at programme start — see
`docs/v4/baseline/V4_REPO_INVENTORY.json`). The pack path is treated
as an environment artifact of pack authoring, not an instruction to
relocate.

## DV4C-002 — Release version target

The pack targets `v4.0.0-rc1` → `v4.0.0`. Both tags ALREADY EXIST and
`v4.0.0` is a published GitHub release (2026-07-16, 9 assets). Frozen
boundary 3 ("Do not rewrite public Git history, prior tags, prior
release assets") is binding and outranks the target-version line.
Resolution: this completion programme releases as **`v4.1.0-rc1` →
`v4.1.0`**. All pack references to "v4.0.0-rc1/v4.0.0" are read as
"the programme's RC/final tags", i.e. v4.1.0-rc1/v4.1.0. The v4.0.0
release, its assets, and its Zenodo linkage are frozen authorities.

## DV4C-003 — Supplied sources are not present in the repository

The pack's "Required source handling" enumerates ~19 sources
(Toyoda LiNiPO4 IOME, Schlauderer nonlinear AFM switching, Afanasiev
phonon-controlled exchange, Higuchi & Kuwata-Gonokami MnF2 optical
annealing, vdW exciton-magnon, chiral-phonon, optical angular
momentum, metacrystal, FDT essay, CERN/Atlantis/Star Nation
transcripts, News & Views 10.1038/s41563-026-02641-3). A full-repo
scan (PDF/subtitle glob; pack zip listing) finds NONE of these files
locally. The pack zip contains prompts only.

Resolution (missing dependency ≠ stop condition, contract §10):

1. M1 registers every required source as a **metadata-only** record:
   `access_status: METADATA_ONLY_NOT_LOCALLY_SUPPLIED`, `sha256: null`
   (no guessed hashes, contract §7), citation from public metadata,
   `licence_status: NOT_APPLICABLE_NO_LOCAL_FILE`,
   `redistribution_allowed: false`.
2. The News & Views item is registered `ACCESS_RESTRICTED_PREVIEW_ONLY`
   as mandated.
3. Model equations for the physics workstreams are implemented from
   their published, standard forms as enumerated IN THE PACK ITSELF
   (which is local, hashable, and registered as a source of type
   `INTERNAL_RGCS_AUTHORITY`), with classification ceilings:
   REDUCED_ORDER_VALIDATED is claimable only against DECLARED
   equations and analytic limits; any numeric comparison to
   paper-specific measured values is marked
   `SOURCE_VALUE_COMPARISON_PENDING_LOCAL_SOURCE` and excluded from
   validation claims.
4. FDT equations and subtitle motifs are taken from the pack's own
   enumeration (F = c^4/(4G)·α1·α2, α_R = (n²−1)/n², motif list) and
   quarantined as SOURCE_HYPOTHESIS/SRC exactly as specified.
5. If the user later supplies the files, M1's source-diff tool
   upgrades records to FULL_TEXT_LOCAL with real hashes.

## DV4C-004 — Execution topology

The contract suggests one git worktree per agent with parallel
dispatch. This environment is a OneDrive-synced Windows checkout where
parallel worktrees + parallel full FEM suites contend on the same
physical machine and OneDrive sync; the prior v4 programme (Agents
04–13) executed sequentially inline with per-agent commits and shipped
v4.0.0 with all gates green. Resolution: workstreams execute
**sequentially in-place on `v4-dev`, one coherent commit (or small
series) per agent, each with its own run log under `docs/v4/runlogs/`
and proof directory under `docs/v4/proof/<agent>/`**. R1 duties are
performed by the orchestrator directly (explicitly permitted by 19).
Commit boundaries provide the isolation the worktrees were meant to
give; ownership is still declared per agent in its run log. Deviation
recorded here per the contract's conflict rule.

## DV4C-005 — Namespace for the new platform layer

New v4-completion code lives in `rscs2_core/multiphysics/` (capability
firewall, coupling graph, result envelope), `rscs2_core/refmodels/`
(reduced-order reference systems), `rscs2_core/optics_channels.py`
(channel taxonomy), `rscs2_core/source_hypotheses/` (FDT + lore,
import-firewalled), `schemas/v4/`, `sources/registry/`, and
`docs/v4/`. The validated v4.0.0 modules (fem, quartz, crystal110,
piezo, accel, projections, eye, refsystems, proofbundle, cli) are the
CORE_VALIDATED authorities and are extended, never rewritten.

## DV4C-006 — v3 references location

The existing v3 source registry (`references/source_registry.yaml`,
`equation_provenance.yaml`) is a frozen v3 authority. The v4
completion registry lives at `sources/registry/` (per M1 prompt) and
LINKS to v3 records rather than editing them.
