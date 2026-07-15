# Publication Readiness Report (Agent 12)

**Date:** 2026-07-15. **Method:** the repository was read end-to-end as a
first-time engineer would encounter it; every confusing point was listed;
everything fixable without touching mathematics or software behavior was
fixed; the audit loop was repeated until no obvious polish item remained.

## 1. First-contact audit — confusions found and resolved

| # | Confusion (fresh-eyes) | Resolution |
|---|---|---|
| 1 | README was a v2 document with a v3 paragraph bolted on | full rewrite: architecture diagram, five-label table, quick start with *expected* test output, figures, publications, roadmap, limitations, acknowledgements |
| 2 | `manuscript/` vs `manuscripts/` — near-identical names, different eras | `manuscript/README.md` disambiguates at the directory boundary; README table lists both |
| 3 | ~60 files in `docs/` with no map; v2/v3 QA files share base names | `docs/README.md` index: start-here table, frozen-record vs living-register conventions, explicit note that the QA name pairing is deliberate |
| 4 | Version drift: pyproject `3.0.0a1` vs CITATION/tag `3.0.0-rc1` | pyproject → `3.0.0rc1` |
| 5 | RSCS acronym never expanded at first use in README | expanded in the header |
| 6 | LaTeX build intermediates tracked in `manuscript/` | untracked + gitignored (pdf/tex/bbl/bib/figures/tables retained) |
| 7 | Stale `.gitkeep` files in populated directories; `release/.gitkeep` beside real artifacts | removed (empty skeleton dirs keep theirs) |
| 8 | Two dead documentation references (v2 test-report path; a planned corpus doc that became the Historical Companion) | both re-pointed (link scan now clean) |
| 9 | No contributor on-ramp; the governance rules lived only in agent briefs | CONTRIBUTING / CODE_OF_CONDUCT / SECURITY / SUPPORT / DESIGN_PHILOSOPHY / RESEARCH_HISTORY / FAQ authored |
| 10 | The expected single test failure off-Linux would read as a broken install | called out in README quick start, FAQ, and SUPPORT |
| 11 | No visual anywhere a browser renders | two generated PNGs (`docs/images/`) in README, produced from the same tested code paths as the manuscript figures |

Remaining sweep found no further items: markdown link scan clean;
terminology scan clean (K = i·2πg convention uniform in substance;
Hydrogenuine spelling uniform; five-label vocabulary consistent);
LICENSE/CITATION.cff/CHANGELOG present and current.

## 2. Verification results (this commit's tree)

| Check | Result |
|---|---|
| Full test suite | **376 passed / 1 failed** — the documented NR3-001 golden byte-equality (Linux-reference-only) |
| Frozen baseline | `git diff 715486b HEAD -- archive/v2.0.0` empty |
| Schema validation | 12/12 targets OK |
| Generated docs freshness | `generate_optical_comparison.py --check` OK |
| Release SHA256SUMS | all files verify |
| Release ZIP contents | 4 manuscript PDFs + per-manuscript checksums; source zip contains README/LICENSE/CITATION and excludes internal-docs/.venv |
| Manuscript layout | 4× (0 undefined refs, 0 overfull boxes) — unchanged since Agent 11 |
| Markdown links | all resolve |
| CITATION.cff | cff 1.2.0, v3.0.0-rc1, honest abstract; DOI steps documented in `PUBLIC_COMMUNICATION.md` (Zenodo integration before the GitHub release, badge in follow-up) |

## 3. What was deliberately NOT changed

- No mathematics, no equations, no architecture (Agent 12 charter).
- The v2 frozen record (`archive/v2.0.0/`, frozen docs, v2 manuscript
  content) — untouched beyond removing untracked-able build litter.
- The release tag `v3.0.0-rc1` (tags are never rewritten); the refreshed
  release assets record their own commit in `PROVENANCE.json`.
- Historical statements in agent handoffs (dated snapshots by design;
  the docs index says so).

## 4. Blockers

**None found by this audit.** The single pre-existing gate stands
unchanged: the Linux CI legs have not yet executed (the workflow exists;
this environment is Windows-only).

## 5. Recommendation

**Publish.** Concretely:

1. Push `main` + tags; let the CI matrix run.
2. When the Linux legs are green: tag **`v3.0.0`** at this commit,
   rebuild `release/` via `tools/build_v3_release.py <sha>` (updates the
   source zip name/PROVENANCE), and publish the GitHub release using the
   title/announcement in `docs/PUBLIC_COMMUNICATION.md`, attaching the
   `release/` artifacts.
3. If a Linux leg fails: it lands in `DEFECT_REGISTER.md` first,
   fix-forward, re-tag — per project discipline.
4. Optional same-day: enable Zenodo before publishing the release; add
   the DOI to CITATION.cff in a follow-up commit.

Should CI stay red for reasons outside the code (runner availability),
`v3.0.0-rc1` remains a publishable, honest release candidate as-is.
