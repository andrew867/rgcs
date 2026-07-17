# V4X2 QA verdict (Q07)

Scope: the Post-v4.2 Emergent Resonator and Structured-Wave Expansion
programme. Attacks per the pack's Phase 10 list, implemented as
executable tests in `tests/v4/test_v4x2_qa.py` so they re-run on every
build.

## Verdict

**RELEASE APPROVED** as the next semantic version — a
software-and-protocol release. No open P0/P1. Nothing physical
exists; every physical path is capability-gated and currently
refuses.

## Attacks and outcomes

| Attack | Outcome |
|---|---|
| Fake ledger completion (validated status, bogus symbol) | repelled — gate B_symbols fails on sabotage (tested) |
| Measured/targeted status confusion | repelled — constructor + certificate refuse (tested) |
| Trim overshoot / blind burn loop | repelled — selector returns None rather than the least-bad burn |
| Mode switching hidden by index | repelled — MAC tracking catches permutation |
| Source laundering into quartz | repelled — firewall raises for all five sources |
| Playground evidence upgrade | repelled — REFERENCE_MATHEMATICS_ONLY, label survives comparison |
| Synthetic flag stripping | repelled — stripped certificate fails HMAC verify; unflagged session refuses to load |
| Unsafe automation | repelled — no machine capability, no execution; S01 evidence required |
| Private lore leakage | repelled — internal-docs untracked; policy public, content never |
| Product overclaims | repelled — tier vocabulary enforced; certificates print claims-not-made |
| Stale test/coverage counts | repelled — metadata authority + guard |
| Dramatic sentence detachment | repelled — caveats live inside the current claim card; correction trail append-only |
| Resource overconfidence | repelled — range predictions; preflight refuses the known-infeasible case |

## What development-time QA actually caught (the honest part)

These defects were found and fixed DURING the build, which is what
the attacks are for:

1. **Triangular-transport sign error (P1, scientific).** The
   substrate-removal Fermi factor had the wrong sign, so the cluster
   saturated full at any bias and the paper's redistribution window
   could not exist. Caught because the redistribution test could not
   find its window; fixed by rederiving the rate. The broken version
   is in git history.
2. **Angular-Nyquist aliasing (P2).** The partial-array decomposition
   reported orders outside the sampling band, making m=1 and m=−3
   indistinguishable claims. Fixed: the API now reports only the
   alias band and says why (→ ORPH2-007 design rule).
3. **Flat-data NaN in the Lorentzian fit (P2).** A perfectly flat
   sweep produced NaN instead of `fitted: None`.
4. **Twin init-order crash (P2).** Caught on first run.
5. **The census corrected the programme's own headline (the most
   important catch).** Y03's unbiased census showed the v4.1 and
   v4.2.1 coordinates are two resolution-dependent estimates of ONE
   apex feature — and that the feature has a symmetric family
   (female-apex twin, mid-shaft pair). Claim card v3 → v4; the
   correction trail records it. **The independent replication agent
   existed precisely to catch the biased-selection narrative, and it
   did.**

## Boundary spot-checks

- Resonator ≠ oscillator: enforced (`is_oscillator` requires
  Barkhausen).
- Printed silica ≠ quartz: enforced (registration refuses).
- Neutron mathematics ≠ neutron physics: enforced (transfer
  firewall).
- Reference model ≠ quartz evidence: enforced (playground firewall +
  per-source guards).
- Synthetic ≠ measured: enforced end to end (ledger → session →
  certificate → QR payload).

## Residual risks (named, not hidden)

- The census ran at cl3.0/cl2.0; a cl1.5 census level needs a quiet
  memory window (queued, ORPH2-005-adjacent).
- Q04's filtration benefit is demonstrated on a synthetic system
  only; scored WEAK_ANALOGY in the intuition ledger accordingly.
- The Q02 model is qualitative by declared scope; nobody should read
  its currents as fits to the paper.
