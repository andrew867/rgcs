# SYNTHETIC demo report (A23)

**SYNTHETIC DEMO REPORT — every number in this file was produced by simulation; no hardware and no crystal exist**

## 1 exact relation census (SYNTHETIC)

- **ranked**: [{"inputs": [["5", "4096"]], "output_hz": "20480", "target_hz": "20480", "class": "HARMONIC", "order": 5, "exact": true}, {"inputs": [["500", "1024/25"]], "output_hz": "20480", "target_hz": "20480", "class": "PHASE_CLOSURE_ONLY", "order": 500, "exact": true}, {"inputs": [["1000", "512/25"]], "output_hz": "20480", "target_hz": "20480", "class": "PHASE_CLOSURE_ONLY", "order": 1000, "exact": true}, {
- **explanation**: {"4096*5": {"class": "HARMONIC", "why": "order 5 is a LOW-ORDER PRACTICAL harmonic: a square/pulse drive at 4096 Hz physically carries a fifth-harmonic line at 1/5 Fourier amplitude"}, "8*2560 | 20.48*1000 | 40.96*500": {"classes": ["PHASE_CLOSURE_ONLY", "PHASE_CLOSURE_ONLY", "PHASE_CLOSURE_ONLY"], "why": "exact arithmetic but orders 2560/1000/500 are far beyond any waveform's usable harmonic cont

## 2 waveform distinction (SYNTHETIC)

- **sine_4096**: [{"f_hz": 4099.906160595079, "amplitude": 5222.14704590544}, {"f_hz": 4299.901583063132, "amplitude": 6.346580376592556}, {"f_hz": 3849.9118825100136, "amplitude": 3.558156532536377}, {"f_hz": 3649.916460041961, "amplitude": 0.5812970605902726}]
- **square_4096**: [{"f_hz": 4099.906160595079, "amplitude": 6649.211114712732}, {"f_hz": 12299.718481785238, "amplitude": 2147.8668795088024}, {"f_hz": 20499.530802975398, "amplitude": 1209.517166901755}, {"f_hz": 28649.344268548542, "amplitude": 834.8837404167258}]
- **sine_20480**: [{"f_hz": 20499.530802975398, "amplitude": 4746.7830619905735}, {"f_hz": 20299.535380507343, "amplitude": 36.20669874955168}, {"f_hz": 20749.525081060463, "amplitude": 10.386733381830284}, {"f_hz": 20049.541102422278, "amplitude": 2.4974529448577756}]
- **key_comparison**: {"sine_fifth": 0.0, "square_fifth_over_fundamental": 0.19999999999999998, "statement": "an ideal 4096 Hz sine contains NO 20480 Hz component; an ideal 50% square carries an odd fifth harmonic at exactly 1/5 of its fundamental Fourier amplitude \u2014 before any hardware or plant filtering"}

## 3 nominal specimen sweep (SYNTHETIC)

- **sweep_id**: "SYNTHETIC-SWEEP-0000"
- **fit**: {"fitted": true, "f0_hz": 20275.44, "fwhm_hz": 46.31999999999971, "q": 437.725388601039, "u_f0_hz": 0.05999999999949068, "grid_hz": 0.11999999999898137}
- **q_ci95**: [434.3811500560255, 500.1362563335155]
- **note**: "pre-arrival plant model; the peak is the MODEL's, not a crystal's"

## 4 optimizer Pareto + compiled recipes (SYNTHETIC)

- **pareto_families**: ["resonance_locked_sine", "direct_sine_target", "direct_square_target", "off_resonance_control", "clock_square_4096", "am_envelope_20_48", "sham_output_off", "highorder_mix"]
- **gate_check**: {"rule": "high-order arithmetic cannot outrank low-order physical generation", "holds": true}
- **compiled**: [{"family": "resonance_locked_sine", "recipe_id": "SYNTHETIC-resonance_locked_sine", "valid": true, "hash": "698d4d3de6008130"}, {"family": "direct_sine_target", "recipe_id": "SYNTHETIC-direct_sine_target", "valid": true, "hash": "6b721b5dc27a50dd"}, {"family": "direct_square_target", "recipe_id": "SYNTHETIC-direct_square_target", "valid": true, "hash": "d945d93b50daf57f"}, {"family": "off_resonan

## 5 device simulator end-to-end (SYNTHETIC)

- **uploaded**: true
- **ran**: true
- **segments**: [{"segment": "clock_square_4096", "requested_hz": "4096", "calculated_realized_hz": "4096", "measured_realized_hz": null, "synthetic": true}]
- **log_chain_intact**: true
- **all_events_synthetic**: true

## 6 fault refusal (SYNTHETIC)

- **all_failed_off**: true
- **overtemp**: {"state": "FAULT_LATCHED", "output_on": false}
- **arm_expiry**: {"started": false, "state": "FAULT_LATCHED"}
- **pin_conflict**: {"loaded": false, "state": "FAULT_LATCHED"}

