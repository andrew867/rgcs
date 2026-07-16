# Agent 13 Handoff — Documentation, QA, Repair, CI, Release

Status: COMPLETE. G1–G30 all green; tags v4.0.0-alpha → v4.0.0-rc1
(05a427a) → v4.0.0.

- Role A: docs/RGCS_V4_TECHNICAL_MANUSCRIPT.md,
  CANONICAL_110MM_CASE_STUDY.md, EYE_METHODOLOGY.md,
  V4_MODELLING_GUIDE.md, V4_API_REFERENCE.md, USER_GUIDE_V4.md,
  RELEASE_NOTES_V4.md, plans-v4/LESSONS_LEARNED_V4.md — all carrying
  the required wording (computational-only, Source-claim eye, no
  experimental confirmation, CPU authority, distinct geometries).
- Role B: tools/qa_audit_v4.py (19 independent checks, 19/19) +
  QA_REPORT_V4, DEFECT_REGISTER_V4, NUMERICAL/QUARTZ_TENSOR/
  PIEZOELECTRIC/ACCELERATOR/EYE_DIAGNOSTIC/REFERENCE_SYSTEM/
  REPRODUCIBILITY/SCREENSHOT audits, RELEASE_RECOMMENDATION (gate
  table).
- Role C: V4-D-002/003/004 registered → reproduced → regression-tested
  → fixed → evidence regenerated. No open P0/P1.
- Role D: CI 10/10 green at rc1 (portable 3-OS × py3.11/3.13, pinned
  reference, v4-demo 3-OS clean-workspace demo + fast audit);
  tools/build_v4_release.py assets + PROVENANCE + SHA256SUMS;
  GitHub release v4.0.0 with 9 assets.
- Zenodo: per docs/DOI_RELEASE_GUIDE.md the GitHub integration
  auto-archives the published release; the on-Zenodo metadata
  verification + publish click (docs/ZENODO_METADATA_V4.md) and the
  follow-up CITATION.cff DOI commit are the ONLY human steps left.
