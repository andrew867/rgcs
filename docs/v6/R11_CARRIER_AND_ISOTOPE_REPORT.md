# R11 Carrier and Isotope Report

**Authority:** RGCS R11 / v6.0.0 (candidate)
**Scope:** the crystal-carrier arithmetic audit with its look-elsewhere null and its source-pack discrepancy, and the Cs-137/Ba-137 coarse age with the Cs-133 alias analysis.
**Last verified commit:** v5.9.0 baseline (branch v590-r11)
**Prerequisites:** [R11_SPEC.md](R11_SPEC.md), [R11_PHASE_REPORT.md](R11_PHASE_REPORT.md)
**Related code / tests:** `r11/carrier.py`, `r11/isotope.py`, `tests/v6/test_r11_carrier.py` (29 tests), `tests/v6/test_r11_isotope.py` (38 tests), `tests/v6/test_r11_redteam.py`
**Known limitations:** no crystal, sample or specimen exists or is measured. No activity is counted, no clock is compared, no spectrum is taken. Both results are arithmetic on supplied numerals.
**Next review trigger:** an independently computed mode the rational was not selected on, or a real counted parent/daughter measurement with its closed-system declarations filled in.

## Verdicts

- `r11.carrier.carrier_report()["verdict"]` → **`CRYSTAL_CARRIER_CANDIDATE_ARITHMETIC_ONLY`**
- `r11.isotope.isotope_report()["verdict"]` → **`CESIUM_BARIUM_EPOCH_STILL_NON_UNIQUE`**

## Part 1 — `CRYSTAL_CARRIER_CANDIDATE_A`

### The audited chain, exact

Every step is exact rational arithmetic and every step reproduces:

| step | exact | decimal |
|---|---|---|
| `f_crystal` | 344307/25 | **13772.28 Hz** |
| `f_crystal × 2/3` | 229538/25 | **9181.52 Hz** |
| residual to grouped 9192 | 262/25 | **10.48 Hz** |
| `63/6` | 21/2 | **10.50 Hz** (exact) |
| `9181.52 + 63/6` | — | **9192.02 Hz** (overshoot 0.02 Hz) |
| `9192 × 3/2` | — | **13788 Hz** exactly (the exact base for 9192) |

Relative residual: **0.0011401218…** = **0.11401…%**.

### The pack discrepancy, stated plainly

The source pack describes 13788.00 Hz as *"0.03 Hz below the finest
computational result"*. Computed exactly here:

```
13788.00 - 13772.28 = 15.72 Hz
```

so the exact base for 9192 sits **15.72 Hz ABOVE** the computed mode — wrong in
sign and by a factor of about 500 in magnitude. The report's
`base_difference_sign` field reads `EXACT_BASE_IS_ABOVE_COMPUTED_MODE`. The
module's assessment is that the 0.03 figure most closely resembles the
`9192.02 − 9192 = 0.02` Hz overshoot at the *other end* of the chain. The pack
figure is **not adopted**; 15.72 Hz is the value reported, and it is not quietly
corrected in silence — it is carried as `pack_discrepancy`.

Note the size of it: 15.72 Hz is 0.114% of 13788, which is exactly the size of
the residual the candidate is asking to be forgiven.

### The candidate is target-fitted

`target_fitted` is **true**. `2/3` was chosen *after* 9192 was in view, so the
chain is fitted to its target. `refuse_carrier_selected_after_target` raises on
an unlabelled post-hoc selection (red-team attacks 9 and 10; attack 10 tries the
`13772.28 * 2/3 + 63/6` form specifically and is refused).

### The look-elsewhere null

The preregistered search grid holds **2160** expressions — four registered base
frequencies, four supplied rationals, nine operations, each overlaid with
harmonic and subharmonic orders 1–8. Searching a band of 1000–20000 Hz for
2000 random targets at the same 0.114% tolerance:

- **hits: 691 / 2000**
- **p-value: 0.3455**
- verdict: **`NO_BETTER_THAN_CHANCE`**

A grid this size matches a random target to the observed tolerance far more
often than 1 in 20. Landing near 9192 is what the search does, not what the
crystal says.

### The power control

To show the search is not simply blind, a planted target `(4096 × 3/4) × 5 =
15360` is recovered exactly as `20480 × 3/4`, residual **0**, `detected: true`.
The benchmark can find a real hit. That it calls the 9192 candidate chance is a
finding, not blindness.

