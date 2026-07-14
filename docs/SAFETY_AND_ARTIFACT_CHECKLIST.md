# RGCS v2 — Safety and Artifact Checklist

**Author:** Sub-Agent 06 (Experiments, Controls, and Data Schemas)
**Date:** 2026-07-14
**Version:** 1.0.0
**Scope:** binding on every bench session. The session lead initials each applicable section in the session log; the run manifest's `artifact_register_ref` points at the campaign's living artifact list. Stop conditions are hard: when one triggers, power down, log, and do not resume until the cause is dispositioned.

---

## 1. Electrical safety

**Limits (absolute, all branches):**

- Bench ceiling **60 V DC / 3 A peak** (the top of the source-stated coil range; nothing in any protocol requires more). The corpus 100 V/300 ns "plant test" point is NOT replicated at that voltage.
- All supplies current-limited; fused outputs; RCD/GFCI-protected mains.
- **SELV rule for human presence:** during human-loading sessions only SELV equipment (< 25 V AC / 60 V DC, current-limited) may be present on the bench, and every drive output is hardware-interlocked off (`no_energized_contact_confirmed`).
- No human contact with energized coils or electrodes, ever; > 24 V runs require an enclosure.

**Staged power ramp (coil/electrode branches; adapted from WB3 Safety Checklist):**

| Stage | Level | Exit criteria |
|---|---|---|
| 0 | 3.3/5 V logic into dummy input | clean gates, no overlap/shoot-through on scope |
| 1 | 5 V, 25–100 mA current-limited | no heating, no ringing |
| 2 | 12 V, 100–250 mA | repeatable, cool, dummy controls clean |
| 3 | 24 V, ≤ 500 mA, enclosed | no spikes/singing/cracking/arcing |
| 4 | full protocol point (≤ 60 V/3 A), enclosed | all lower stages documented |

**Checklist:** □ snubber/flyback/TVS fitted on switching stages □ gate dead-time verified on scope □ no UI-loop safety (hardware enable + fault pin) □ cable strain relief and no exposed conductors □ silver/copper electrode edges deburred.

**Stop conditions:** any spike exceeding device rating; arcing; shoot-through; supply current limit reached unexpectedly; > 5–10 °C rise on coil/crystal/fixture; smell/discoloration.

## 2. Acoustic safety

- ≤ **85 dB(A)** continuous at any operator position; 85–94 dB(A) only with hearing protection and signage; hard ceiling **100 dB(A)** at the specimen, never with a person < 1 m.
- Ultrasonic content (> 16 kHz sweeps): keep < 94 dB SPL at operator positions; prefer enclosure.
- Water-branch hydrophone checks in-vessel levels; ultrasonic-cleaner comparator runs follow the cleaner's own rating.
- **Stop conditions:** operator discomfort/tinnitus report; SPL meter reading above the applicable limit.

## 3. Mechanical / specimen protection

- Never clamp crystal tips; support in padded V-blocks or the torque-controlled jig; tap energy < 10 mJ.
- Inspect (photograph, hash) before and after each session; **stop** on any click, crack, chip, or visible inclusion heating (WB3 ringing-control table).
- Growing amplitude or audible "singing" is a **reduce-and-reassess** condition: lower voltage/current/duty, move contact, shorten run, add damping — and record it; it is data, not a target to chase past safe limits.
- Spiral/control metal parts: deburred edges, gloves for handling.

## 4. Human-subject boundary (human-loading branch)

- **Non-clinical.** A volunteer holds an undriven crystal. No physiological measurement, no health/therapeutic/wellness claim or framing in any artifact, log, or UI (policy §2 vocabulary gate).
- **Ethics review is required before any participant contact** — institutional IRB-equivalent or documented exemption; `human_loading.ethics_review_ref` is a schema-enforced gate; consent records stay outside the data repository; withdrawal honored with deletion.
- Pseudonymous participant codes only; no personal data in manifests, filenames, or notes.
- No energized drive of any kind during contact (hardware interlock; §1 SELV rule).

## 5. Chemical / water branch

- Eye protection with saturated salt/silica solutions; spill kit at bench; liquids physically separated from mains-powered equipment; RCD/GFCI outlets.
- No ingestion-related language or testing; vessels labeled "not potable".

## 6. Artifact checklist (per campaign; each item gets a register entry with status)

**Electrical/EMI**
- □ Direct drive pickup: dummy-electrode / no-crystal / dummy-load subtractions acquired at identical settings (JH-033 is the cautionary precedent — "minute signals" traced to pickup).
- □ Switching transients characterized (spectrum of the dummy-load run) and listed with frequencies.
- □ Ground loops audited (single-point ground; lift test documented).
- □ Cable-borne magnetic coupling: rotated-coil + cable-dress variation test.
- □ Charge-amp microphonics and saturation/blanking behavior during pulses documented.
- □ Mains hum ladder (50/60 Hz + harmonics) in the artifact register.

**Acoustic/mechanical**
- □ Fixture/mount resonances mapped (fixture-only runs) and overlaid on every spectrum.
- □ Acoustic leakage path: speaker-only (no specimen) floor acquired.
- □ Room standing waves: 50 mm specimen-position shift; surviving effects only.
- □ Sensor mass loading: light-sensor repeat at one station; shift < peak uncertainty.
- □ Speaker harmonic distortion measured; overlap with crystal modes flagged.

**Measurement chain**
- □ I/Q artifacts (LO leakage, images, constant bands) identified and listed with frequencies (KOS-14 discipline); two independent measurement paths for any headline result.
- □ Aliasing: fs ≥ 4× highest analysis frequency or AA filter documented.
- □ Inter-channel skew < 1 sample (spatial mapping); common-injection σ_φ² ≈ 0 check passed.
- □ Sensor aperture vs shortest mode wavelength documented (spatial low-pass, KOS-11).
- □ Instrument phase-drift budget measured this session (KOS-13) and recorded in the environment record.
- □ Coherence baseline b_w measured for every window length in use; window-sensitivity scan done.

**Thermal/environmental**
- □ Temperature logged start/end (+ specimen where heated); drift limits per branch respected.
- □ Hand-warmth control (human loading): glove/surrogate comparison acquired.
- □ Water branch: evaporation, cavitation/degassing (ultrasound comparator), vessel-lot variance, meter drift (mid-batch recalibration).

**Analysis-side**
- □ Scrambled-label nulls run for spectrum/parity claims (RGCS-M.60 item 4).
- □ Detection-limit injection (G-C) current for this campaign — prerequisite for any null claim.
- □ Forbidden-vocabulary scan on outputs ("quantum shear", BEC/condensate/dark-sector terms) — Agent 08 gate.

## 7. Session log minimum

Date/time, session lead, participants present, branch + protocol version, power stage reached, stop conditions triggered (or "none"), artifact register updates, specimen condition photos (hashed), and the seeded randomization draw for the session.
