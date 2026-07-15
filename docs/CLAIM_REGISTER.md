# Claim Register — RGCS v3 / RSCS 1.0

Machine-lintable register of claims. Classes: **EST** (established),
**DER** (derived), **HYP** (hypothesis), **SRC** (source claim, preserved
not endorsed), **ENG** (engineering heuristic — never evidence).
CSV columns follow `internal-docs/plans-v3/templates/CLAIM_REGISTER_TEMPLATE.csv`.

Seed state (Agent 01): the v2 claim base is inherited, not re-litigated —
61 registry equations (classification census in `V2_BASELINE_AUDIT.md`
§5) and 14 pre-registered hypotheses H-01…H-14 (+H-01a/H-06a/H-08b) in
`ROADMAP_TO_FALSIFICATION.md`. New v3 claims are appended below by
Agents 02–08 with full rows; no v2 claim may be upgraded in class without
experimental evidence logged in `NEGATIVE_RESULTS.md`/QA trail.

```csv
claim_id,class,statement,source_or_derivation,observable,controls,failure_condition,uncertainty,status
CLM-3-000,EST,"RGCS v2.0.0 baseline reproduces from frozen archives (232/232 files SHA256-identical; 10/10 release checksums)",docs/V2_BASELINE_AUDIT.md,repo diff vs archives,independent re-extraction,any hash mismatch,exact,verified
CLM-3-001,DER,"4 of 227 v2 tests fail on Windows/Py3.13 due to environment drift and v2 Windows portability defects (V2-WIN-01, V2-PKG-01), not baseline corruption",docs/V2_BASELINE_AUDIT.md §3,pytest results,same suite on Linux/Py3.11/numpy 2.4.4,failures persist in pinned Linux env,n/a,open-until-linux-rerun
```

## Agent 04 — falsifiable HG memory software claims (H-15..H-19)

These are ENG software claims about the Hydrogenuine memory implementation
(RSCS-C.15, RSCS-O.14/15/16), each with a pre-registered failure condition
(`docs/NHT_HAL_RSCS_MAPPING.md` §4). They test the engineering artifact, NOT
the NHT/HAL neuroscience (which stays HYP/SRC and excluded).

```csv
claim_id,class,statement,source_or_derivation,observable,controls,failure_condition,uncertainty,status
H-15,ENG,"HG retrieval quality: a stored record is retrievable by its allocentric key",docs/HG_RSCS_MEMORY_ARCHITECTURE.md,exact-match recall rate over N stores,distinct keys,any distinct-key collision or lost record,n/a,testable-at-persistence-layer
H-16,ENG,"HG transform consistency: replay into any frame preserves allo == frame.ego",tests/property/test_rscs_hg_properties.py,frame_consistent() after replay,random frames,any inconsistency > 1e-6 mm,1e-6 mm,machine-tested-pass
H-17,ENG,"HG temporal continuity: event_time ordering preserved and monotonic under append",docs/HG_RSCS_MEMORY_ARCHITECTURE.md,sortedness of replayed sequence,append order,any reorder/aliasing of timestamps,n/a,testable-at-persistence-layer
H-18,ENG,"HG localization/replay fidelity: replay into original frame reproduces egocentric position; allocentric anchor invariant",tests/property/test_rscs_hg_properties.py,"||ego_replayed-ego||, ||allo_replayed-allo||",random frames/positions,drift > 1e-9 mm,1e-9 mm,machine-tested-pass
H-19,ENG,"HG uncertainty calibration: after update with a sharper observation, reported sigma does not increase without a flag",docs/HG_RSCS_MEMORY_ARCHITECTURE.md,sigma before/after update,sharper observation,silent sigma inflation,n/a,testable-at-persistence-layer
```

## Agent 06 — optical / directional claims (H-20..H-23)

Optical-branch claims with pre-registered failure conditions
(`docs/OPTICAL_AND_NONRECIPROCAL_COUPLING.md` section 4). The binding null
expectation for all directional observables is NO asymmetry (DECISION_LOG
D6-003); H-21/H-23 are pre-registered as expected nulls.

