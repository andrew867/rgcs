# RGCS v4.7.0 — Phase Memory, Worldline Channel Recovery, Phryll Translation Hypothesis

**SOFTWARE_VERIFIED, PHYSICAL_UNTESTED.** No apparatus was built, no
data collected; the entire crystal-translation lane is `SOURCE_CLAIM`
with preregistered plans around it, and no Phryll-detected state
exists in this release by construction. All prior tags untouched.

Full account: [PMWR findings](pmwr/PMWR_FINDINGS.md) · manuscript §13.

## The centre

> A synchronized, calibrated receiver can estimate portions of a
> signal's timing and phase history **only when the observation and
> model make the inverse problem identifiable.**

## Highlights

- **Exact closure is a delay alias.** The 1/4096 s closure window of
  the 4096/20480/40960 family is an alias grid — 4097
  indistinguishable delays per second. The v4.6 synchronization
  feature and the v4.7 ambiguity are the same arithmetic fact. A dual
  coprime lattice (adding a 4375 Hz family) extends the unambiguous
  range ×4096.
- **Recovery that refuses.** Path reconstruction runs behind an
  identifiability gate (rank, condition number, posterior width);
  underdetermined or ill-conditioned cases return `REFUSED` with
  reasons, never a best guess. Unwrapping returns candidate lists.
- **Finite-Q phase memory.** A phase authority's cycle count exists
  only while `PHASE_LOCKED`; the memory horizon is the earlier of
  amplitude death and phase diffusion; infinite-Q and beyond-horizon
  claims are refusals. Two authorities with no synchronization method
  are incomparable regardless of Q.
- **Causality guards.** Arrival reordering is computed and named
  ordinary delay geometry; the audit's output cannot represent
  "causal reversal", and a prose lint refuses reversal language.
  Worldline-indexed proper phase reproduces the validated LEO/GPS
  fixtures — metrology, not travel.
- **Pyramid-ratio audit.** 2a/h at 51.843° = 1.5714157792, within
  ~5×10⁻⁴ of π/2 — carried as `GEOMETRY_IDENTITY` about a chosen
  angle; the Great Pyramid is `ANTHROPOGENIC_STRUCTURE`; the
  mechanism reading is refused in code.
- **Phryll operationalized, not detected.** Five-rung ladder, one
  arrow at a time; a residual requires all eleven ordinary output
  channels bounded plus a sham-drive control — the source's own
  power-not-engaged episode is preserved as the expectation-effect
  warning. A test greps the package to keep any detected-state out.
- **Workbench + workbook.** New Evidence-ledger desktop panel (14
  panels now) and three PMWR workbook sheets (24 sheets total)
  generated from the canonical store.
- **Governance.** v4.6 was independently re-verified by object ID and
  remote download before branching; only CI-verified commits reached
  main. `enforce_admins` remains OFF pending an operator action —
  documented in the findings.

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 1113 passed
python -m pytest tests/v4/ -q -k pmwr          # the PMWR suite
python tools/qa_audit_v4.py --fast             # 19/19
```

## Boundary

Nothing here is evidence that a crystal translates phase between
domains, that termination angles direct energy, that any residual
exists, or that any temporal mechanism operates. Calibrated,
preregistered, independently replicated bench evidence would be
required; none exists.
