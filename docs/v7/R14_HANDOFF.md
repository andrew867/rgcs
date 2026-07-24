# R14 Handoff — from R13 (v7.0.0)

**From:** RGCS R13 / v7.0.0.
**State at handoff:** all 48 R13 phases carry a complete receipt
(`docs/v7/receipts/`); 32 `r13/` modules; 5638 tests pass; firewall and
packaging gates green; verdict
`R13_GREEN_COMPLETE_SOFTWARE_SIMULATION_AND_EXPERIMENT_ARCHITECTURE_NO_BENCH_CLAIM`.

There is **no hidden deferred work**: every blocked item below is already a
complete `BLOCKED_MISSING_INPUT` (or `PREREGISTERED_NOT_RUN`) receipt, not a
silently dropped phase.

## What R13 leaves open (the honest blocked set)

These are blocked on inputs that do not exist in this environment. Each is
the natural first task for R14 **if and only if** the corresponding input
becomes available.

| Blocked input | Unblocks | R13 receipt |
|---|---|---|
| A built bench (apparatus, detector stack) | phases 25–30 execution | 20, 21, 25–30, 45 |
| DFT/DFPT quartz force constants | real phonon spectrum | 08, 31 |
| A licensed neutron facility + beam time | INS validation | 33, 34 |
| Conventional preliminary bench data (Raman/BVD) | a submittable beamtime proposal | 34, 35 |
| An independent known-destination vector set | the decoder falsification run | 37, 42 |

## Standing rules R14 inherits (do not weaken)

1. **Simulation ≠ measurement; certificate ≠ evidence.** A cross-domain
   transfer stays an `ENGINEERING_CANDIDATE` until its falsifying measurement
   is performed.
2. **No promotion** — the seven refusals in `r13/claimtypes.py`, exercised by
   `tests/v6/test_r13_redteam.py`.
3. **Blocked is stated, not hidden.**
4. **Every null needs power on planted data** (the R10.6 band-clustering
   lesson) — carried into `experiments`, `holdout`, and `preregister`.

## Concrete R14 candidate tasks

- If a bench is built: run the preregistered experiments (25–30) against the
  sealed protocols; do **not** unblind before committing (`holdout`,
  `preregister`).
- If DFT force constants arrive: replace the analytic toy force constants in
  `euphonic` and re-derive the dispersion/DOS; compare to `atomistic`.
- Run the decoder falsification protocol (phase 42) against genuinely
  independent known-destination vectors; the current alias-set result is
  evidence **against** a unique decode — a real test could confirm or reject.
- Extend the coupling-graph search (`bridgegraph`) with any newly certified
  bridges; each new composite edge needs its own certificate.

## Provenance note (post-tag rule)

Per R04/R65 and the R13 release contract: the `v7.0.0` tag is immutable and
already contains every release-owned artifact. Any confirming measurement run
recorded after tagging is committed to `main` **separately**, never by
rewriting the tag.
