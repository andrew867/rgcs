# HG Embedded OS — Application & SDK Contract (ENG)

**Owner:** Agent 08. **Class: ENG (engineering plan).** Nothing here is
built or measured yet; every number is a requirement, not a claim. Safety
envelope DECISION_LOG D7-003 is binding. Timing acceptance requirements:
`docs/COIL_LASER_TIMING_AND_PHASE.md` §9. Architecture context:
`docs/SOFTWARE_HARDWARE_ARCHITECTURE.md` §6–7.

## 1. Platform

ESP32 (CYD-class board: 320×240 touch LCD, SD, RGB LED) on FreeRTOS.
Existing DashCDG/CYD sources are an *input baseline only* — reusable
drivers may be adapted with provenance notes; nothing is inherited as a
requirement.

## 2. Layer contract

```
apps/           rgcs_controller | karaoke | self_test   (one active, build-time)
sdk/            ui | storage | timing | peripherals | logging | lifecycle
bsp/            display, touch, sd, rtc_tcxo, pwm_rmt, triggers, adc
freertos        tasks, queues, timers
```

- **BSP** exposes capabilities, never policy. No app touches a register.
- **SDK.timing** is the ONLY producer of output waveforms. It implements
  the master-clock model of `rgcs_core.timing.master_clock` (single
  reference, per-channel rational dividers; non-integer channels via DDS).
- **SDK.storage**: SD card carries assets and *non-safety* configuration.
  Safety limits (D7-003 values) compile into firmware; a config file can
  tighten but never loosen them.
- **SDK.logging** writes CSV per the v2 `timeseries_channel` contract
  (unit-suffixed columns, sha256 in the run manifest).

## 3. Application manifest

Build-time app selection is driven by a manifest validated against
`embedded/app_manifest.schema.json`: app id/version, required SDK
services, required BSP capabilities, storage quota, and — for any app that
can arm outputs — the declared output classes and their envelope caps
(which must be ≤ D7-003). The build fails if an app requests an output
class the manifest does not cap.

## 4. RGCS controller app (requirements)

1. Reproduce the three frozen macro modes with cycle-exact boundaries
   (G-12 allocations from v2 `drive_sequence`).
2. Complementary coil outputs: commanded phase resolution ≤ 1° @ 4096 Hz;
   complement verified each session (self-test).
3. Isolated (opto/transformer) trigger outputs: laser trigger + ADC sync.
4. Waveform preview on-device mirrors the desktop
   `waveform_preview` output for the same preset (same math).
5. Measurement logging: synchronized ADC (sample clock from the same
   reference), CSV out per §2.
6. Boot calibration & self-test: measure per-channel latency to the
   connector, store as `latency_calibration_s`; refuse to arm on failure
   or on open interlock loop; a null calibration renders the channel
   phase-invalid (H-29 rule) and the UI must show it.
7. Interlocks are hardware: output-enable requires the physical loop;
   overcurrent trip; thermal cutoff; watchdog disarm. Software
   `safe_drive_check` gates arming on top, never instead.

## 5. Karaoke app migration

Migrates the existing CYD karaoke function as a *proof of the SDK*: it
must use only SDK services (UI, storage, lifecycle) and demonstrate that
the app model supports a non-RGCS app without touching timing/trigger
capabilities (its manifest requests none — the build must enforce that).

## 6. Future CPLD/FPGA boundary

The CPLD (complementary pair + dead-time, clocked by the TCXO) sits
BETWEEN SDK.timing and the coil drivers; its register interface is part of
the BSP trigger capability. FPGA is out of scope until a measurement
requirement exceeds what the TCXO/DDS/CPLD chain provides (quantified
table: architecture doc §7).
