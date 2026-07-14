# Assumptions Register — RGCS v3 / RSCS 1.0

Append-only. Every assumption gets an ID, owner agent, and a validation
or retirement path.

| ID | Date | Assumption | Owner | Validation path | Status |
|---|---|---|---|---|---|
| A3-001 | 2026-07-14 | The Linux-generated golden CSVs remain the authoritative numerical reference; cross-platform reruns may differ in the last ulp without invalidating them. | 01 | Rerun v2 suite in pinned Linux/Py3.11/numpy 2.4.4 container (CLM-3-001). | open |
| A3-002 | 2026-07-14 | v2's declared limitation "built and verified on Linux only" fully explains the 3 Windows integration failures (root cause V2-WIN-01 confirmed for step 7; steps 4/4b share the OS-path class, confirmed by code inspection of `services/bundle.py`, presumed for workspace listing). | 01 | v3 Windows portability fix + regression tests (MIG-CODE-07). | open |
| A3-003 | 2026-07-14 | The prompt-pack `current_release/` copies duplicate `archive/v2.0.0/release/` content; the archive copies are authoritative. | 01 | SHA256 spot-check (RELEASE_NOTES/QA_REPORT matched). | accepted |
