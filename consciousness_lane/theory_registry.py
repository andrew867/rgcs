"""T01-T10 theory registry: C001-C052 with layer, status, evidence
tag, and falsification condition. Every entry states which of the
eight CONSCIOUSNESS_LAYERS it lives on so that a metaphor is never
read as established evidence (G34/G38/G40).

STATUS RULE (v4.2.1 completeness audit). An entry may carry
`REDUCED_ORDER_VALIDATED` only when a mathematical model exists in
`consciousness_lane.reduced_models`, its equations and parameters are
declared, at least one meaningful limit or comparator is tested, and a
falsification condition is stated. The v4.2.0 registry marked 18
entries REDUCED_ORDER_VALIDATED while only 6 had models; this audit
implemented models for 5 more and DOWNGRADED the other 7 to
`SOURCE_HYPOTHESIS`. `model_symbol` names the implementing function and
is verified by `test_reduced_order_claims_have_models` and by ledger
gate G42F — an entry cannot claim validation without code that runs."""

from __future__ import annotations

from rscs2_core.research_records import make_record

# (id, title, layer, status, tag, falsification condition, model)
_E = [
 ("C001", "decaying resonance of state change", "mathematical_model",
  "REDUCED_ORDER_VALIDATED", "DER",
  "no damped-oscillator fit to any operationalized state-change "
  "series outperforms an AR(1) null", "state_change_response"),
 ("C002", "awareness of time as current velocity of state change",
  "mathematical_model", "REDUCED_ORDER_VALIDATED", "DER",
  "reported time-rate is uncorrelated with |d(state)/dt| proxies "
  "across participants", "state_change_response"),
 ("C003", "subjective time from update/novelty/arousal/memory",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "DER",
  "duration judgements are unaffected by novelty and arousal "
  "manipulations under preregistered analysis", "subjective_time"),
 ("C004", "block-universe wavefront versus snapshot", "metaphor",
  "SOURCE_HYPOTHESIS", "HYP",
  "not falsifiable as stated; retained as metaphor only", None),
 ("C005", "observer-frame and 4th-dimension language", "metaphor",
  "SOURCE_HYPOTHESIS", "SRC",
  "not falsifiable as stated; retained as source language", None),
 ("C006", "two or three linked temporal phases",
  "mathematical_model", "SOURCE_HYPOTHESIS", "HYP",
  "DOWNGRADED by the v4.2.1 audit: no phase-count model is "
  "implemented, so no comparison against a one-phase null exists. "
  "Falsified if a one-phase model fits state-change data as well by "
  "information criterion", None),
 ("C007", "Arisaka 'space is time' audit", "metaphor",
  "SOURCE_HYPOTHESIS", "SRC",
  "claim is a source statement; the audit records page-level "
  "provenance and does not endorse it", None),
 ("C008", "MePMoS", "engineering_analogy", "ENGINEERING_PROTOTYPE",
  "ENG", "architecture fails its own stated engineering benchmark",
  None),
 ("C009", "Neural Holographic Tomography", "engineering_analogy",
  "ENGINEERING_PROTOTYPE", "ENG",
  "reconstruction fails on synthetic phantoms", None),
 ("C010", "Holographic Ring Attractor Lattice",
  "mathematical_model", "REDUCED_ORDER_VALIDATED", "DER",
  "ring attractor does not form or does not maintain a bump after "
  "the input is removed, under the declared noise level",
  "ring_attractor"),
 ("C011", "Q-HAL, BFFT, CAIRO, TERESA", "engineering_analogy",
  "ENGINEERING_PROTOTYPE", "ENG",
  "components fail their declared software benchmarks", None),
 ("C012", "space-to-time operator S_to_T", "mathematical_model",
  "SOURCE_HYPOTHESIS", "HYP",
  "no operator definition reproduces the claimed mapping with "
  "declared units", None),
 ("C013", "alpha/theta/gamma phase timing",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "DER",
  "phase-dependent coupling is absent beyond surrogate-corrected "
  "chance", "phase_amplitude_coupling"),
 ("C014", "language and creativity as frequency-time navigation",
  "metaphor", "SOURCE_HYPOTHESIS", "HYP",
  "no operational measure distinguishes it from a semantic-search "
  "null model", None),
 ("C015", "microtubules as candidate coherence transformers",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "measured decoherence time at 310 K is below the causal threshold "
  "of C016 (Tegmark-type estimate)", "microtubule_threshold"),
 ("C016", "tau_c * eta_phi * K_cross > theta_neural_bias",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "the product stays below threshold under any physiological "
  "parameter set; see microtubule_threshold()",
  "microtubule_threshold"),
 ("C017", "ordered water and aromatic-electron transitions",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "no coherent transition observed in the declared band in vivo",
  None),
 ("C018", "Hz/kHz/MHz/GHz/THz resonance claims",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "claimed resonances are absent above the look-elsewhere-corrected "
  "noise floor", None),
 ("C019", "fractal time-crystal hypothesis",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "no subharmonic response persists without drive", None),
 ("C020", "6G/THz instrumentation analogy", "engineering_analogy",
  "ENGINEERING_PROTOTYPE", "ENG",
  "ANALOGY ONLY: THz hardware existing is not evidence that the "
  "brain receives THz (G34)", None),
 ("C021", "100 GHz-10 THz measurement lane", "engineering_analogy",
  "PROTOCOL_READY_HARDWARE_REQUIRED", "ENG",
  "instrument noise floor cannot reach the claimed signal level",
  None),
 ("C022", "superheterodyne receiver analogy", "engineering_analogy",
  "ENGINEERING_PROTOTYPE", "ENG",
  "ANALOGY ONLY: no biological mixer element identified (G34)",
  None),
 ("C023", "cross-frequency coupling and downconversion",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "DER",
  "PAC is absent beyond surrogate-corrected chance in the declared "
  "dataset", "phase_amplitude_coupling"),
 ("C024", "interpersonal synchrony and mentorship",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "DER",
  "measured synchrony does not exceed pseudo-pair surrogates",
  "synchrony_with_surrogates"),
 ("C025", "firefly and pendulum synchronization analogies",
  "mathematical_model", "REDUCED_ORDER_VALIDATED", "DER",
  "the simulation fails to reproduce the analytic K_c = 2 gamma",
  "kuramoto"),
 ("C026", "gamma 40-160 Hz and consciousness claims",
  "established_cognitive_evidence", "SOURCE_HYPOTHESIS", "HYP",
  "gamma power dissociates from report under anesthesia-graded "
  "designs; correlation is not constitution", None),
 ("C027", "dreams versus wake permanence", "mathematical_model",
  "SOURCE_HYPOTHESIS", "HYP",
  "no measurable constraint difference between dream and wake state "
  "under the declared operationalization (C041)",
  "dream_wake_constraint"),
 ("C028", "temporal permanence through other observers", "metaphor",
  "SOURCE_HYPOTHESIS", "HYP",
  "not falsifiable as stated; retained as metaphor", None),
 ("C029", "aura as social/behavioral influence radius",
  "established_cognitive_evidence", "SOURCE_HYPOTHESIS", "HYP",
  "no behavioral influence gradient with distance beyond "
  "sensory-cue controls; NOT an electromagnetic claim", None),
 ("C030", "external field or receiver hypothesis",
  "speculative_external_field_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "shielded-versus-unshielded designs show no difference; K_ext "
  "quarantined (C042)", "dream_wake_constraint"),
 ("C031", "multiverse and quantum-state influence",
  "speculative_external_field_mechanism", "SOURCE_HYPOTHESIS", "SRC",
  "outside current empirical reach; retained without endorsement",
  None),
 ("C032", "quantum cognition versus literal quantum brain",
  "mathematical_model", "REDUCED_ORDER_VALIDATED", "DER",
  "the parameter-free QQ equality is violated by the data, or the "
  "classical comparator fits as well (then no quantum-probability "
  "model is warranted). BOUNDARY: quantum-probability models of "
  "decisions are NOT evidence of quantum processes in neurons (G37)",
  "order_effect_model"),
 ("C033", "entanglement and nonclassical-correlation tests",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "no CHSH-type violation in any biological preparation", None),
 ("C034", "manifestation as attention-shaped affordance selection",
  "established_cognitive_evidence", "SOURCE_HYPOTHESIS", "HYP",
  "DOWNGRADED by the v4.2.1 audit: no affordance-selection model is "
  "implemented. Falsified if attention manipulation does not change "
  "action-selection rates", None),
 ("C035", "path-integral language as metaphor unless formalized",
  "metaphor", "SOURCE_HYPOTHESIS", "SRC",
  "retained as metaphor; formalization required before any claim",
  None),
 ("C036", "active inference and affordances",
  "established_cognitive_evidence", "SOURCE_HYPOTHESIS", "HYP",
  "DOWNGRADED by the v4.2.1 audit: no free-energy model and no "
  "reactive-policy null are implemented. Falsified if the "
  "free-energy-style model fails to beat a reactive-policy null",
  None),
 ("C037", "first-person conduit/empty-mind origin report",
  "first_person_phenomenology", "SOURCE_HYPOTHESIS", "SRC",
  "PRIVATE: not a public scientific claim; not falsifiable (G38)",
  None),
 ("C038", "spirit/God/private myth layer", "private_myth",
  "SOURCE_HYPOTHESIS", "SRC",
  "PRIVATE: outside scientific adjudication; retained without "
  "endorsement or refutation (G38)", None),
 ("C039", "mystical language preserved without endorsement",
  "private_myth", "SOURCE_HYPOTHESIS", "SRC",
  "not a scientific claim; preserved verbatim, unendorsed", None),
 ("C040", "layer map: unknown-information -> molecular -> neural -> "
  "cognitive -> phenomenological", "mathematical_model",
  "SOURCE_HYPOTHESIS", "HYP",
  "DOWNGRADED by the v4.2.1 audit: the layer map is a documentation "
  "instrument, not a validated model. Falsified as an instrument if "
  "a claim crosses a layer boundary without a stated bridge law and "
  "the map fails to flag it", None),
 ("C041", "Dream-Wake Constraint Theory", "mathematical_model",
  "REDUCED_ORDER_VALIDATED", "HYP",
  "the constraint parameter fitted to dream reports does not "
  "separate from wake reports", "dream_wake_constraint"),
 ("C042", "Field-Constraint Layer and K_ext quarantine",
  "speculative_external_field_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "K_ext is identically zero in every fit; the layer exists so the "
  "hypothesis is testable and separable, not assumed",
  "dream_wake_constraint"),
 ("C043", "fragments-of-energy source family", "private_myth",
  "SOURCE_HYPOTHESIS", "SRC",
  "source family; no physical claim imported", None),
 ("C044", "sixth/seventh-sense separation",
  "first_person_phenomenology", "SOURCE_HYPOTHESIS", "HYP",
  "no discrimination performance above chance in a forced-choice "
  "design", None),
 ("C045", "social entrainment, speaker-listener coupling, mentoring",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "DER",
  "coupling does not exceed surrogate pairs",
  "synchrony_with_surrogates"),
 ("C046", "flow as subsystem coherence", "mathematical_model",
  "SOURCE_HYPOTHESIS", "HYP",
  "DOWNGRADED by the v4.2.1 audit: no flow model and no coherence "
  "index are implemented. Falsified if flow reports are uncorrelated "
  "with any coherence index", None),
 ("C047", "raising consciousness as coordination, not magic",
  "mathematical_model", "SOURCE_HYPOTHESIS", "HYP",
  "DOWNGRADED by the v4.2.1 audit: no coordination index is "
  "implemented against a group outcome. Falsified if the "
  "coordination index does not track the declared group outcome",
  None),
 ("C048", "'coherence is not truth' control", "mathematical_model",
  "REDUCED_ORDER_VALIDATED", "DER",
  "CONTROL: falsified as a control if a maximally coherent "
  "population cannot encode an arbitrary/false state; coherence "
  "measures order, not veridicality", "coherence_is_not_truth"),
 ("C049", "embodied spatial event memory for Hydrogenuine",
  "engineering_analogy", "ENGINEERING_PROTOTYPE", "ENG",
  "retrieval benchmark fails; NO consciousness claim (G39)", None),
 ("C050", "SWR-like replay and offline consolidation",
  "engineering_analogy", "ENGINEERING_PROTOTYPE", "ENG",
  "replay does not improve the declared benchmark", None),
 ("C051", "Q-HAL local world-memory block", "engineering_analogy",
  "ENGINEERING_PROTOTYPE", "ENG",
  "block fails its declared capacity/latency benchmark", None),
 ("C052", "BFFT transform/compression scaffold",
  "engineering_analogy", "ENGINEERING_PROTOTYPE", "ENG",
  "transform is not invertible within the declared error bound",
  None),
]

