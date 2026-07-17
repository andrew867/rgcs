"""RGCS Frequency-Key Harmonic Excitation and ESP32-CYD Instrument
(v4.4 pack; agents A00-A26).

    Lore proposes. Mathematics translates. Software attacks.
    Evidence decides. Provenance remembers.

Binding rules carried by every module here:

- Exact frequency arithmetic uses `fractions.Fraction` (or Decimal at
  the parse boundary), NEVER binary-float equality (A04).
- Every relation has exactly one primary mechanism class; the class
  controls language and scoring (orchestrator taxonomy).
- Arithmetic closeness is not power: a high-order exact match cannot
  outrank a low-order physically generated component (A10 gate).
- Seller dimensions are SOURCE_CLAIM, never measurements (A01/A07).
- Requested, calculated-realized, and measured-realized frequency are
  three separate fields (A16; PHASE_AND_TIMING_NOTES).
- Synthetic data carries SYNTHETIC markers in ids, filenames,
  manifests, and UI text (A21).
- The physical output is fail-off: no auto-arm, faults latch, every
  abnormal path lands in output-off (A19).
- No physical effect is claimed anywhere: SOFTWARE lanes may be green
  while every physical hypothesis remains UNTESTED (A25).
"""

MECHANISM_CLASSES = (
    "HARMONIC",
    "SUBHARMONIC_CLOCK",
    "AMPLITUDE_MODULATION_SIDEBAND",
    "FREQUENCY_MODULATION_SIDEBAND",
    "INTERMODULATION",
    "PHASE_CLOSURE_ONLY",
    "ARITHMETIC_COINCIDENCE",
    "MEASURED_RESONANCE_MATCH",
    "UNKNOWN",
)

EVIDENCE_CLASSES = (
    "LORE",
    "DERIVED_ARITHMETIC",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "SYNTHETIC_INSTRUMENT_RUN",
    "BENCH_MEASUREMENT_PLAN",
    "SOURCE_CLAIM",
    "SOURCE_CLAIM_PLUS_ANALYTIC_MODEL",
)
