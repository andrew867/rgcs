# Orphan idea register (P02)

Ideas found in the source corpus or repository that the fixed 248-item coverage ledger has no row for. The P02 rule is binding: **no orphan may be deleted because it sounds implausible.** It may be translated, quarantined, or rejected on evidence — each of which is recorded here.

Fixed ledger IDs: **248** · orphans found: **20** · total coverage after the sweep: **268**

Dispositions: preserved_contradiction (1), preserved_distinct (1), preserved_null (1), quarantined_private (2), quarantined_source (1), quarantined_translation (4), rejected (2), translated_to_model (1), translated_to_null (1), translated_to_protocol (6)

| ID | Idea | Source | Status | Disposition |
|---|---|---|---|---|
| ORPHAN-001 | Phryll (source term for a universal medium/field) | source lore transcripts | SOURCE_HYPOTHESIS | quarantined_translation |
| ORPHAN-002 | 'Collector' apparatus fragment | source lore / apparatus notes | SOURCE_HYPOTHESIS | translated_to_protocol |
| ORPHAN-003 | 'Density bridge' between materials | source lore | SOURCE_HYPOTHESIS | quarantined_translation |
| ORPHAN-004 | 'Phase conjugation' as a resonance mechanism | source lore + optics notes | MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL | quarantined_translation |
| ORPHAN-005 | 'Retuning' of a crystal by exposure | source lore / comms log | SOURCE_HYPOTHESIS | translated_to_protocol |
| ORPHAN-006 | 'Portal' / 'time breakage' motifs | source lore transcripts | SOURCE_HYPOTHESIS | quarantined_private |
| ORPHAN-007 | Atlantis / CERN / Star Nation source motifs | source lore transcripts | SOURCE_HYPOTHESIS | quarantined_private |
| ORPHAN-008 | 'Vortex' as a field geometry claim | source lore + spiral notes | SOURCE_HYPOTHESIS | translated_to_model |
| ORPHAN-009 | 'Singularity' at the cone cusp | spiral-cone source notes | REJECTED_BY_EVIDENCE | rejected |
| ORPHAN-010 | 454 ohm non-frequency value | master workbook | NOT_APPLICABLE | rejected |
| ORPHAN-011 | 51.843 deg vs 51 deg 51' 51" (=51.8642 deg) | Vogel master reference + workbooks | SOURCE_HYPOTHESIS | preserved_distinct |
| ORPHAN-012 | 2.45 GHz ratio (microwave-oven coincidence) | workbook | SOURCE_HYPOTHESIS | translated_to_null |
| ORPHAN-013 | 7.6 Hz phi-EEG lead | workbook / consciousness notes | SOURCE_HYPOTHESIS | translated_to_protocol |
| ORPHAN-014 | Vendor '100 nm' flatness/precision claim | seller listings | SOURCE_HYPOTHESIS | quarantined_source |
| ORPHAN-015 | Seven-turn one-litre 70 F historical coil | historical/engineering notes | PROTOCOL_READY_HARDWARE_REQUIRED | translated_to_protocol |
| ORPHAN-016 | Recorded source nulls and ambiguous experiments | communications-log audit | EXPERIMENTALLY_NULL | preserved_null |
| ORPHAN-017 | Contradiction: catalog vs measured specimen lengths | workbooks vs seller listings | INCONCLUSIVE | preserved_contradiction |
| ORPHAN-018 | 'Brushing' as an excitation technique | source lore | PROTOCOL_READY_HARDWARE_REQUIRED | translated_to_protocol |
| ORPHAN-019 | 'Sound key' sequences | workbooks / lore | SOURCE_HYPOTHESIS | translated_to_protocol |
| ORPHAN-020 | 465/787/880 Hz body-mapped source labels | workbook | SOURCE_HYPOTHESIS | quarantined_translation |

## Dispositions in full

### ORPHAN-001 — Phryll (source term for a universal medium/field)

- Source: source lore transcripts
- Status: `SOURCE_HYPOTHESIS` (SRC)
- Disposition: **quarantined_translation**
- Documented in: `docs/v4/ORPHAN_IDEA_REGISTER.md`

No physical quantity is defined. Retained verbatim as source vocabulary in the lore lane; NOT imported into any solver. Falsifiable only once a source supplies an operational definition with units; none does.

### ORPHAN-002 — 'Collector' apparatus fragment

- Source: source lore / apparatus notes
- Status: `SOURCE_HYPOTHESIS` (SRC)
- Disposition: **translated_to_protocol**
- Documented in: `docs/v4/APPARATUS_DIGITAL_TWIN.md`