# Documents that explain each lane's models (T01-T10 deliverables).
LANE_DOCS = {
    "T01": "docs/v4/consciousness/RESONANT_STATE_CHANGE_FORMALISM.md",
    "T02": "docs/v4/consciousness/ARISAKA_AUDIT.md",
    "T03": "docs/v4/consciousness/MICROTUBULE_COHERENCE_AUDIT.md",
    "T04": "docs/v4/consciousness/THZ_INSTRUMENTATION_ROADMAP.md",
    "T05": "docs/v4/consciousness/SYNCHRONY_AND_MENTORSHIP.md",
    "T06": "docs/v4/consciousness/DREAM_WAKE_CONSTRAINT_THEORY.md",
    "T07": "docs/v4/consciousness/"
           "QUANTUM_COGNITION_AND_PHYSICS_BOUNDARY.md",
    "T08": "docs/v4/consciousness/"
           "PHENOMENOLOGY_AND_PRIVATE_MYTH_POLICY.md",
    "T09": "docs/v4/consciousness/"
           "HYDROGENUINE_SPATIAL_TEMPORAL_MEMORY.md",
    "T10": "docs/v4/consciousness/RESONANT_STATE_CHANGE_BOOK.md",
}

# Which agent owns which IDs (for the crosswalk and coverage ledger).
OWNER = {}
for _i in ["C001", "C002", "C003", "C004", "C005", "C006", "C012",
           "C014", "C034", "C035", "C036", "C040", "C046", "C047"]:
    OWNER[_i] = "T01"
