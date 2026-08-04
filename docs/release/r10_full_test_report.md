# R10 Full Test and Static Audit

Status: **PASS**

Tested commit: `350a7c3fb60be673f38f92a26ce9cbffab2c0617`

Tested tree: `b4aad42696e10eabf5f77de51d19b1bd24131743`

## Full Suite

```text
python -m pytest tests rgcs_ardk/tests -q --basetemp build/pytest-r10-public-full-final4 --junitxml=build/r10-public-full-final4-junit.xml
```

- Process exit: **0**
- Passed: **8,920**
- Skipped: **16**
- Warnings: **3**
- Failures: **0**
- Errors: **0**
- Xfails: **0**
- Pytest runtime: **1,639.97 seconds**
- Wall runtime: **1,644.1 seconds**

The three warnings are the same `skfem.element.discrete_field`
deprecation warning. They do not change test outcomes.

## Focused Evidence

- Original failure-site rerun: **147 passed, 2 skipped**.
- Release filter, release builder, and privacy gates: **64 passed**.
- Qt WebEngine lifecycle control: **1 passed**, process exit **0**.
- Isolated public candidate: **1,508 passed**, process exit **0**.
- Existing Terra release-filter suite: **38 passed**.

## Filter Audit

The exclusion-first audit classified 3,018 tracked files: 575 safe-public,
94 policy-withheld, 410 quarantine, and 1,939
review-needed. Excluded-term public leaks: **0**. Result: **PASS**.

The JUnit evidence remains local at
`build/r10-public-full-final4-junit.xml`. It is generated evidence and is
not part of the source candidate.
