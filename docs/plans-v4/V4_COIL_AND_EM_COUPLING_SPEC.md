# V4 Coil & EM Coupling Spec (RSCS2-E.10/E.11)

**Status:** PLANNING. Magnetoquasistatic; full-wave EM is an
**integration contract**, not a rebuilt solver. **Safety:** the frozen
D7-003 envelope (≤30 V, ≤3 A, ≤5 mJ/pulse, dummy-load-first, no human
exposure) binds every coil-run description; no high-power hardware
instructions.

## 1. Coil geometry & quasi-static field (RSCS2-E.10, EST)

- Import coil geometry (the opposed A/B pair from v3 `rgcs_core.timing`
  parameters) with `coil` mesh tags.
- Magnetoquasistatic field from a **measured current waveform input**
  (Biot–Savart for the field of a prescribed current distribution; the
  standard low-frequency approximation, valid ≪ self-resonance which the
  frozen coil model already checks). Electric-field/capacitive coupling
  and mutual inductance from the frozen `coil_impedance`,
  `mutual_inductance_h`, `self_resonance_hz` models (reused, EST).

## 2. Drive projection (RSCS2-E.11, EST)

The magnetic/electric field → a body-force or equivalent modal-drive
term b, projected onto elastic/piezo modes: f_n = ∫ φ_n·b dV. Phase and
propagation delays to the interaction coordinate come from the frozen
timing phase budget (`phase_at_coordinate`, six delay terms). This is
projection onto modes, not a full electromechanical field solve.

## 3. Leakage / artifact controls

EM leakage (direct sensor pickup, ground loops) is modelled as an
explicit **artifact channel** (extends the Agent-14 control set): a
"coil-only, no-specimen" projection gives the leakage baseline that any
claimed coil→mode coupling must exceed. No coupling is reported without
its leakage control.

## 4. Integration contracts (external solvers)

Documented field-exchange contracts for **openEMS / Elmer / GetDP /
FEMM** (units, mesh/field interchange, coordinate frame). v4 supplies
the geometry+material and consumes a returned field; it does not embed
any of these solvers. Licences documented; all are external tools.

## 5. Reciprocity / exclusions

No nonreciprocity is imported as an intrinsic quartz property (D6-003);
circulation in a plotted field is not a physical vortex (exclusion). Coil
performance numbers from any reference stay with their source (frozen
forbidden-transfer clauses).

## 6. Tests

Biot–Savart field vs closed form (single loop, solenoid on-axis);
mutual-inductance/self-resonance reuse vs frozen `rgcs_core.timing`;
drive-projection energy conservation; leakage-baseline control present;
phase-budget consistency vs frozen timing; safety-envelope lint on run
descriptions.