```csv
claim_id,class,statement,source_or_derivation,observable,controls,failure_condition,uncertainty,status
H-20,HYP,"Intensity-modulated probe addressing the measured mode-overlap region shows a photoelastic sideband at the acoustic drive frequency, magnitude within 10x of the DER estimate (delta_n = -1/2 n^3 p S)",rgcs_core.optics.photoelastic_index_shift + OPTICAL_AND_NONRECIPROCAL_COUPLING.md section 3,optical sideband amplitude at f_drive,"heating_matched_power_off_node, glass_isotropic_control, no_drive_baseline",no sideband above noise at predicted magnitude with drive verified on,DER estimate 10x band,pre-registered
H-21,HYP,"Any directional (forward/backward) optical asymmetry reverses sign under beam reversal; expected outcome is NULL (no asymmetry, D6-003)",DECISION_LOG D6-003 + RSCS-O.22/O.23,forward-vs-backward response difference,"beam_reversal, sham_timing, coil_phase_flip, rotated_crystal",asymmetry that fails to reverse under the battery = artifact; absence of asymmetry = expected null,paired-run difference stats,pre-registered-null
H-22,ENG,"The optical control battery separates path-geometry effects from absorption/heating at matched absorbed power",optical_probe.schema.json controls enum,response vs path at matched power,"heating_matched_power_off_node, dummy_crystal",controls cannot separate geometry from heating -> optical branch unusable,n/a,testable-at-bench
H-23,HYP,"Circular-polarization (sigma+ vs sigma-) dependence of any optical response at low power; expected outcome is NULL in transparent unbiased quartz",RSCS-O.22 chi3 spin term (null default),response difference sigma+ vs sigma-,"polarization_flip, no_drive_baseline",dependence absent = expected null; dependence present must survive polarization_flip + sham controls or is artifact,paired-run difference stats,pre-registered-null
```

## Agent 07 — node-menu and timing claims (H-24..H-30)

Pre-registered in `docs/EXPERIMENTAL_PROGRAMME.md` section 4. H-24..H-28
give the five HYP node definitions (crystal application section 3,
definitions 4-8) their observables and failure conditions; the measured
vibration node supersedes (inherited H-07 rule). H-29/H-30 are ENG timing
architecture gates.

```csv
claim_id,class,statement,source_or_derivation,observable,controls,failure_condition,uncertainty,status
H-24,HYP,"An electrical node (impedance minimum) exists along the shaft distinct from the geometric definitions",node menu def 4,impedance vs position,"fixture swap, dummy_crystal",no reproducible minimum distinct from geometry or moves with fixture,position sigma,pre-registered
H-25,HYP,"An optical path/phase feature marks a node location",node menu def 5 + RSCS-O.18,phase map along ray paths,"glass_control, no_drive_baseline",no feature above phase-noise floor at claimed location,phase noise floor,pre-registered
H-26,HYP,"Maximal multimode overlap defines a stable node location",node menu def 6 + RSCS-O.19 overlap,overlap argmax from measured mode shapes,re-measurement,argmax unstable > +/-5 mm across re-measurement,+/-5 mm,pre-registered
H-27,HYP,"Coupling-integral maximum defines a node location",node menu def 7 + RSCS-O.4,fitted g vs probe position,"sensor_reposition",no position-dependence of fitted g above uncertainty,fit sigma,pre-registered
H-28,HYP,"A phase singularity/saddle exists in the spatial phase field",node menu def 8,phase-field critical point (spatial mapping branch),"sensor aperture check (KOS-11)",no critical point or aperture artifact,aperture bound,pre-registered
H-29,ENG,"Latency calibration + phase_at_coordinate predicts measured phase at the interaction coordinate within +/-5 deg at 4096 Hz",rgcs_core.timing.phase_at_coordinate,measured vs predicted phase,"calibrated vs uncalibrated channel",error > 5 deg after calibration -> phase claims blocked,+/-5 deg gate,pre-registered
H-30,ENG,"Sham-timing branch is indistinguishable from combined on every NON-phase observable",EXPERIMENTAL_PROGRAMME section 4,amplitude-only observables sham vs combined,"randomized_blinded order",sham differs on amplitude-only observables -> uncontrolled drive artifact,SAP effect-size rules,pre-registered
```

## Agent 08 status updates (2026-07-15)

H-15, H-17, H-19 (previously `testable-at-persistence-layer`) are now
**machine-tested-pass** via `rscs_core/memory/persistence.py` and
`tests/unit/test_rgcs_platform.py` (keyed retrieval + no distinct-key
collision; append-order/monotonicity enforcement; no silent sigma
inflation). Rows above are append-only and retained unchanged; this note
supersedes their status column.
