"""T01-T10 theory registry: C001-C052 with layer, status, evidence
tag, and falsification condition. Every entry states which of the
eight CONSCIOUSNESS_LAYERS it lives on so that a metaphor is never
read as established evidence (G34/G38/G40)."""

from __future__ import annotations

from rscs2_core.research_records import make_record

# (id, title, layer, status, tag, falsification condition)
_E = [
 ("C001", "decaying resonance of state change", "mathematical_model",
  "REDUCED_ORDER_VALIDATED", "DER",
  "no damped-oscillator fit to any operationalized state-change "
  "series outperforms an AR(1) null"),
 ("C002", "awareness of time as current velocity of state change",
  "mathematical_model", "REDUCED_ORDER_VALIDATED", "DER",
  "reported time-rate is uncorrelated with |d(state)/dt| proxies "
  "across participants"),
 ("C003", "subjective time from update/novelty/arousal/memory",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "EST",
  "duration judgements are unaffected by novelty and arousal "
  "manipulations under preregistered analysis"),
 ("C004", "block-universe wavefront versus snapshot", "metaphor",
  "SOURCE_HYPOTHESIS", "HYP",
  "not falsifiable as stated; retained as metaphor only"),
 ("C005", "observer-frame and 4th-dimension language", "metaphor",
  "SOURCE_HYPOTHESIS", "SRC",
  "not falsifiable as stated; retained as source language"),
 ("C006", "two or three linked temporal phases",
  "mathematical_model", "REDUCED_ORDER_VALIDATED", "HYP",
  "a one-phase model fits state-change data as well as the "
  "two/three-phase model by information criterion"),
 ("C007", "Arisaka 'space is time' audit", "metaphor",
  "SOURCE_HYPOTHESIS", "SRC",
  "claim is a source statement; audit records page-level provenance "
  "and does not endorse it"),
 ("C008", "MePMoS", "engineering_analogy", "ENGINEERING_PROTOTYPE",
  "ENG", "architecture fails its own stated engineering benchmark"),
 ("C009", "Neural Holographic Tomography", "engineering_analogy",
  "ENGINEERING_PROTOTYPE", "ENG",
  "reconstruction fails on synthetic phantoms"),
 ("C010", "Holographic Ring Attractor Lattice",
  "mathematical_model", "REDUCED_ORDER_VALIDATED", "DER",
  "ring attractor does not maintain a bump under the declared "
  "noise level"),
 ("C011", "Q-HAL, BFFT, CAIRO, TERESA", "engineering_analogy",
  "ENGINEERING_PROTOTYPE", "ENG",
  "components fail their declared software benchmarks"),
 ("C012", "space-to-time operator S_to_T", "mathematical_model",
  "SOURCE_HYPOTHESIS", "HYP",
  "no operator definition reproduces the claimed mapping with "
  "declared units"),
 ("C013", "alpha/theta/gamma phase timing",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "EST",
  "phase-dependent performance effects absent under preregistered "
  "replication"),
 ("C014", "language and creativity as frequency-time navigation",
  "metaphor", "SOURCE_HYPOTHESIS", "HYP",
  "no operational measure distinguishes it from a semantic-search "
  "null model"),
 ("C015", "microtubules as candidate coherence transformers",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "measured decoherence time at 310 K is below the causal threshold "
  "of C016 (Tegmark-type estimate)"),
 ("C016", "tau_c * eta_phi * K_cross > theta_neural_bias",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "the product stays below threshold under any physiological "
  "parameter set; see microtubule_threshold()"),
 ("C017", "ordered water and aromatic-electron transitions",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "no coherent transition observed in the declared band in vivo"),
 ("C018", "Hz/kHz/MHz/GHz/THz resonance claims",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "claimed resonances are absent above the look-elsewhere-corrected "
  "noise floor"),
 ("C019", "fractal time-crystal hypothesis",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "no subharmonic response persists without drive"),
 ("C020", "6G/THz instrumentation analogy", "engineering_analogy",
  "ENGINEERING_PROTOTYPE", "ENG",
  "ANALOGY ONLY: THz hardware existing is not evidence that the "
  "brain receives THz (G34)"),
 ("C021", "100 GHz-10 THz measurement lane", "engineering_analogy",
  "PROTOCOL_READY_HARDWARE_REQUIRED", "ENG",
  "instrument noise floor cannot reach the claimed signal level"),
 ("C022", "superheterodyne receiver analogy", "engineering_analogy",
  "ENGINEERING_PROTOTYPE", "ENG",
  "ANALOGY ONLY: no biological mixer element identified (G34)"),
 ("C023", "cross-frequency coupling and downconversion",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "EST",
  "PAC absent beyond surrogate-corrected chance in the declared "
  "dataset"),
 ("C024", "interpersonal synchrony and mentorship",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "EST",
  "measured synchrony does not exceed pseudo-pair surrogates"),
 ("C025", "firefly and pendulum synchronization analogies",
  "mathematical_model", "REDUCED_ORDER_VALIDATED", "DER",
  "Kuramoto model fails to reproduce its own analytic K_c"),
 ("C026", "gamma 40-160 Hz and consciousness claims",
  "established_cognitive_evidence", "SOURCE_HYPOTHESIS", "HYP",
  "gamma power dissociates from report under anesthesia-graded "
  "designs; correlation is not constitution"),
 ("C027", "dreams versus wake permanence", "mathematical_model",
  "SOURCE_HYPOTHESIS", "HYP",
  "no measurable constraint difference between dream and wake state "
  "under the declared operationalization (C041)"),
 ("C028", "temporal permanence through other observers", "metaphor",
  "SOURCE_HYPOTHESIS", "HYP",
  "not falsifiable as stated; retained as metaphor"),
 ("C029", "aura as social/behavioral influence radius",
  "established_cognitive_evidence", "SOURCE_HYPOTHESIS", "HYP",
  "no behavioral influence gradient with distance beyond "
  "sensory-cue controls; NOT an electromagnetic claim"),
 ("C030", "external field or receiver hypothesis",
  "speculative_external_field_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "shielded-versus-unshielded designs show no difference; K_ext "
  "quarantined (C042)"),
 ("C031", "multiverse and quantum-state influence",
  "speculative_external_field_mechanism", "SOURCE_HYPOTHESIS", "SRC",
  "outside current empirical reach; retained without endorsement"),
 ("C032", "quantum cognition versus literal quantum brain",
  "mathematical_model", "REDUCED_ORDER_VALIDATED", "EST",
  "BOUNDARY: quantum-probability models of decisions are NOT "
  "evidence of quantum processes in neurons (G37)"),
 ("C033", "entanglement and nonclassical-correlation tests",
  "speculative_biological_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "no CHSH-type violation in any biological preparation"),
 ("C034", "manifestation as attention-shaped affordance selection",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "EST",
  "attention manipulation does not change action-selection rates"),
 ("C035", "path-integral language as metaphor unless formalized",
  "metaphor", "SOURCE_HYPOTHESIS", "SRC",
  "retained as metaphor; formalization required before any claim"),
 ("C036", "active inference and affordances",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "EST",
  "free-energy-style model fails to beat a reactive-policy null"),
 ("C037", "first-person conduit/empty-mind origin report",
  "first_person_phenomenology", "SOURCE_HYPOTHESIS", "SRC",
  "PRIVATE: not a public scientific claim; not falsifiable (G38)"),
 ("C038", "spirit/God/private myth layer", "private_myth",
  "SOURCE_HYPOTHESIS", "SRC",
  "PRIVATE: outside scientific adjudication; retained without "
  "endorsement or refutation (G38)"),
 ("C039", "mystical language preserved without endorsement",
  "private_myth", "SOURCE_HYPOTHESIS", "SRC",
  "not a scientific claim; preserved verbatim, unendorsed"),
 ("C040", "layer map: unknown-information -> molecular -> neural -> "
  "cognitive -> phenomenological", "mathematical_model",
  "REDUCED_ORDER_VALIDATED", "DER",
  "a layer boundary is crossed by a claim without a stated bridge "
  "law (this map is the audit instrument)"),
 ("C041", "Dream-Wake Constraint Theory", "mathematical_model",
  "REDUCED_ORDER_VALIDATED", "HYP",
  "constraint parameter fitted to dream reports does not separate "
  "from wake reports"),
 ("C042", "Field-Constraint Layer and K_ext quarantine",
  "speculative_external_field_mechanism", "SOURCE_HYPOTHESIS", "HYP",
  "K_ext is identically zero in every fit; the layer exists so the "
  "hypothesis is testable and separable, not assumed"),
 ("C043", "fragments-of-energy source family", "private_myth",
  "SOURCE_HYPOTHESIS", "SRC",
  "source family; no physical claim imported"),
 ("C044", "sixth/seventh-sense separation",
  "first_person_phenomenology", "SOURCE_HYPOTHESIS", "HYP",
  "no discrimination performance above chance in a forced-choice "
  "design"),
 ("C045", "social entrainment, speaker-listener coupling, mentoring",
  "established_cognitive_evidence", "REDUCED_ORDER_VALIDATED", "EST",
  "coupling does not exceed surrogate pairs"),
 ("C046", "flow as subsystem coherence", "mathematical_model",
  "REDUCED_ORDER_VALIDATED", "HYP",
  "flow reports are uncorrelated with any coherence index"),
 ("C047", "raising consciousness as coordination, not magic",
  "mathematical_model", "REDUCED_ORDER_VALIDATED", "DER",
  "coordination index does not track the declared group outcome"),
 ("C048", "'coherence is not truth' control", "mathematical_model",
  "REDUCED_ORDER_VALIDATED", "DER",
  "CONTROL: a maximally coherent oscillator population can encode "
  "an arbitrary/false state; coherence measures order, not "
  "veridicality (demonstrated in coherence_is_not_truth())"),
 ("C049", "embodied spatial event memory for Hydrogenuine",
  "engineering_analogy", "ENGINEERING_PROTOTYPE", "ENG",
  "retrieval benchmark fails; NO consciousness claim (G39)"),
 ("C050", "SWR-like replay and offline consolidation",
  "engineering_analogy", "ENGINEERING_PROTOTYPE", "ENG",
  "replay does not improve the declared benchmark"),
 ("C051", "Q-HAL local world-memory block", "engineering_analogy",
  "ENGINEERING_PROTOTYPE", "ENG",
  "block fails its declared capacity/latency benchmark"),
 ("C052", "BFFT transform/compression scaffold",
  "engineering_analogy", "ENGINEERING_PROTOTYPE", "ENG",
  "transform is not invertible within the declared error bound"),
]


def build_theory_registry() -> dict:
    out = {}
    for rid, title, layer, status, tag, falsif in _E:
        out[rid] = make_record(
            "ConsciousnessLayerRecord", rid, title, "consciousness",
            status, [tag], layer=layer,
            failure_conditions=[falsif],
            public=layer not in ("first_person_phenomenology",
                                 "private_myth"),
            quarantine="no consciousness record may be imported as "
                       "evidence into quartz computation")
    return out


def coverage_map() -> dict:
    return {rid: ["T-lane theory registry"]
            for rid in build_theory_registry()}