### What would change this

An independent computed mode the rational was not selected on; a look-elsewhere
p that survives the full grid; and a physical mechanism that *predicts* the
10.48 Hz correction rather than absorbing it into a chosen fraction.

## Part 2 — the two cesiums are different typed systems

| | Cs-133 | Cs-137 |
|---|---|---|
| system | `cs133_clock_definition` | `cs137_radionuclide` |
| evidence class | **`DEFINITION`** | **`EVALUATED_LITERATURE`** |
| stable | yes | no |
| observable | ground-state hyperfine transition frequency | beta decay to Ba-137 (via Ba-137m, ~94.6%) |
| value | **9 192 631 770 Hz** exactly | half-life **601/20 a = 30.05 a** |
| uncertainty | **0, by definition** | evaluated, not zero |

Cs-133 *gives the second its length*; it does not tell you where you are on the
time axis. A clock tells you how long, never how long ago. Cs-137 is a
chronometer only in the weak, assumption-laden sense any parent/daughter pair
is. `refuse_isotope_conflation` raises when a shared chemical symbol is used to
merge them (red-team attack 12).

## Part 3 — the coarse age model

`t = T_half × log2(1 + R)`, with `R = N_Ba_rad / N_Cs`. Seven declarations are
**mandatory** and all seven are `UNDECLARED` by default: initial stable Ba-137,
parent or daughter loss, contamination, branching data, measurement
uncertainty, formation epoch, measurement epoch. `closed_system_declared` is
**false**, and `refuse_age_without_closed_system_declaration` raises until they
are filled in.

Two facts make those declarations unavoidable rather than ceremonial. Natural
barium is already about **11.232%** Ba-137, so radiogenic and inherited daughter
are not separable by assertion. And branching (94.6% via Ba-137m, 5.4% direct
to the ground state, summing to 1) matters for any **gamma-counting**
measurement, which sees only the Ba-137m branch — even though the total daughter
inventory is insensitive to the split, because both branches end at Ba-137.

## Part 4 — the orientation trap

`ISOTOPE_RATIO_CANDIDATE_A` is the supplied pair (192, 55). A bare ratio does
not carry its own convention, and the two readings give different ages:

| orientation | ratio | age (years) |
|---|---|---|
| `R = 192/55` | 3.4909090909… | **65.1185759177…** |
| `R = 55/192` | 0.2864583333… | **10.9203121624…** |

Difference: **54.198 years**. `orientation_chosen` is `null`;
`orientation_status` is `UNDECLARED_BY_DESIGN`; the coarse interval is reported
as **[10.920, 65.119] years**; verdict
**`ORIENTATION_NOT_DETERMINED_BY_THE_DATA`**. The spread between the legs *is*
the coarse uncertainty, and it is not narrowed by preferring one.
`refuse_orientation_chosen_from_desired_year` raises when the orientation is
picked to land on a preferred calendar year (red-team attack 8).

## Part 5 — the alias analysis: no unique epoch

A coherent carrier gives a phase, and a phase is known only modulo one whole
cycle. For the Cs-133 line over a realistic coarse interval:

- single-carrier alias count: **15 722 775 201 816 374 084**
- second carrier at 10 MHz alone: **17 103 671 282 828 262**
- joint alias count: **17 103 671 283** (n-range 3 446 188 431 – 20 549 859 713)
- reduction factor: **≈ 9.19 × 10⁸**
- `unique`: **false**; `still_ambiguous`: **true**
- verdict: **`ALIASES_REDUCED_NOT_RESOLVED`**

A second coherent carrier is a real constraint and removes most aliases, but the
survivors repeat at the common period `1/gcd(f1, f2)` — here 0.1 s. For any
interval wide enough to have needed a coarse chronometer in the first place, the
survivor count stays far above one. **A unique six-digit-year epoch is therefore
forbidden**, and `refuse_unique_epoch` raises.

## Non-claims

No crystal carries, generates or locks to any caesium frequency. 13772.28 Hz is
not physically privileged. 2/3 is a fraction chosen after the target was known.
63/6 corrects nothing. No sample is counted, no activity measured, nothing
dated. No unique epoch is named. No physical crystal effect is established.

PHYSICAL_VALIDATION_NOT_CLAIMED
