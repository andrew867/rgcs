# Broadcast oscillator heritage and technical continuity (Agent H01)

The technically legitimate continuity between broadcast engineering
and this resonator programme — extracted as engineering lessons, with
no claim that heritage validates any hypothesis.

## What genuinely transfers from broadcast practice

| Broadcast discipline | Resonator-platform counterpart |
|---|---|
| Frequency standards & crystal ovens | the acceptance band + TCF compensation (`oscillator.tcf_compensation`); a frequency without a temperature is not a specification |
| Phase locking & synchronization | the Barkhausen loop discipline (`oscillator.barkhausen`); the phase condition is as binding as the gain condition |
| Impedance matching | OSL calibration (`bvd.osl_correct`); an unmatched fixture measures itself |
| Transmission-line thinking | cable loading (`apparatus.cable_loading`); the cable is part of the circuit |
| Spectral purity / phase noise | Leeson model (`oscillator.leeson_phase_noise`); loaded Q is the whole game near the carrier |
| Fault diagnosis by substitution | the control sets everywhere: dummy coil, no-crystal, sham trim — broadcast's "swap the suspect stage" as experimental design |
| Logging discipline | the append-only ledger; transmitter logs were legally append-only for good reason |
| Proof of performance | the resonator certificate: measured numbers, dated, signed, instrument-traceable |

## The aging lesson

Broadcast crystals were burned in before their frequency was trusted
(`oscillator.aging_model`, logarithmic early drift). A certificate
issued before burn-in overstates stability — a rule this platform
inherits directly.

## What does NOT transfer

Heritage is not evidence. That broadcast engineering used quartz
resonators magnificently says nothing about any unconventional quartz
hypothesis; the continuity is in the **discipline** (calibration,
logging, controls, substitution testing), not in the claims. No
"golden age" argument appears anywhere in this programme's evidence
chain.

Status: documentation of practice; `SOURCE_HYPOTHESIS` where any
historical claim is repeated, `ENGINEERING_PROTOTYPE` for every
transferred practice implemented in code (each named above).
