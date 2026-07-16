# V4.1 Independent QA Final Verdict (Agent Q1)

Method: fresh adversarial attacks against the INTEGRATED candidate
(tests/v4/test_v4c_q1_adversarial.py), independent of implementer
fixtures, plus re-execution of the standing audits.

## Defects found by this pass (registered BEFORE repair)

- V4C-D-002 (P1): NaN/inf inputs produced NaN alignment envelopes in
  the IOME model -> finite-input validation added; regression kept.
- V4C-D-003 (P1): capability laundering via a lying coupling edge (an
  IOME operator smuggled under elasticity) -> OPERATOR_CAPABILITY_
  FLOOR added to the graph compiler; regression kept.
- (Earlier in the wave, user-identified V4C-D-001, P1: proximity-
  threshold node classification -> corrected with the uncertainty-
  aware rule and a 7-test regression battery.)

## Attacks repelled without change

Classification case/alias tricks; extreme-parameter boundedness
(g2=1e6, bias=1e9); verdict-status injection; frozen-history and
restricted-source audits; independent re-derivation of the 3.906 mm
node comparison (classification tracks uncertainty, not a radius).

## Standing evidence at this commit

Full v4 suite green (incl. 7 Q1 attacks, 7 node-coincidence
regressions); proof bundle regenerated with corrected vocabulary,
115/115 checksums; programmatic audit 19/19; AST import-firewall
clean; provenance linter clean over docs+code; no FDT/lore promotion
in any public doc.

## Verdict

NO OPEN P0/P1. Declared open risks (source files absent; mesh-limited
eye localization; junction comparator untested; user-constructed
capability records are by-design data) are recorded in the risk
register with discriminating actions, not hidden. RELEASE of v4.1.0
recommended.
