# RGCS R10.8 — Handshake, EMI, 13 MHz, and the 1604/1644 Cues: Findings

**Status:** `SOFTWARE_VERIFIED` · `PHYSICAL_VALIDATION_NOT_CLAIMED`
**Baseline:** v5.7.0 (`977e0b6`)
**Evidence class:** `DERIVED_MATHEMATICS`, conventional literature, and typed source records.
**Hardware:** deferred. **No apparatus built, no signal sent, no EMI measured, no channel opened, no person stimulated, no trade placed.**

---

## Gate Zero

Baseline v5.7.0 / `977e0b6`, tree clean, 3079 tests. Publication
firewall committed-tree CLEAN; history carries only the declared
`PRIVATE_PATH` residual. Private repository `RGCS-private`: 0 remotes,
outside the public worktree, OneDrive-synchronized; Tier-A source
authority (`SRC_JH`, `SRC_LS`, alias `OMEGA_REGION_SOURCE`) and the
preserved CW vectors + Vortex Key carry forward, integrity intact.

## The firewalls come first (P03)

**Module:** [`r10/claimfirewall.py`](../../r10/claimfirewall.py)

The private session contains claims that would be dangerous if acted on:
alleged differential viral effects on hidden human groups, hidden
hybrid/genetically-modified populations, medical predictions, and
investment tips. The content-claim firewall preserves each **as a source
record** and refuses to do anything more with it. It **never** classifies
a real person as nonhuman/hybrid/genetic, never infers biology from race/
geography/appearance/group, never produces pathogen-engineering or
group-targeted medical analysis, never gives medical advice from a
message, never makes a public accusation, and never issues a financial
action. A quarantined claim can only ever be `UNSUPPORTED`,
`CONTRADICTED`, or `UNRESOLVED`; promotion to any evidentiary status is
refused. This is distinct from `r10/firewall.py` (which keeps private
*material* out of the public tree); this keeps unsupported *claims* out
of findings.

## Provenance discipline (P01, P02, P04)

- **[`r10/session.py`](../../r10/session.py)** — an append-only session
  archive. Tier-A **source** records and **operator (AG)** notes are
  separate provenance classes that the type system refuses to merge;
  `raw_text_private` is never emitted publicly; corrections are appended,
  never overwritten. Tier-A attribution is faithful recording, **not**
  empirical evidence.
- **[`r10/nolookahead.py`](../../r10/nolookahead.py)** — no-look-ahead is
  only ever a **self-report** unless independently captured, and the
  module refuses to call it proof. A cue that appeared after a search
  began, or matches remembered prior media, is flagged potentially
  contaminated; a late clock-check or minute-rollover widens the onset
  uncertainty.
- **[`r10/numcue.py`](../../r10/numcue.py)** — a preregistration registry:
  a numeric cue's allowed transforms and search budget are hashed and
  frozen **before** results are inspected, and an unregistered or
  budget-exhausted transform is refused.

## The 1604/1644 cues are not better than chance (P05)

**Module:** [`r10/cue1604.py`](../../r10/cue1604.py)

The tempting relation is `1604 ≈ 925·√3 = 1602.147`. The residual is
exact and reported: `1604 − 925·√3 = 1.853…`, a relative residual of
about **0.116%** — `APPROXIMATE_NOT_EXACT`, never an identity. And against
a preregistered look-elsewhere search over small `a·√b` expressions, a
random target lands equally close **essentially always** (p ≈ 1.0):
`NO_BETTER_THAN_CHANCE`. The search has power — a planted exact grid
target is recovered at ~zero residual. `1644 − 1604 = 40` exactly, and
**no meaning is assigned** to it. A spoken digit readback (`1-6-0-4`) is
kept distinct from a base-10 integer with units.

## The handshake is a software state machine, and there is no human path (P06)

**Module:** [`r10/handshake.py`](../../r10/handshake.py)

The source's "request for communication" is modelled as an ordinary
connection handshake: acquire carrier (4096 Hz), present channel key
(925 Hz), present opening key, address, phase/chirality, request,
acknowledge, message, phase-conjugate return, close. It advances only in
order, refuses replays (nonce), times out, and checksums the message.
**Human exposure is prohibited in every state** — there is no pineal,
brain, subliminal, RF, optical, acoustic, magnetic, or electrical
human-stimulation path, and `refuse_human_stimulation()` raises
unconditionally. The twelve-word opening key and the CW vectors stay
private; the handshake checks an **opaque reference**, never the material.

## The engineering models (P07–P13)

- **[`r10/microcrystal.py`](../../r10/microcrystal.py)** — a 13 MHz quartz
  resonator as a Butterworth–Van Dyke circuit (`fs`, `fp`, `Q`, odd
  overtones). It **refuses** to use the free-space wavelength (23.06 m)
  inside quartz without refractive index, mode, cut, temperature, and
  direction. `RESONATOR_MODEL_ONLY`.
- **[`r10/multiframe.py`](../../r10/multiframe.py)** — exact integer-
  frequency closures: 13 MHz and 4096 Hz close every **15.625 ms**
  (`gcd = 64`), 13 MHz and 925 Hz every **40 ms** (`gcd = 25`), and all
  three every **1 s** (`gcd = 1`). `20.48 = 512/25` exactly. Mixer
  products are enumerated and carry **no assigned meaning**.
