# R11 Shell Sequence and Codec Report

**Authority:** RGCS R11 / v6.0.0 (candidate)
**Scope:** three range readings with missing timestamps, and the lossless / lossy envelopes over one twelve-digit address.
**Last verified commit:** v5.9.0 baseline (branch v590-r11)
**Prerequisites:** [R11_SPEC.md](R11_SPEC.md)
**Related code / tests:** `r11/shelladdr.py`, `tests/v6/test_r11_shelladdr.py` (45 tests), `tests/v6/test_r11_redteam.py`
**Known limitations:** the three ranges are reported values, not observations made by this software. Timestamps are absent, so no kinematic quantity exists to be estimated. The mixed-radix field layout is DECLARED by the module, not decoded from anything.
**Next review trigger:** arrival of any timestamp for any of the three readings, or an externally justified re-ordering event.

## Verdict

`r11.shelladdr.shelladdr_report()["verdict"]` returns:

> **`MOVING_SHELL_SEQUENCE_RETAINED_WITHOUT_KINEMATICS`**

## Part 1 — the three shell readings

`MOVING_SHELL_SEQUENCE_A` holds three reported ranges of one object, retained
in the order given, which is ordered inward:

| obs_id | range (mi) | range (km, exact) | radius (Earth radii) | timestamp |
|---|---|---|---|---|
| `SHELL_A_OBS_1` | 3478 | 5597.298432 | 1.8785576437760974 | **null** |
| `SHELL_A_OBS_2` | 1903 | 3062.581632 | 1.4807059218245868 | **null** |
| `SHELL_A_OBS_3` | 1238 | 1992.367872 | 1.3127240836672824 | **null** |

`timestamp_class` is `TIMESTAMPS_MISSING` on every row and on the sequence.
`ordered_inward` is `true`; `order_class` is `CANDIDATE_ORDER` — the order in
which the readings were reported, not an order established by a clock.

The conversion constants are carried as exact rationals: one mile is
`25146/15625` km, and `R_E = 39587613/10000` mi = `497735058249/78125000` km
(= 3958.7613 mi = 6371.0087455872 km). That value reproduces every reference
radius above to better than 1e-9. A rounded 6371.0 km does **not** — it misses
by about 1.2e-6 — so the reproducing value is the one asserted throughout.

### No speed, no orbit, no ETA

Speed is a range difference divided by a time difference. With the timestamps
missing there is no denominator — not an uncertain one, not a wide one, *none*.
An orbit needs position and velocity, or three timed positions; with the clock
removed, an infinite family of trajectories passes through the same three
radii, from a slow descent over weeks to a hypersonic pass in minutes, and
nothing in the readings distinguishes them. An arrival time is a speed
extrapolated forward and inherits the emptiness twice over.

So `derived_kinematics` is `null`, and `refuse_speed`, `refuse_orbit` and
`refuse_eta` each raise a typed `ShellAddrError` (red-team attack 7). Supplying
a plausible interval would not *estimate* the missing quantity; it would
**manufacture** it, and the result would then look exactly like a measurement.

`refuse_reordering` protects the sequence: a model that fits better under some
permutation has not found a better fit, it has chosen its data (attack 6).

## Part 2 — one twelve-digit address, through envelopes

The address is preserved exactly and rendered four mutually consistent ways:

- decimal `344478312553` — 12 digits
- bit length **39**
- octal `5006440364151`
- binary `101000000110100100000011110100001101001`

Octal and binary both round-trip; `all_consistent` is `true`.

### The 42-bit envelope — LOSSLESS

`DECIMAL_PRESERVING_42_BIT`: a 2-bit header plus a 40-bit payload, total 42
bits, serialized as **exactly 14 octal digits** (`05006440364151`). The payload
width is justified by `2**39 < 10**12 <= 2**40`, and both halves of that
inequality are asserted. `bits_required` 39, `bits_available` 40,
`bits_lost` **0**, `round_trip` **true**.

What the round-trip proves is stated in the code itself: that the *frame* is
faithful. A reversible envelope **relocates** information and never **creates**
it, so an exact round-trip is necessary but never sufficient to claim the
address has been decoded.

### The 36-bit envelope — LOSSY, with explicit bit accounting

`HCM_NATIVE_36_BIT`: 36 bits, **exactly 12 octal digits**. Thirty-six bits
cannot hold a thirty-nine-bit value, and the module accounts for the shortfall
rather than hiding it:

- `bits_required` 39, `bits_available` 36, **`bits_lost` 3**
- truncated high bits: value **5**, binary `101`
- retained value: **880928873**
- **`aliasing_factor` 8** — eight distinct addresses collide onto every
  surviving 36-bit code
- `exact_round_trip` **false**

`refuse_lossy_as_lossless` raises rather than let a truncated address be
presented as a faithful one (attack 5). Compression that discards is not
compression that reveals.

### Mixed radix — LOSSLESS, but DECLARED

`MIXED_RADIX_SEVEN_FIELD` splits the value across seven fields:

| field | radix | value |
|---|---|---|
| shell | 8 | 2 |
| face | 6 | 1 |
| local_coord | 67108864 | 24663706 |
| phase | 4 | 3 |
| epoch_class | 3 | 2 |
| parity | 2 | 0 |
| revision | 16 | 9 |

Capacity 1236950581248 ≥ value 344478312553; `round_trip` true, `bits_lost` 0.
The report flags `layout_is_declared_not_decoded: true`. The field names and
radices are the module's own invention. An exact round-trip shows the layout is
faithful; it says nothing whatever about whether the address is organised this
way.

### Negative controls

`NEGATIVE_CONTROL`: a 48-bit BCD encoding (wider than the packed form, exactly
reversible) and a digit reversal (`355213874443`, an involution, exactly
reversible). Both are lossless and neither exposes anything. They exist to
calibrate what a clean round-trip is worth: **nothing on its own.**

## The never-parse-8-or-9-as-octal rule

The symbols `8` and `9` do not exist in base 8, so a decimal digit string
containing them has no octal value at all. `refuse_decimal_digits_as_octal`
raises instead of silently mangling it — red-team attack 4 calls it with
`"344478312553"`, which contains 8s, and it raises a typed `ShellAddrError`.
Any tool that "reads" such a string as octal has produced a number by
corruption, not by conversion.

`refuse_header_semantics_from_target` completes the set: a header meaning read
off the one number it was chosen to fit is retrofitted, not tested.

## Non-claims

This does not say the three readings are false, and it does not say nothing was
moving. It says three ranges with missing timestamps carry no speed, no orbit
and no arrival time. It does not say the twelve-digit value is meaningless, and
it does not say no encoding exists — it says no decoding has been demonstrated.
No ship, no external transmission, no decoded location.

PHYSICAL_VALIDATION_NOT_CLAIMED
