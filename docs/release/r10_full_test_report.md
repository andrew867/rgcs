# R10 Full Test and Static Audit

Status: **PASS**

Tested commit: `592a1654897a488f432c66fde8d922ef4f40714b`  
Tested tree: `76ed57d532f93f3b94baf7ae82908c1f204ede51`

## Full Suite

```text
python -m pytest tests rgcs_ardk/tests -q --basetemp build/pytest-r10-public-full-final2 --junitxml=build/r10-public-full-final2-junit.xml
```

- Process exit: **0**
- Passed: **8,918**
- Skipped: **16**
- Warnings: **3**
- Failures: **0**
- Errors: **0**
- Xfails: **0**
- Pytest runtime: **1,617.44 seconds**
- Wall runtime: **1,623.2 seconds**

The three warnings are the same `skfem.element.discrete_field`
deprecation warning. They do not change test outcomes.

## Focused Evidence

- Original failure-site rerun: **147 passed, 2 skipped**.
- Release filter, release builder, and privacy gates: **62 passed**.
- Qt WebEngine lifecycle control: **1 passed**, process exit **0**.
- Existing Terra release-filter suite: **38 passed**.

## Filter Audit

The exclusion-first audit at the tested commit classified 3,016 tracked
files: 532 safe-public, 96 policy-withheld, 410 quarantine, and 1,978
review-needed. Excluded-term public leaks: **0**. Result: **PASS**.

The JUnit evidence remains local at
`build/r10-public-full-final2-junit.xml`. It is generated evidence and is
not part of the source candidate.