- **[`r10/timebase.py`](../../r10/timebase.py)** — the SI second from the
  cesium-133 hyperfine transition (**9 192 631 770 Hz by definition**,
  zero uncertainty by definition, not a measurement), vacuum wavelength,
  and an overlapping Allan-deviation estimator (recovers the τ^−1/2 slope
  on white FM). Primary sources are cited; live measured data is
  `BLOCKED_NO_DATA_SOURCE`.
- **[`r10/emisurvey.py`](../../r10/emisurvey.py)** — a blinded ABAB
  device-on/off EMI survey with three **separate** outcomes (perceived
  quality, measured EMI, instrument readout); correlation among them
  establishes no cause. Null has power on a planted ON-block excess;
  measured data is blocked.
- **[`r10/txline.py`](../../r10/txline.py)** — reflection/SWR, delay, and
  quarter-wave resonance for the "long unterminated line" interferer. Its
  safety firewall **refuses to defeat protective earth** or connect a
  person to earth; grounding never overrides electrical safety.
- **[`r10/envlog.py`](../../r10/envlog.py)** — synchronizes RF/mains/
  magnetic/temperature/acoustic/optical/device/operator streams to a
  common timebase and **refuses to correlate unsynchronized streams**;
  recovers a known injected lag (power).
- **[`r10/pcemi.py`](../../r10/pcemi.py)** — the R10.7 phase-conjugate
  refocus under additive interference. The focusing metric **degrades
  monotonically** with interference power; incoherent noise averages down
  ~√N but a **coherent** interferer does not, and claiming otherwise is
  refused. Reciprocity is still required.

## Binding without retrofit (P14, P15)

- **[`r10/routebind.py`](../../r10/routebind.py)** — binds a handshake
  address to an R10.7 rooted route **only if preregistered**; a post-hoc
  fit is refused as retrofit, and a numeric cue or CW vector may not be
  silently converted into a coordinate or route index. Bound routes still
  carry the light-time floor and refuse zero-time transit.
- **[`r10/memhandshake.py`](../../r10/memhandshake.py)** — the handshake
  over the R10.6 fading-memory crystal: addressed write, destructive
  read, refresh-to-retain, ordered readout. A frame past the retention
  window is unreadable, and a memory claim without demonstrated ordered
  readout is refused (a decay curve alone is ordinary relaxation).

## Time-disciplined comparison and correlation (P16, P17)

- **[`r10/extcompare.py`](../../r10/extcompare.py)** — compares the
  session against an external corpus by **publication time**: an item
  published after the session cannot support a prospective claim, only a
  retrospective coincidence check. Semantic nulls, multiplicity, and an
  independence score guard against shared-vocabulary artifacts.
- **[`r10/skycorr.py`](../../r10/skycorr.py)** — correlates anonymized
  sky-observation windows with a catalog of ordinary events; a temporal/
  angular coincidence is **never** an identification
  (`UNIDENTIFIED_CORRELATION_ONLY`), with a time-shuffled null (power on a
  planted true coincidence) and multiplicity correction.

## Prospective evidence and the financial firewall (P18)

**Module:** [`r10/prospective.py`](../../r10/prospective.py)

Retrospective analysis can only fail to find something; confirmation
needs a **prospective** prediction frozen before its outcome. The holdout
registry hashes and freezes predictions (signal, EMI, root, memory, sky,
paper-market), records outcomes only **after** the freeze, and **never
deletes a failed prediction**. Investment cues are private hypotheses
validated only by **blinded paper trading** — `paper_only` is fixed True,
rules are frozen, real-money execution is refused. Every holdout here is
`AWAITING_OUTCOME`; this environment produces none.

---

## What R10.8 does not claim

- No apparatus, no emitted signal, no measured EMI, no opened channel, no
  human stimulation, no crystal driven, no trade placed.
- No external communication source, hidden-species identity, medical
  effect, or financial signal is identified — none has prospective,
  discriminating evidence.
- The 1604/1644 cues carry no location, distance, route index, or
  meaning; `1604 ≈ 925·√3` is approximate and no better than chance.
- The frozen frequencies (13 MHz, 4096, 925, 20.48 Hz) are hypotheses;
  their exact closures are arithmetic, not physics.
- No named person, session text, opening-key word, or CW vector digit
  enters the public tree; the session archive and quarantined claims are
  private, and every quarantined claim is `UNSUPPORTED`.

## Not executed (deferred / blocked)

- **Measured EMI spectra (P10)** and **environmental captures (P12):** no
  spectrum analyzer, field probe, or logger — `BLOCKED_NO_DATA_SOURCE`.
- **Live atomic-time data (P09):** blocked; only the definitional
  standard and estimators are modelled.
- **Apparatus / bench / mechanical source:** none built; hardware
  deferred.
- **Prospective outcomes (P18):** no holdout has resolved; no future
  cue, market window, or sky event exists yet to score against.
- **Real external corpus ingestion (P16):** the comparator is
  implemented; no corpus was ingested here.

`PHYSICAL_VALIDATION_NOT_CLAIMED`.
