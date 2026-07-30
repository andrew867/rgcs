# Documentation Acceptance Matrix

| ID | Requirement | Verification |
|---|---|---|
| DOC-001 | A new user can create a specimen without reading source code. | clean-user walkthrough |
| DOC-002 | The manual distinguishes measured and computed frequencies. | claim-lint test |
| DOC-003 | Every JSON example validates. | schema test |
| DOC-004 | Every current command exists. | help-tree test |
| DOC-005 | Every release example executes. | documentation integration test |
| DOC-006 | Windows and Linux installs are covered. | clean VM or CI jobs |
| DOC-007 | Geometry conventions have diagrams or unambiguous text. | human review |
| DOC-008 | Unknown orientation produces a range or refusal. | solver test |
| DOC-009 | Proof bundle verification is documented. | end-to-end test |
| DOC-010 | Research hypotheses carry non-claim boundaries. | claim audit |
| DOC-011 | No public document contains private personal provenance. | privacy scan |
| DOC-012 | The consolidated manual matches the individual documents. | build and diff gate |
