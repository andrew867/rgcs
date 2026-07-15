# Claim Audit — v3 (Agent 10)

**Date:** 2026-07-15. The v2 audit (`CLAIM_AUDIT.md`) is retained.

## Method
Every claim row added in v3 (CLM-3-000..001, H-15..H-30) checked for:
class validity, observable, controls, failure condition, uncertainty
statement, and firewall compliance (no strong-from-weak lineage).

## Results
- CLM-3-000 (EST, baseline reproduction) / CLM-3-001 (DER, env drift):
  verified against V2_BASELINE_AUDIT; CLM-3-001 partially SUPERSEDED --
  2 of the 4 discrepancies were an undeclared dependency, 1 was fixed
  (V2-WIN-01), 1 remains (NR3-001). Register addenda record this;
  original rows untouched (append-only). COMPLIANT.
- H-15..H-19 (ENG, HG memory software): all five have failure
  conditions; H-15/H-17/H-19 now machine-tested-pass (Agent 08
  persistence), H-16/H-18 machine-tested since Agent 04. COMPLIANT.
- H-20..H-23 (optical): observables + controls + failure conditions
  present; H-21/H-23 are pre-registered NULLS with explicit
  artifact-vs-survivor logic (D6-003). No class upgrades anywhere.
  COMPLIANT.
- H-24..H-28 (node menu): each of the five HYP node definitions carries
  an observable and a retirement condition; measured-node supersession
  (H-07) preserved. COMPLIANT.
- H-29/H-30 (ENG timing gates): failure conditions block phase claims /
  flag drive artifacts respectively; wired into schema rules. COMPLIANT.
- Firewall: no EST/DER row derives from HYP/ENG/SRC inputs; all SRC
  operating points (RG-12/13/14) enter only as protocol parameters.
  VERIFIED by suite firewall tests + row inspection.

## Verdict
No claim-classification defect found in v3 rows. The claim system is
internally consistent and machine-enforced where enforceable.
