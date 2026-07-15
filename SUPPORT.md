# Support

## Where to get help

| Need | Go to |
|---|---|
| "What is this project, really?" | [README](README.md), [FAQ.md](FAQ.md), [DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md) |
| Install / build / test problems | README Quick start; per-manuscript `BUILD.md`; open a GitHub issue with your platform + Python version + full error |
| Understanding an equation or operator | `docs/RSCS_NOTATION_LEDGER.md` (ids + symbols), `rscs_core/registry/rscs_registry.yaml` (machine registry: module, units, tests per id), `docs/model_registry.yaml` (frozen v2 equations) |
| Why a decision was made | `docs/DECISION_LOG.md` (append-only, D3-001 onward) |
| Claim status / evidence | `docs/CLAIM_REGISTER.md`, `docs/ROADMAP_TO_FALSIFICATION.md`, `docs/NEGATIVE_RESULTS.md` |
| Reproducing the release | `release/PROVENANCE.json`, `release/SHA256SUMS.txt`, `release/RELEASE_NOTES.md` |
| Security or safety concerns | [SECURITY.md](SECURITY.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |

## Issue etiquette

- One problem per issue; include commit hash (`git rev-parse HEAD`),
  OS, Python version, and the exact command + output.
- Test failures: note that exactly one failure
  (`test_generator_deterministic`) is expected off the Linux reference
  platform — it is documented, not a bug report target.
- Scientific disagreements are welcome as issues **when framed against a
  specific claim id** (e.g. "H-26's failure condition is too loose
  because…"). "This is all wrong" without a register row is not
  actionable.

There is no real-time chat; the maintainer is one person and response
times vary.
