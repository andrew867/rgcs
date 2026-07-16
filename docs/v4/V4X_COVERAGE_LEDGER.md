# RGCS V4X master coverage ledger

Total ledger IDs: **248** — covered **248** — uncovered **0**

Gate G42: PASS

| ID | Item | Owner | Artifact | Status |
|---|---|---|---|---|
| A01 | Exciton-cavity photon polariton model | C01 polaritons | `rscs2_core/refmodels/polariton.py::hopfield_2x2,cavity_dispersion_ev,polariton_dispersion` | REDUCED_ORDER_VALIDATED |
| A02 | Hopfield coefficients and Rabi splitting | C01 polaritons | `rscs2_core/refmodels/polariton.py::hopfield_2x2,cavity_dispersion_ev,polariton_dispersion` | REDUCED_ORDER_VALIDATED |
| A03 | Momentum/angle dispersion | C01 polaritons | `rscs2_core/refmodels/polariton.py::hopfield_2x2,cavity_dispersion_ev,polariton_dispersion` | REDUCED_ORDER_VALIDATED |
| A04 | Magnon-polariton third-mode extension | C01 polaritons | `rscs2_core/refmodels/polariton.py::hopfield_3x3,polarization_channel` | REDUCED_ORDER_VALIDATED |
| A05 | Polarization and magnetic-field channels | C01 polaritons | `rscs2_core/refmodels/polariton.py::hopfield_3x3,polarization_channel` | REDUCED_ORDER_VALIDATED |
| A06 | Quantum transduction interface | C01/C13 | `rscs2_core/refmodels/polariton.py::transduction_interface` | INTERFACE_ONLY |
| A07 | Adaptive sub-millimetre Eye refinement | C02 Eye refinement | `rscs2_core/eye_refinement.py::candidate_ladder,refined_verdict + docs/v4/proof/C02/refinement_ladder.json` | INSUFFICIENT_RESOLUTION |
| A08 | More elastic modes, mesh levels, boundaries, material draws | C02 Eye refinement | `rscs2_core/eye_refinement.py::candidate_ladder,refined_verdict + docs/v4/proof/C02/refinement_ladder.json` | INSUFFICIENT_RESOLUTION |
| A09 | Complex driven Eye response, D9/D10 phase diagnostics | C02 Eye refinement | `rscs2_core/fem.py::harmonic_field + eye_refinement.py::driven_phase_diagnostics` | REDUCED_ORDER_VALIDATED |
| A10 | Eye candidate frequency sensitivity versus coordinate | C02 Eye refinement | `rscs2_core/eye_refinement.py::frequency_sensitivity_map` | REDUCED_ORDER_VALIDATED |
| A11 | Harmonic crystal family N=5 through N=12 | C03 harmonic family | `rscs2_core/harmonic_family.py::build_family_member,tolerance_sensitivity,specimen_registry` | CANDIDATE_NEW_COUPLING |
| A12 | Manufacturing tolerances and prospective specimen generator | C03 harmonic family | `rscs2_core/harmonic_family.py::build_family_member,tolerance_sensitivity,specimen_registry` | CANDIDATE_NEW_COUPLING |
| A13 | Frequency-key registry and null-model significance | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry,coincidence_significance` | REDUCED_ORDER_VALIDATED |
| A14 | BVD equivalent circuit extraction | C06 BVD | `rscs2_core/bvd.py::extract_bvd,derived_parameters` | REDUCED_ORDER_VALIDATED |
| A15 | C0, R1, L1, C1, fs, fp, Q, k_eff², spurious modes | C06 BVD | `rscs2_core/bvd.py::extract_bvd,derived_parameters` | REDUCED_ORDER_VALIDATED |
| A16 | Coil, electrode, transducer, fixture, and apparatus models | C07 apparatus | `rscs2_core/apparatus.py::wheeler_inductance_h,crossed_coil_coupling,apparatus_registry,ordinary_artifact_model` | REDUCED_ORDER_VALIDATED |
| A17 | Calibration, uncertainty, inverse design | C08 calibration/inverse design | `rscs2_core/calibration.py (v4.1 module)` | REDUCED_ORDER_VALIDATED |
| A18 | DFT/BSE/ab-initio/QFT/microscopic interfaces only | C13 future interfaces | `rscs2_core/interfaces_future.py::request_computation` | INTERFACE_ONLY |
| C001 | decaying resonance of state change | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C002 | awareness of time as current velocity of state change | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C003 | subjective time as internal update/novelty/arousal/memory dynamics | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C004 | block-universe wavefront versus snapshot | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C005 | observer-frame and 4th-dimension language | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C006 | two or three linked temporal phases | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C007 | Arisaka “space is time” audit | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C008 | MePMoS | T-lane theory registry | `consciousness_lane/theory_registry.py` | ENGINEERING_PROTOTYPE |
| C009 | Neural Holographic Tomography | T-lane theory registry | `consciousness_lane/theory_registry.py` | ENGINEERING_PROTOTYPE |
| C010 | Holographic Ring Attractor Lattice | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C011 | Q-HAL, BFFT, CAIRO, TERESA | T-lane theory registry | `consciousness_lane/theory_registry.py` | ENGINEERING_PROTOTYPE |
| C012 | space-to-time operator S_to_T | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C013 | alpha/theta/gamma phase timing | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C014 | language and creativity as frequency-time navigation | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C015 | microtubules as candidate coherence transformers | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C016 | tau_c * eta_phi * K_cross > theta_neural_bias | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C017 | ordered water and aromatic-electron transition hypotheses | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C018 | Hz/kHz/MHz/GHz/THz resonance claims | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C019 | fractal time-crystal hypothesis | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C020 | 6G/THz instrumentation analogy | T-lane theory registry | `consciousness_lane/theory_registry.py` | ENGINEERING_PROTOTYPE |
| C021 | 100 GHz–10 THz measurement lane | T-lane theory registry | `consciousness_lane/theory_registry.py` | PROTOCOL_READY_HARDWARE_REQUIRED |
| C022 | superheterodyne receiver analogy | T-lane theory registry | `consciousness_lane/theory_registry.py` | ENGINEERING_PROTOTYPE |
| C023 | cross-frequency coupling and downconversion | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C024 | interpersonal synchrony and mentorship | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C025 | firefly and pendulum synchronization analogies | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C026 | gamma 40–160 Hz and consciousness claims | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C027 | dreams versus wake permanence | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C028 | temporal permanence through other observers | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C029 | aura as social/behavioral influence radius | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C030 | external field or receiver hypothesis | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C031 | multiverse and quantum-state influence | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C032 | quantum cognition versus literal quantum brain | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C033 | entanglement and nonclassical-correlation tests | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C034 | manifestation as attention-shaped affordance/path selection | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C035 | path-integral language as metaphor unless formalized | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C036 | active inference and affordances | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C037 | first-person conduit/empty-mind origin report | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C038 | spirit/God/private myth layer | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C039 | mystical language preserved without public scientific endorsement | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C040 | layer map from unknown information state to molecular, neural, cognitive, phenomenological | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C041 | Dream-Wake Constraint Theory | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C042 | Field-Constraint Layer and K_ext quarantine | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C043 | fragments-of-energy source family | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C044 | sixth/seventh-sense separation | T-lane theory registry | `consciousness_lane/theory_registry.py` | SOURCE_HYPOTHESIS |
| C045 | social entrainment, speaker-listener coupling, mentoring | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C046 | flow as subsystem coherence | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C047 | raising consciousness as coordination, not magic | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C048 | “coherence is not truth” control | T-lane theory registry | `consciousness_lane/theory_registry.py` | REDUCED_ORDER_VALIDATED |
| C049 | embodied spatial event memory architecture for Hydrogenuine | T-lane theory registry | `consciousness_lane/theory_registry.py` | ENGINEERING_PROTOTYPE |
| C050 | SWR-like replay and offline consolidation | T-lane theory registry | `consciousness_lane/theory_registry.py` | ENGINEERING_PROTOTYPE |
| C051 | Q-HAL local world-memory block | T-lane theory registry | `consciousness_lane/theory_registry.py` | ENGINEERING_PROTOTYPE |
| C052 | BFFT transform/compression scaffold | T-lane theory registry | `consciousness_lane/theory_registry.py` | ENGINEERING_PROTOTYPE |
| E001 | 4096 Hz non-contact brushing on 3 axes | E-lane E01 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E002 | 4096 Hz non-contact brushing on all 6 sides | E-lane E01 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E003 | contact and non-contact acoustic excitation | E-lane E01 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E004 | tuning forks versus voice-coil/piezo drive | E-lane E01 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E005 | silver electrodes at measured compression node | E-lane E02 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E006 | 20/21 Hz pulse comparison | E-lane E02 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E007 | 1496/587/644 node excitation | E-lane E02 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E008 | crossed copper/silver coils at 90° | E-lane E03 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E009 | 40 turns, 0.33 mm wire modern coil hypothesis | E-lane E03 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E010 | seven-turn coil, one-litre vessel, 70°F historical scaffold | E-lane E03/E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E011 | 3-axis magnetometer | E-lane E03 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E012 | high-impedance electric-field/electrometer channel | E-lane E08 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E013 | capacitance and impedance | E-lane E08 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E014 | microphone and contact microphone | E-lane E08 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E015 | accelerometer | E-lane E08 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E016 | scanning laser vibrometer | E-lane E08 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E017 | current, voltage, field, temperature, humidity, SPL | E-lane E08 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E018 | grounded/ungrounded, glove, no-contact, automated controls | E-lane E09 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E019 | fixed nonmetal jig | E-lane E09 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E020 | dummy coil, resistor, no crystal, rotated crystal, metal bracket controls | E-lane E09 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E021 | cheap quartz before expensive precision crystal | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E022 | repeated days and blind labels | E-lane E09 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E023 | simultaneous acoustic and electrical pickup | E-lane E09 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E024 | phone-app claims tested only as instrument-limited ENG/HYP | E-lane E08 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E025 | collector-reference geometry from CAD source | E-lane E08 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E026 | north/orientation logging | E-lane E09 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| E027 | contact force and mounting-pressure logging | E-lane E09 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F001 | 4096 Hz | E-lane E01 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F002 | 20.480 kHz = 4096×5 | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | CORE_VALIDATED |
| F003 | 32.768 kHz = 4096×8 = 2^15 | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | CORE_VALIDATED |
| F004 | 20 Hz | E-lane E02 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F005 | 19.8 Hz | E-lane E02 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F006 | 21 Hz | E-lane E02 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F007 | 21×195 ≈ 4095 Hz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F008 | 40.00 Hz | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| F009 | 40.96 Hz = 4096/100 | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| F010 | 41.00 Hz | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| F011 | 42.00 Hz | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| F012 | 8 Hz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | ENGINEERING_PROTOTYPE |
| F013 | 20.48 Hz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | CORE_VALIDATED |
| F014 | 5.12 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | CORE_VALIDATED |
| F015 | 10.24 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | CORE_VALIDATED |
| F016 | 5.1515 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F017 | 10.3030 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F018 | 20.000 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | ENGINEERING_PROTOTYPE |
| F019 | 20.6061 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F020 | 18.5–21.2 kHz | E-lane E01 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F021 | 19.8–21.2 kHz | E-lane E01 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F022 | 10.0–12.7 kHz | E-lane E01 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F023 | 24.5–25.5 kHz | E-lane E01 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F024 | 1496 Hz | E-lane E02 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F025 | 587 Hz | E-lane E02 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F026 | 644 Hz | E-lane E02 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| F027 | 465 Hz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F028 | 787 Hz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F029 | 880 Hz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F030 | 465×44 = 20.460 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F031 | 787×26 = 20.462 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F032 | 210.42×98 = 20.62116 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F033 | 4160×5 = 20.800 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | ENGINEERING_PROTOTYPE |
| F034 | 4225×5 = 21.125 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | ENGINEERING_PROTOTYPE |
| F035 | 4225×8 = 33.800 kHz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | ENGINEERING_PROTOTYPE |
| F036 | 10,20,30,50,80,130,210,340,550 Hz | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F037 | 7,9,14,21,42 | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F038 | multiples of 9 | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F039 | 51.843×20 and chains ×128, ×256, ×4096 | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F040 | 60×4096 phase-factor branch | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F041 | 46 ms | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F042 | 60π/4096 s | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F043 | 192-cycle binary timing | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F044 | phi^8 timing | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F045 | 552 ms macrocycle | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F046 | 2260.992 cycles | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | CORE_VALIDATED |
| F047 | 1507.328 cycles | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | CORE_VALIDATED |
| F048 | density ladder 64×8^(n-1) | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F049 | 2.45 GHz powers-of-eight ratio | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F050 | 454 Omega value | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F051 | 7.6 Hz phi-EEG lead | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| F052 | f(n)=f0×phi^n | C04 frequency keys | `rscs2_core/frequency_keys.py::build_registry` | SOURCE_HYPOTHESIS |
| G001 | Rx angle 51.843° | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | SOURCE_HYPOTHESIS |
| G002 | source form 51°51′51″ | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | SOURCE_HYPOTHESIS |
| G003 | decimal conversion near 51.86° | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | SOURCE_HYPOTHESIS |
| G004 | vendor approximation 52° | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | SOURCE_HYPOTHESIS |
| G005 | pyramid comparison near 51.8° | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | SOURCE_HYPOTHESIS |
| G006 | Tx angle 60.000° and 58–60° sensitivity | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | CORE_VALIDATED |
| G007 | six-sided lattice alignment | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | ENGINEERING_PROTOTYPE |
| G008 | 6, 8, 12, and 24 facet families | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | ENGINEERING_PROTOTYPE |
| G009 | facet rotation and square/hexagonal alignment | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | ENGINEERING_PROTOTYPE |
| G010 | phi ellipse, sqrt(phi), sqrt(3), sqrt(5), 60°/72° | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | SOURCE_HYPOTHESIS |
| G011 | C-axis and lateral-axis XRD determination | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | ENGINEERING_PROTOTYPE |
| G012 | vendor 100 nm alignment claim as SRC, not accepted fact | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | SOURCE_HYPOTHESIS |
| G013 | ideal versus nominal 110 mm geometry | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | CORE_VALIDATED |
| G014 | non-metric eye coordinate | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | CORE_VALIDATED |
| G015 | 71 mm 24-sided natural citrine | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G016 | 81 mm 8-sided natural citrine | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G017 | 75 mm 24-sided Himalayan rutilated | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G018 | 63 mm 24-sided Himalayan rutilated | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G019 | 138 mm 24-sided Himalayan rutilated | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G020 | 86 mm 24-sided Himalayan rutilated | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G021 | 62 mm 24-sided Himalayan smoky | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G022 | 125 mm 8-sided Himalayan | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G023 | 157 mm 8-sided flawless Himalayan | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G024 | 125 mm 12-sided flawless Himalayan | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G025 | 34 g, 39 g, 59 g and all catalog mass/dimension records | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | SOURCE_HYPOTHESIS |
| G026 | clear quartz, citrine, amethyst, smoky, rutilated comparisons | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G027 | inclusions, surface damage, polish, density, and seller uncertainty | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | ENGINEERING_PROTOTYPE |
| G028 | prospective N=5..12 specimen family | C03/C05 specimen registry | `rscs2_core/harmonic_family.py::specimen_registry` | ENGINEERING_PROTOTYPE |
| G029 | printed polymer geometry controls | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| G030 | glass acoustic controls | E-lane E04 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| H001 | grip force and contact location | E-lane E06 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H002 | hand capacitance | E-lane E06 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H003 | contact stiffness and damping | E-lane E06 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H004 | equivalent modal load | E-lane E06 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H005 | personalized held-target length correction | E-lane E06 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H006 | grounded versus ungrounded | E-lane E06 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H007 | glove and no-contact | E-lane E06 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H008 | automated no-operator baseline | E-lane E06 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H009 | breathing protocol | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H010 | imagery and expectancy | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H011 | meditation state | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H012 | optional EEG | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H013 | heart rate and physiological logging | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H014 | 40.96 Hz compared with 40/41/42 | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H015 | blinded objective outcomes | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H016 | privacy, consent, ethics, and withdrawal | E-lane E07 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| H017 | ordinary mechanical/capacitive subtraction before residual claims | E-lane E06 | `rscs2_core/protocols_v4x.py::build_protocols` | ETHICS_APPROVAL_REQUIRED |
| I001 | DFT | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| I002 | Bethe-Salpeter | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| I003 | ab-initio spin dynamics | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| I004 | microscopic proton tunnelling | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| I005 | microscopic plasmonics | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| I006 | QFT/QED | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| I007 | nonclassical photon generation | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| I008 | full quantum transduction | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| I009 | quantum-computing simulators | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| I010 | full fluid chemistry | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| I011 | complete microscopic consciousness theory | C13 future interfaces | `rscs2_core/interfaces_future.py::interface_record` | INTERFACE_ONLY |
| S001 | logarithmic contracting spiral r=r0 exp(-aθ) | G01 spiral cone | `rscs2_core/spiral_cone.py` | REDUCED_ORDER_VALIDATED |
| S002 | inverse frequency-wavelength surface | G01 spiral cone | `rscs2_core/spiral_cone.py` | REDUCED_ORDER_VALIDATED |
| S003 | 3D spiral-cone path with vertical exponent p | G01 spiral cone | `rscs2_core/spiral_cone.py` | REDUCED_ORDER_VALIDATED |
| S004 | stable-focus eigenvalues -a±i | G01 spiral cone | `rscs2_core/spiral_cone.py` | REDUCED_ORDER_VALIDATED |
| S005 | curvature invariant 1/sqrt(1+a²) | G01 spiral cone | `rscs2_core/spiral_cone.py` | ENGINEERING_PROTOTYPE |
| S006 | scale ratios phi, 2, e, 8 | G01 spiral cone | `rscs2_core/spiral_cone.py` | REDUCED_ORDER_VALIDATED |
| S007 | one-pointed spinning waveform translation | G01 spiral cone | `rscs2_core/spiral_cone.py` | REDUCED_ORDER_VALIDATED |
| S008 | cusp or centre response | G01 spiral cone | `rscs2_core/spiral_cone.py` | REDUCED_ORDER_VALIDATED |
| S009 | mode overlap Lambda_ab | G01 spiral cone | `rscs2_core/spiral_cone.py` | REDUCED_ORDER_VALIDATED |
| S010 | geometry merit Gamma_s | G01 spiral cone | `rscs2_core/spiral_cone.py` | ENGINEERING_PROTOTYPE |
| S011 | OpenSCAD printable geometry | G01 spiral cone | `rscs2_core/spiral_cone.py` | ENGINEERING_PROTOTYPE |
| S012 | PCB copper cymatic disk | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | REDUCED_ORDER_VALIDATED |
| S013 | dielectric substrate and copper-layer model | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | REDUCED_ORDER_VALIDATED |
| S014 | PCB electromagnetic and structural resonance | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | REDUCED_ORDER_VALIDATED |
| S015 | Chladni/cymatic pattern synthesis | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | REDUCED_ORDER_VALIDATED |
| S016 | plain disk control | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | ENGINEERING_PROTOTYPE |
| S017 | simple cone control | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | ENGINEERING_PROTOTYPE |
| S018 | flat logarithmic spiral control | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | ENGINEERING_PROTOTYPE |
| S019 | Archimedean spiral control | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | ENGINEERING_PROTOTYPE |
| S020 | mass-matched blank | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | ENGINEERING_PROTOTYPE |
| S021 | printed polymer, glass, copper, quartz-like controls | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | ENGINEERING_PROTOTYPE |
| S022 | FFT peak, Q, ring-down, node map, cusp amplitude | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | REDUCED_ORDER_VALIDATED |
| S023 | selected kHz target optimization | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | ENGINEERING_PROTOTYPE |
| S024 | fabrication exports: SCAD, STL, DXF, Gerber, drill, BOM | G02 cymatic disk | `rscs2_core/cymatic_disk.py` | ENGINEERING_PROTOTYPE |
| W001 | matched blind vessels | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W002 | sham exposure | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W003 | temperature control | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W004 | dissolved-gas control | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W005 | pH | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W006 | conductivity | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W007 | UV-visible and IR where available | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W008 | acoustic-pressure logging | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W009 | flow rate and pressure | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W010 | no-crystal control | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W011 | raw quartz control | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W012 | polymer and glass controls | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W013 | reversed orientation | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W014 | one through seven passes | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W015 | seven-turn one-litre 70°F source geometry | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W016 | contamination, mass balance, randomized labels | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
| W017 | no ingestion or therapeutic claims | E-lane E05 | `rscs2_core/protocols_v4x.py::build_protocols` | PROTOCOL_READY_HARDWARE_REQUIRED |
