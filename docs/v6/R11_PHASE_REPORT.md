# R11 Phase Report — The Four-Fraction Alphabet and Its One-Channel Loss

**Authority:** RGCS R11 / v6.0.0 (candidate)
**Scope:** the four-symbol rational phase alphabet, the 15-degree lattice, the phase-versus-spin distinction, and the negative result about single-quadratic readout.
**Last verified commit:** v5.9.0 baseline (branch v590-r11)
**Prerequisites:** [R11_SPEC.md](R11_SPEC.md)
**Related code / tests:** `r11/phasealpha.py`, `tests/v6/test_r11_phasealpha.py` (37 tests), `tests/v6/test_r11_redteam.py`
**Known limitations:** everything here is exact arithmetic over supplied rationals. No field is applied, no atom is interrogated, no apparatus exists, and no symbol has ever been read out.
**Next review trigger:** an independent mechanism that links a phase fraction to a nuclear spin quantum number, or any measured readout channel.

## Verdict

`r11.phasealpha.phasealpha_report()["verdict"]` returns:

> **`FRACTIONAL_PHASE_ALPHABET_SPECIFIABLE`**

Specifiable. Not transmitted, not received, not physical.

## The alphabet

`PHASE_ALPHABET_A` is four supplied rationals read as fractions of one turn.
Arithmetic is kept exact with `Fraction`, so nothing rounds at a claim
boundary; floating point appears only where trigonometry forces it.

| pair | literal | phase (turns) | degrees | 15° sector | cos² | sin² |
|---|---|---|---|---|---|---|
| `23` | 2/3 | 2/3 | **240.0** | **16** | 0.25 | 0.75 |
| `34` | 3/4 | 3/4 | **270.0** | **18** | 0.00 | 1.00 |
| `56` | 5/6 | 5/6 | **300.0** | **20** | 0.25 | 0.75 |
| `72` | 7/2 | **1/2** | **180.0** | **12** | 1.00 | 0.00 |

All four land on the 15-degree lattice (`on_15_degree_lattice: true`,
`sector_degrees: 15.0`, `sector_count: 24`).

The fourth row is the interesting one. `7/2` turns **reduces mod one turn** to
`1/2` turn = 180°; `reduces_mod_one_turn` is `true` for that row and `false`
for the other three. The reduction has a visible consequence: scaling the
literal by 192 gives 672, while scaling the *phase* by 192 gives 96, so
`literal_and_phase_scalings_agree` is **false** for `72` and true for the rest.
Whether a symbol is scaled before or after reduction therefore changes the
answer, and the module records both rather than picking one.

## 7/2 as a phase is not I = 7/2 as a nuclear spin

The Cs-133 ground-state nuclear spin quantum number is also written 7/2. The
module holds the two apart explicitly:

| | `RATIONAL_PHASE` | `NUCLEAR_SPIN_I` |
|---|---|---|
| value | 7/2 | 7/2 |
| kind | angular turn (dimensionless fraction of one turn) | quantum number labelling an angular-momentum representation |
| reduces mod one turn to | 1/2 | **null — it does not reduce** |
| degrees | 180.0 | **null — it has no degree measure** |

`numerically_equal: true`, `same_kind_of_quantity: false`, and the status is
**`CANDIDATE_CORRESPONDENCE`** — which is the ceiling, not a step toward
something stronger. A spin quantum number does not reduce mod one turn and has
no degree measure; a phase does both. Equality of the numeral in two contexts
is a coincidence of notation until an independent mechanism links them.

`refuse_spin_phase_conflation` raises when the two are merged (red-team attack
12), and `r11.isotope.refuse_isotope_conflation` raises on the parallel move at
the isotope end.

## The negative result: one quadratic channel loses a symbol

This is the headline finding of the module, and it is arithmetic rather than
opinion.

A quadratic observable — `cos²(θ)`, the shape a quadratic Zeeman projection or
any intensity-only detector has — maps **240° and 300° to the same value,
0.25**, because cos(240°) = −1/2, cos(300°) = +1/2, and squaring destroys the
sign. The report records it as:

- `colliding_pair`: `["23", "56"]`
- `colliding_degrees`: `[240.0, 300.0]`
- `shared_cos_squared`: `0.25`
- `symbols_in`: **4**, `distinct_values_out`: **3**
- verdict: **`SINGLE_QUADRATIC_CHANNEL_INSUFFICIENT`**

Pairing `cos²` with `sin²` does not rescue it: `sin² = 1 − cos²` is the same
channel written backwards, not a second independent one, so it repeats the same
collision and adds no information.

### What would recover all four symbols

`recoverability` in the report:

| channel | recovers all four? |
|---|---|
| `SIGNED_QUADRATURE` | **yes** |
| `TWO_ORTHOGONAL_MAGNETIC_FIELD_AXES` | **yes** |
| `IN_PHASE_AND_QUADRATURE_MICROWAVE` | **yes** |
| `RAMSEY_ZONES_WITH_RELATIVE_PHASE` | **yes** |
| `SINGLE_QUADRATIC_ZEEMAN_PROJECTION` | **no** |

The common ingredient in the four that work is *sign sensitivity*. Any readout
that discards the sign of the projection cannot distinguish 240° from 300°, no
matter how precise it is. Precision does not fix a degeneracy.

These are arithmetic sketches of channels. None of them has been built. The one
firm result among them is the negative one.

## Unit discipline

Frequency and angular frequency are carried separately and never mixed. Units
declared: `CYCLES_PER_SECOND`, `RADIANS_PER_SECOND`, `DEGREES`, `TURNS`, with
`omega = 2*pi*f` and `f = omega/(2*pi)`. `refuse_unit_confusion` raises when two
quantities of different unit kinds are combined by number alone — red-team
attack 11 tries to equate 180 degrees with 180 Hz and gets a typed
`PhaseAlphaError`. The guard is not a blanket refusal: comparing 180° with 90°
is allowed, because those are the same kind of quantity.

## Non-claims

This does not say the four rationals are a code, that they were transmitted, or
that anything physical selects them. It does not say the supplied 7/2 is the
Cs-133 nuclear spin. It does not say any apparatus exists, that any channel was
built, or that any symbol was ever read out. No decoded location, no unique
epoch, no new particle, no physical crystal effect.

PHYSICAL_VALIDATION_NOT_CLAIMED