Translated to the ordinary-channel apparatus model: any 'collector' is an antenna/electrode with a measurable capacitance and impedance (apparatus.electrode_capacitance_f). Falsified as an exotic device if its response is bounded by the ordinary artifact budget (G14).

### ORPHAN-003 — 'Density bridge' between materials

- Source: source lore
- Status: `SOURCE_HYPOTHESIS` (SRC)
- Disposition: **quarantined_translation**
- Documented in: `docs/v4/ORPHAN_IDEA_REGISTER.md`

Read literally it is a claim about acoustic impedance matching (Z = rho c), which IS implemented and testable; read as a novel coupling it has no operational definition. Both readings are recorded; only the impedance reading is computable.

### ORPHAN-004 — 'Phase conjugation' as a resonance mechanism

- Source: source lore + optics notes
- Status: `MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL` (SRC)
- Disposition: **quarantined_translation**
- Documented in: `docs/v4/V4_OPTICAL_CHANNEL_TAXONOMY.md`

Optical phase conjugation is established physics in nonlinear media; alpha quartz has no registered capability for the required chi(3) four-wave-mixing channel at the declared drive levels. MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL, which is NOT a claim that it cannot exist.

### ORPHAN-005 — 'Retuning' of a crystal by exposure

- Source: source lore / comms log
- Status: `SOURCE_HYPOTHESIS` (HYP)
- Disposition: **translated_to_protocol**
- Documented in: `docs/v4/experiments/MATERIAL_COMPARISON.md`

Operationalized as a persistent change in modal frequency or Q after an exposure, measured against a sham-exposed matched control. Falsified if the pre/post shift does not exceed the day-to-day drift of the control (E04/E09).

### ORPHAN-006 — 'Portal' / 'time breakage' motifs

- Source: source lore transcripts
- Status: `SOURCE_HYPOTHESIS` (SRC)
- Disposition: **quarantined_private**
- Documented in: `docs/v4/consciousness/PHENOMENOLOGY_AND_PRIVATE_MYTH_POLICY.md`

Preserved verbatim in the private myth layer (C038/C039). Not a public scientific claim, neither endorsed nor mocked, and excluded from public assets by the source filter.

### ORPHAN-007 — Atlantis / CERN / Star Nation source motifs

- Source: source lore transcripts
- Status: `SOURCE_HYPOTHESIS` (SRC)
- Disposition: **quarantined_private**
- Documented in: `docs/v4/consciousness/PHENOMENOLOGY_AND_PRIVATE_MYTH_POLICY.md`

Same disposition as ORPHAN-006: private myth layer, retained without endorsement, no observable proposed by the source.

### ORPHAN-008 — 'Vortex' as a field geometry claim

- Source: source lore + spiral notes
- Status: `SOURCE_HYPOTHESIS` (HYP)
- Disposition: **translated_to_model**
- Documented in: `docs/v4/SPIRAL_CONE_MODEL.md`

Translated to the log-spiral / stable-focus mathematics that IS implemented (spiral_cone.focus_eigenvalues, eigenvalues -a +/- i). A converging spiral trajectory is a real solution of a declared ODE; it is not evidence of a physical vortex field.

### ORPHAN-009 — 'Singularity' at the cone cusp

- Source: spiral-cone source notes
- Status: `REJECTED_BY_EVIDENCE` (DER)
- Disposition: **rejected**
- Documented in: `docs/v4/SPIRAL_CONE_MODEL.md`

REJECTED as stated: the cusp energy-concentration metric is ~1.44x, not divergent. A geometric point of high curvature is not a physical singularity, and the FEA shows a finite, bounded response. The G01 prompt forbids claiming a singularity; the measurement agrees.

### ORPHAN-010 — 454 ohm non-frequency value

- Source: master workbook
- Status: `NOT_APPLICABLE` (SRC)
- Disposition: **rejected**
- Documented in: `docs/v4/NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md`

A resistance in ohms is not a frequency in hertz. Registered as a non-frequency value so it can never enter the harmonic graph; the frequency schema's `non_frequency_value` kind exists for exactly this (C04).

### ORPHAN-011 — 51.843 deg vs 51 deg 51' 51" (=51.8642 deg)

- Source: Vogel master reference + workbooks
- Status: `SOURCE_HYPOTHESIS` (SRC)
- Disposition: **preserved_distinct**
- Documented in: `docs/v4/FAMILY_N5_N12.md`