for _i in ["C007", "C008", "C009", "C010", "C011"]:
    OWNER[_i] = "T02"
for _i in ["C015", "C016", "C017", "C019", "C033"]:
    OWNER[_i] = "T03"
for _i in ["C018", "C020", "C021", "C022"]:
    OWNER[_i] = "T04"
for _i in ["C013", "C023", "C024", "C025", "C026", "C045", "C048"]:
    OWNER[_i] = "T05"
for _i in ["C027", "C028", "C029", "C030", "C041", "C042", "C044"]:
    OWNER[_i] = "T06"
for _i in ["C031", "C032"]:
    OWNER[_i] = "T07"
for _i in ["C037", "C038", "C039", "C043"]:
    OWNER[_i] = "T08"
for _i in ["C049", "C050", "C051", "C052"]:
    OWNER[_i] = "T09"


def build_theory_registry() -> dict:
    out = {}
    for rid, title, layer, status, tag, falsif, model in _E:
        owner = OWNER.get(rid, "T10")
        out[rid] = make_record(
            "ConsciousnessLayerRecord", rid, title, "consciousness",
            status, [tag], layer=layer,
            failure_conditions=[falsif],
            model_symbol=model,
            owner_agent=owner,
            documentation_path=LANE_DOCS[owner],
            public=layer not in ("first_person_phenomenology",
                                 "private_myth"),
            quarantine="no consciousness record may be imported as "
                       "evidence into quartz computation")
    return out


def coverage_map() -> dict:
    return {rid: [rec["owner_agent"]]
            for rid, rec in build_theory_registry().items()}
