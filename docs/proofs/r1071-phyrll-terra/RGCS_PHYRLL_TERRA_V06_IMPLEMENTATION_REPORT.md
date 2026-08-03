# RGCS Phyrll / Terra v0.6 — implementation report

**PUBLICATION HOLD. No tag, no push.** Parent `eda8938`, clean worktree.
Supersedes the v0.5 lane: v0.6 = v0.5 + coefficient roles + calibration
lane + release filter, per the pack's own correction note.

**A successful run does not prove the craft.** What exists after this run
is a reproducible mathematical/simulation scaffold whose remaining
blockers are measured material parameters, physical field maps and
controlled bench receipts — exactly as the success criterion defines.

No claim of antigravity, reactionless propulsion, free energy, source
authentication, flight validation, or nonhuman communication is made
anywhere, and tests enforce the absence structurally.

---

## 1. Exact coefficient table `EXACT_ARITHMETIC`

The mandated identity passes:

```
q = 27/93 = 9/31                        (Fraction reduction, asserted)
eta_calc = 47/63 · 9/31 · (311 − 9/31) = 64672/961 = 67.2966…
round(·, 1) = 67.3  ✓
```

**The source figure and the derivation are not the same number.**
673/10 − 64672/961 = **33/9610** exactly (≈ 0.00343). They agree at one
decimal place only. Recorded so rounding agreement cannot quietly become
an identity.

| Coefficient | Exact | Role | Claim |
|---|---|---|---|
| η_F source | 673/10 | A force/coupling | SOURCE_PROVENANCE |
| q | 9/31 | A | EXACT_ARITHMETIC |
| σ | 47/63 | A | EXACT_ARITHMETIC |
| A | 311 | A | SOURCE_PROVENANCE |
| η_F calc | 64672/961 | A | EXACT_ARITHMETIC |
| c_g | 631/732 | B geometry | SOURCE_PROVENANCE |
| 57.3 | 573/10 | B | SOURCE_PROVENANCE (shorthand, ≠ 180/π) |
| θ_tilt = c_g·57.3 | 361563/7320 ≈ 49.394° | B | MODEL_OUTPUT |
| 142/897 | — | C calibration | UNRESOLVED |
| state47 = 297·142/897 | 14058/299 ≈ 47.017 | C | UNRESOLVED |
| small_angle | ≈ 9.070° | C | UNRESOLVED |
| 236805/142 | ≈ 1667.641 km | C | MODEL_OUTPUT |

The three angle readings of c_g are inequivalent — acos(631/732) =
30.463°, asin = 59.537°, ×57.3 = 49.394° — and **none is selected**
(`UNRESOLVED`). 29.7, 297634, 47 and 23 remain candidates with no
assigned role.

## 2. Ring masks `MODEL_OUTPUT`

All required behaviours verified:

| Mask | Active | \|S\| | arg(S) |
|---|---|---|---|
| all active 37/37 | 37 | **0 exactly** | — |
| nominal 35, adjacent blanks | 35 | 1.9928 | 4.86° |
| nominal 35, near-opposite blanks | 35 | 0.0849 | 87.6° |
| steering 33, adjacent | 33 | 3.9283 | 14.59° |
| steering 33, spread | 33 | 0.1226 | 131.4° |

- adjacent blanks give strong S; near-opposite blanks cancel >20×
  harder (37 is odd, so exact opposition does not exist — k=0/k=18 is
  the closest pair);
- steering direction follows arg(S) exactly (single blank at k → angle
  2πk/37, asserted);
- rotation invariance: rotating a mask rotates arg(S) by the cell pitch
  and preserves |S| to 1e−12;
- randomized null (equal active count, 500 trials): mean |S| = 1.27,
  max = 1.99 — the adjacent-pair pattern **is** the 2-blank extreme, so
  a "strong" |S| of ~2 is the family maximum, not an anomaly;
- uniform weights give d_eff = 0 (sum of the 37 roots of unity).

## 3. Carrier and coupled power

```
f_ext = 4096 × 411 = 1,683,456 Hz        411/37 = 11 + 4/37  (exact)
I_k(t) = I0·a_k·cos(2π f_ext t − 4·φ_k + φ0)     (m = 4 winding)
P_ring = ωU/Q,  U = L_eff I_rms² + C_eff V_rms²,  F = η·P_ring
```

**The wall-power rule is enforced in code:** `ring_power_from_wall`
raises unless a separate `eta_couple ∈ (0,1]` is declared. F = η·P_ring
is computed in exactly one audited function and tagged
`BENCH_REQUIRED` — η is a coefficient with units N/W whose value only a
bench can supply.

## 4. Brown annular proxy `PRIOR_ART_ANALOGUE`

Laplace relaxation → finite-difference E → energy density
u = ε₀|E|²/2 → energy-weighted direction proxy. Results (41-grid):

| Configuration | Asymmetry scalar | Direction |
|---|---|---|
| centered symmetric | **0.00000** | — |
| off-center inner electrode | 0.19241 | 0.0000° (the displacement axis) |
| masked 37 cells (4 blanks) | 0.01513 | 52.4° |

The proxy behaves physically: perfect symmetry gives zero, physical
displacement gives the strongest asymmetry along the displacement axis,
and electronic (mask) displacement gives a weaker asymmetry — ~13× weaker
here. **The proxy is a direction of field energy, not a force**; the
module exposes no function computing force or thrust, and a test walks
its namespace to keep it that way. Fixed potentials obey the maximum
principle (asserted).

## 5. Force firewall

Keeps the bounded conventional-subtraction arithmetic in the public
firewall without importing the mixed R10.62-R10.70 research lane.
Even/odd decomposition; harmonic extraction for
a₁V + a₂V² + a₃V³ with the closed-form check that DC+h1+h2+h3
reconstructs the polynomial at phase zero; h3 = a₃V_ac³/4 isolates the
cubic fingerprint; EHD F ≈ Id/μ (vanishes in vacuum, by refusal);
artifact placeholders where an **unmeasured budget blocks any residual
quote** (`residual_quotable = False` until an uncertainty is supplied).

## 6. Tests

**68 new, all passing** (8 coefficients, 12 ring, 15 resonance+firewall,
7 proxy, 9 filter, 9 calibration, 8 boundary/claim). No tautologies,
skips or xfails — checked by grep and by reading. The v0.6 pack's own 10
tests also pass in place, untouched.

## 7. Unresolved

- roles of 29.7, 297634, 47, 23 — candidate order/scale values;
- which c_g angle reading (if any) is intended;
- η_couple, L_eff, C_eff, Q — all bench quantities;
- everything in the calibration lane (see its report).

## 8. Next physical measurements needed

1. η_couple (wall→ring), L_eff, C_eff, Q of a physical ring;
2. a KPFM/field map of any bench article (public control protocol);
3. polarity-reversal force data to run the firewall decomposition on.