Two DISTINCT angle conventions differing by 0.0212 deg. The P02 rule forbids silently merging distinct values; both are kept as separate registry entries (G001-G006) and neither is rounded into the other.

### ORPHAN-012 — 2.45 GHz ratio (microwave-oven coincidence)

- Source: workbook
- Status: `SOURCE_HYPOTHESIS` (HYP)
- Disposition: **translated_to_null**
- Documented in: `docs/v4/NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md`

Registered as an arithmetic ratio motif with a look-elsewhere null. 2.45 GHz is an ISM band chosen by regulation, not a water resonance; the common 'water resonance' claim is false and is recorded as such.

### ORPHAN-013 — 7.6 Hz phi-EEG lead

- Source: workbook / consciousness notes
- Status: `SOURCE_HYPOTHESIS` (HYP)
- Disposition: **translated_to_protocol**
- Documented in: `docs/v4/consciousness/SYNCHRONY_AND_MENTORSHIP.md`

A frequency in the theta/alpha boundary. Retained as a frequency key with neighbour controls; any claimed match must survive the look-elsewhere correction. No EEG data exists in this programme.

### ORPHAN-014 — Vendor '100 nm' flatness/precision claim

- Source: seller listings
- Status: `SOURCE_HYPOTHESIS` (SRC)
- Disposition: **quarantined_source**
- Documented in: `docs/v4/METROLOGY_PROTOCOL.md`

A seller claim, retained at SRC in the specimen record's `seller_values` block. It cannot become a measured value without independent metrology; metrology.specimen_record enforces the separation in code.

### ORPHAN-015 — Seven-turn one-litre 70 F historical coil

- Source: historical/engineering notes
- Status: `PROTOCOL_READY_HARDWARE_REQUIRED` (ENG)
- Disposition: **translated_to_protocol**
- Documented in: `docs/v4/experiments/COIL_FIELD_CAMPAIGN.md`

Fully specified as an apparatus record and modelled by the ordinary-channel coil twin (turns, resistance, inductance, field, heating). Requires hardware to execute (E03/E05).

### ORPHAN-016 — Recorded source nulls and ambiguous experiments

- Source: communications-log audit
- Status: `EXPERIMENTALLY_NULL` (NULL)
- Disposition: **preserved_null**
- Documented in: `docs/v4/ORPHAN_IDEA_REGISTER.md`

The source corpus records attempts that produced nothing. Under gate G48 a null is preserved, not deleted: a null result is not a failed project, and erasing it would bias the record toward positive claims.

### ORPHAN-017 — Contradiction: catalog vs measured specimen lengths

- Source: workbooks vs seller listings
- Status: `INCONCLUSIVE` (SRC)
- Disposition: **preserved_contradiction**
- Documented in: `docs/v4/METROLOGY_PROTOCOL.md`

The corpus contains disagreeing lengths for nominally identical specimens. Unresolvable without metrology; both values are retained in `seller_values` and the disagreement is reported by metrology.seller_vs_measured_delta rather than averaged away.

### ORPHAN-018 — 'Brushing' as an excitation technique

- Source: source lore
- Status: `PROTOCOL_READY_HARDWARE_REQUIRED` (SRC)
- Disposition: **translated_to_protocol**
- Documented in: `docs/v4/experiments/ACOUSTIC_CAMPAIGN.md`

Operationalized in E01 as non-contact acoustic excitation swept across 3 axes and 6 facets with calibrated SPL and randomized order. The source term names a procedure, not a mechanism.

### ORPHAN-019 — 'Sound key' sequences

- Source: workbooks / lore
- Status: `SOURCE_HYPOTHESIS` (SRC)
- Disposition: **translated_to_protocol**
- Documented in: `docs/v4/TIMING_FAMILY_AUDIT.md`

Translated to declared frequency sequences (F-registry) dispatched by the E01 protocol with neighbour controls. A sequence that 'works' must beat its own neighbours, or it is a look-elsewhere artifact.

### ORPHAN-020 — 465/787/880 Hz body-mapped source labels

- Source: workbook
- Status: `SOURCE_HYPOTHESIS` (SRC)
- Disposition: **quarantined_translation**
- Documented in: `docs/v4/NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md`

Retained as SOURCE LABELS only. The C04 prompt forbids treating chakra/body mappings as medical facts; they carry no medical claim, and this programme makes none.

## Local corpus extraction

Files scanned: 124; distinct number+unit tokens: 100.

Only derived counts are published; the corpus is LOCAL_ANALYSIS_ONLY and no source text is reproduced here.

