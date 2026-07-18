# RGCS v4.6 — Crystalline Spacetime Coordinate Program (CSCP) ledger

Run ledger for the v4.6 programme. One row per agent, appended as work
lands. **Nothing in this programme is physical evidence.** Every
physical hypothesis is `UNTESTED` unless a calibrated bench record with
apparatus provenance exists — and none does.

- Branch: `v4.6-cspc`, cut from verified `main` @ `8bda6e8` (v4.5.2).
- Baseline: [`BASELINE_V4_6.json`](BASELINE_V4_6.json) (RELEASE_EVIDENCE).
- Doctrine constants: [`cspc/__init__.py`](../../../cspc/__init__.py) —
  evidence ladder, 8 transfer firewalls, excluded claims.
- Verdict contract: the final token may only be emitted when every
  software gate is green **and** all physical claims remain untested.

## Originating question (RQ-CSPC-001)

> Can crystalline resonators provide a physically meaningful bridge
> between stable phase, cross-domain frequency conversion, temporal
> order, spacetime measurement, and the much stronger idea commonly
> described as space-time travel?

The programme does **not** assume the answer is yes. Success does not
require supporting the originating hypothesis; publishable null results
are a success condition.

## Standing corrections carried into v4.6

| id | correction | status |
|----|-----------|--------|
| CSPC-CORR-001 | 2.45 GHz is not a unique fundamental resonance of water | carried from source ingest |
| CSPC-CORR-002 | `0.035652…` retains **Hz** units in the recovered equation | carried |
| CSPC-CORR-003 | the 11th powers-of-eight level is **not** an 11th octave | carried |
| CSPC-CORR-004 | arithmetic relationships do not establish coupling or spacetime travel | carried |
| CSPC-CORR-005 | source precision does not confer measurement precision (a 16-digit decimal derived from a nominal 2.45 GHz input carries the input's significance, not 16 digits) | carried |

## Defects found and fixed during the programme

| id | defect | resolution |
|----|--------|-----------|
| CSPC-D-001 | `compute_source_hash` (v4.5.2 anti-stale guard) hashed **raw bytes**, so a Windows checkout with `core.autocrlf=true` re-materialised `.py` files as CRLF and reported a spurious source mismatch for identical source. A genuinely fresh binary would fail `--build-info` verification after a clean clone or branch switch. | Normalise CRLF→LF before hashing; regression tests assert both line-ending invariance and that a real edit still changes the hash. Failure mode was fail-safe (never passed a stale binary as fresh). |
| CSPC-D-002 | Local `main` was stale at v4.4.0 because releases were fast-forwarded with `git push origin v4-dev:main`, which updates the remote ref only. Branching "from main" silently produced a v4.4.0 tree. | Branch reset to `origin/main`; local `main` re-pointed. Verified v4.5.2 content present before proceeding. |

## Agent ledger

| agent | workstream | commit | evidence class | physical status |
|-------|-----------|--------|----------------|-----------------|
| A00 | Baseline, branch, release isolation | (this commit) | RELEASE_EVIDENCE | UNTESTED |

## Binary freshness

The baseline records whether `dist/` matches current source. At
programme start it is **STALE by construction** — the v4.5.2 binary
predates the `cspc` package — and that is the honest answer, not a
defect. Packaging (A35) re-freezes from the final source; the v4.5.2
guard refuses to package a mismatched tree.
