# Software and Hardware Architecture (RGCS v3, Agent 08)

**Date:** 2026-07-15. **Classification discipline:** every unbuilt hardware
item below is **ENG (engineering plan)** until built and measured; no
performance number in this document is a claim. Safety envelope D7-003 is
binding throughout. v2 desktop guarantees (workspace, provenance, ethics
gate, bundles) are preserved — nothing here weakens them.

## 1. Layering (implemented)

```
rscs_core        typed coordinates + operators (RSCS-C.*/O.*), registry,
                 embedding/CEP, firewall           [reusable library]
rgcs_core        crystal application: geometry, resonance, anisotropy,
                 optics, timing, drive, experiments, fea_export,
                 crystal_db                        [deterministic core]
rgcs_desktop     PySide6 workbench: 13 v2 panels + v3 services
                 (provenance_graph, waveform_preview — headless,
                 Qt-free, tested)                  [UI]
embedded/        HG Embedded OS contracts (ENG)    [future firmware]
```

RSCS was added as a *separate reusable library* (brief desktop rule 2);
`rgcs_core` composes it (anisotropy → O.17, optics → O.18, timing → O.10)
rather than absorbing it.

## 2. Portability & packaging (implemented this tranche)

- **V2-WIN-01 FIXED** (`services/bundle.py`: POSIX arcnames via
  `as_posix()`); the reproducibility-bundle test now passes on Windows.
  Regression guard: `test_bundle_arcnames_posix`.
- **Specimen-listing defect RE-DIAGNOSED:** the two vertical-slice step-4
  failures attributed in the v2 audit to a listing defect were
  missing-`jsonschema` import failures; with the dependency installed the
  tests pass unmodified on Windows. No listing code change was needed.
  (The audit file stays frozen; correction recorded here and in the
  DEFECT_REGISTER addendum.)
- **Dependencies declared:** `jsonschema`, `referencing` added to the dev
  extra (V2-PKG-01 family; `pyyaml` was declared by Agent 01).
- **Windows CI:** `.github/workflows/ci.yml` — Linux + Windows ×
  Py 3.11/3.13; schema validation and generated-docs freshness are gate
  steps; the single byte-equality golden test (NR3-001) is deselected on
  Windows with its documented justification.

## 3. Desktop panels & visualizations (v3 additions)

| View | Backing service (headless, tested) | Status |
|---|---|---|
| Mathematical provenance graph | `services/provenance_graph.py` — nodes/edges from the three machine registries; every node carries classification; EP rows carry their forbidden-transfer text | data layer implemented; Qt panel = tranche T2 |
| Operator / coordinate inspectors | `rscs_core.registry.load_registry` + `OPERATORS`/`COORDINATE_TYPES` maps | data layer existing; panel T2 |
| Waveform & timing preview | `services/waveform_preview.py` — preset sample arrays + macro envelope lanes (frozen v2 G-12 allocations) | implemented; panel T2 |
| Optical-path & phase-delay view | `waveform_preview.phase_budget_rows` over `timing.phase_at_coordinate` + `optics.ray_to_target` | implemented; panel T2 |
| Experiment builder (RSCS) | v2 builder + `timing_program`/`optical_probe` schemas; **UI must flag `latency_calibration_s: null` channels as phase-invalid** (H-29 rule) | contract fixed; panel T2 |
| Modal overlap / coupling graph | `coupling.overlap_integral` + `couple_modes` | data layer existing; panel T3 |
| Claims/provenance visibility | every panel shows the classification chip of the value it renders (v2 rule, extended to RSCS classes) | binding UI rule |

## 4. Persistence (implemented)

- **Crystal DB** (`rgcs_core/crystal_db.py`): JSON, `schema_version`,
  stepwise forward-migration hooks (missing hook or newer-than-software =
  loud failure), uncertainty-aware records feeding the anisotropic model;
  orientation-unknown records inherit the scalar ±5 % band
  (model-selection rule §7 of the crystal application).
- **HG memory store** (`rscs_core/memory/persistence.py`): append-ordered
  JSON, allocentric-key retrieval; **H-15/H-17/H-19 are now
  machine-tested** (previously "testable-at-persistence-layer").
- **FEA export contract** (`rgcs_core/fea_export.py`): solver-agnostic
  material card (Agent 05 constants, SI) + geometry + orientation with
  sha256 self-checksum; NOT a mesh. CalculiX/Elmer import scripts are
  tranche T3.
- Workspace DB/backup/export-history: v2, unchanged.

## 5. CAD (implemented)

`scad/vogel_parametric_crystal_models_v7_RGCS_v3.scad` fixes **D-02**
(inert compact-mode rings: OpenSCAD block-scope assignment could not
override the customizer variable; v7 uses a derived
`effective_show_compact_mode_rings`). v6 ships verbatim for provenance;
the diff summary is in `scad/README.md` ("CAD provenance"). Ring geometry
remains a visualization of a Hypothesis-class model — rendering asserts
nothing physical.

## 6. HG Embedded OS (ENG — architecture contract)

Full contract: `embedded/HG_EMBEDDED_OS_CONTRACT.md`. Summary:
- **Target:** ESP32 (CYD "Cheap Yellow Display" class board) running
  FreeRTOS. DashCDG/CYD code is an input baseline only, if available.
- **BSP layer:** display, touch, SD card, RTC/TCXO, GPIO/RMT/MCPWM/LEDC,
  isolated trigger outputs, ADC.
- **App model:** build-time app selection via an application manifest
  (schema: `embedded/app_manifest.schema.json`); apps = RGCS controller,
  Karaoke migration, self-test. One app active; SDK services shared.
- **SDK contracts:** UI toolkit, storage (SD assets/config where safe —
  never safety limits, those compile in), deterministic timing service,
  peripherals, logging (CSV compatible with the v2 timeseries contract),
  app lifecycle.
- **Calibration & self-test:** boot self-test measures per-channel latency
  against the reference (writes `latency_calibration_s`), verifies the
  180° complement, and refuses to arm outputs on failure.
- **Interlocks (hardware, not software-only):** output-enable requires the
  physical interlock loop closed; overcurrent trip; thermal cutoff;
  watchdog disarms outputs. Software adds `safe_drive_check` before arm.
- **No high-power instructions:** the controller drives signal-level and
  D7-003-envelope outputs only.

## 7. Timing hardware roadmap (quantified before any exotic hardware)

Requirements first (from Agent 07 §9): jitter ≤ 100 ns rms, phase
resolution ≤ 1° @ 4096 Hz (= 678 ns), complement error ≤ 1°, drift
≤ 2 ppm, update latency ≤ 1 macro period.

| Option | Meets jitter? | Meets phase res.? | Drift | Verdict |
|---|---|---|---|---|
| ESP32 LEDC/MCPWM (80 MHz APB) | yes (12.5 ns tick) | yes (54 ticks/deg) | crystal ±10–40 ppm — **fails** | acceptable ONLY with external reference |
| ESP32 + TCXO reference | yes | yes | ≤ 2 ppm — passes | **baseline choice** |
| External DDS (AD9833-class) on TCXO | yes | yes (0.004 Hz res.) | ≤ 2 ppm | required for non-integer channels (1496/644/587/20/21 Hz — `master_clock` flags them) |
| CPLD for complementary pair + dead time | yes, deterministic | yes | n/a (clocked by TCXO) | **justified**: hardware-guaranteed complement + dead-time insertion is a safety function, not prestige |
| FPGA | yes | yes | n/a | **NOT justified** at these rates; revisit only if a measurement need (e.g. multi-channel ≥ MS/s coherent capture) is demonstrated |

ADC synchronization: sample clock phase-locked to the same TCXO (no
free-running sampling for phase claims); scope/DAQ trigger from the
isolated trigger output.

## 8. Implementation tranches & dependency graph

```
T1 (this commit)  fixes+CI+persistence+FEA+headless services+contracts
T2 (desktop)      Qt panels over the T1 services; experiment builder wiring
T3 (analysis)     FEA import scripts; coupling-graph panel; replay UX
T4 (firmware)     HG OS BSP + timing service + self-test  [needs T1 contracts]
T5 (hardware)     TCXO/DDS/CPLD board + interlocks        [needs T4; ENG until measured]
T6 (integration)  H-29 latency-calibration campaign        [needs T4+T5; unblocks phase claims]

T1 ──> T2 ──> T3
 └───> T4 ──> T5 ──> T6
```

Enterprise doc appends: `SPEC.md`, `TEST_PLAN.md`, `IMPLEMENTATION_PLAN.md`,
`MILESTONE.md`, `RISK_REGISTER.md`, `ACCEPTANCE_CRITERIA.md` each gain a v3
§Agent 08 section referencing this file (single source of truth here).
