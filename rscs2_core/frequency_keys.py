"""Frequency-key registry F001-F052 (Agent C04; gates G10/G11).

Every value from the master coverage ledger, typed per the frequency
rules (exact physical frequency vs arithmetic motif vs source label vs
timing inverse vs dimensionless ratio vs angle-derived motif vs
non-frequency value). All derived arithmetic is verified by tests at
exact precision; MISSES are recorded at their exact separation (e.g.
21x195 = 4095, one full Hz below 4096 — never rounded into a match).
A look-elsewhere null model guards against numerology: no candidate
is promoted by numerical coincidence alone."""

from __future__ import annotations

import math

from .research_records import make_record

PHI = (1 + math.sqrt(5.0)) / 2.0


def _f(rid, title, kind, status, tags, **kw):
    return make_record("FrequencyKeyRecord", rid, title,
                       "computational", status, tags,
                       frequency_kind=kind, **kw)


def build_registry() -> dict:
    R = {}

    def add(rec):
        R[rec["record_id"]] = rec

    add(_f("F001", "4096 Hz carrier", "exact_physical_frequency",
           "CORE_VALIDATED", ["EST"], value_hz=4096.0,
           treatment="direct acoustic/non-contact scan (E01)",
           controls=["neighbor scan 4080-4112 Hz"]))
    add(_f("F002", "20.480 kHz = 4096*5", "harmonic_relation",
           "CORE_VALIDATED", ["DER"], value_hz=20480.0,
           relation="4096*5", treatment="sweep + specimen bridge"))
    add(_f("F003", "32.768 kHz = 4096*8 = 2^15",
           "harmonic_relation", "CORE_VALIDATED", ["DER", "EST"],
           value_hz=32768.0, relation="4096*8 == 2**15",
           treatment="oscillator reference + acoustic branch"))
    for rid, v, note in (("F004", 20.0, "compression-node electrode "
                          "baseline"),
                         ("F005", 19.8, "reported tolerance neighbor"),
                         ("F006", 21.0, "compare against 20 Hz"),
                         ("F008", 40.0, "gamma-adjacent control"),
                         ("F010", 41.0, "neighbor control"),
                         ("F011", 42.0, "neighbor + 7x6 branch"),
                         ("F012", 8.0, "octave base / ELF reference"),
                         ("F018", 20000.0, "broad reference")):
        add(_f(rid, f"{v} Hz", "exact_physical_frequency",
               "ENGINEERING_PROTOTYPE", ["ENG"], value_hz=v,
               treatment=note))
    add(_f("F007", "21*195 = 4095 Hz integer-lock hypothesis",
           "arithmetic_motif", "SOURCE_HYPOTHESIS", ["HYP"],
           value_hz=4095.0, relation="21*195",
           exact_miss_hz=1.0,
           note="EXACTLY 1 Hz below 4096; the miss is recorded, "
                "never rounded into a lock",
           failure_conditions=["no beat-frequency observable at "
                               "1 Hz under the declared protocol"]))
    add(_f("F009", "40.96 Hz = 4096/100", "harmonic_relation",
           "CORE_VALIDATED", ["DER"], value_hz=40.96,
           relation="4096/100",
           controls=["F008 40.00", "F010 41.00", "F011 42.00"]))
    add(_f("F013", "20.48 Hz lower bridge", "harmonic_relation",
           "CORE_VALIDATED", ["DER"], value_hz=20.48,
           relation="4096/200"))
    add(_f("F014", "5.12 kHz (20 Hz octave x256)",
           "harmonic_relation", "CORE_VALIDATED", ["DER"],
           value_hz=5120.0, relation="20*256"))
    add(_f("F015", "10.24 kHz (20 Hz octave x512)",
           "harmonic_relation", "CORE_VALIDATED", ["DER"],
           value_hz=10240.0, relation="20*512"))
    add(_f("F016", "5.1515 kHz overlap-workbook target",
           "source_label", "SOURCE_HYPOTHESIS", ["SRC"],
           value_hz=5151.5, source_ids=["SRC-V4X-VOGEL"]))
    add(_f("F017", "10.3030 kHz overlap-workbook target",
           "source_label", "SOURCE_HYPOTHESIS", ["SRC"],
           value_hz=10303.0, source_ids=["SRC-V4X-VOGEL"]))
    add(_f("F019", "20.6061 kHz source motif", "source_label",
           "SOURCE_HYPOTHESIS", ["SRC"], value_hz=20606.1))
    for rid, lo, hi, note in (
            ("F020", 18500.0, 21200.0, "broad first sweep"),
            ("F021", 19800.0, 21200.0, "focused 20.48 kHz sweep"),
            ("F022", 10000.0, 12700.0, "secondary sweep"),
            ("F023", 24500.0, 25500.0, "tertiary sweep")):
        add(_f(rid, f"sweep {lo/1000:g}-{hi/1000:g} kHz",
               "exact_physical_frequency", "ENGINEERING_PROTOTYPE",
               ["ENG"], band_hz=[lo, hi], treatment=note))
    for rid, v in (("F024", 1496.0), ("F025", 587.0),
                   ("F026", 644.0)):
        add(_f(rid, f"{v:g} Hz sound-key", "source_label",
               "SOURCE_HYPOTHESIS", ["SRC"], value_hz=v,
               note="frozen v3 closure golden rows are the validated "
                    "arithmetic layer"))
    for rid, v in (("F027", 465.0), ("F028", 787.0),
                   ("F029", 880.0)):
        add(_f(rid, f"{v:g} Hz body-mapped fork claim",
               "source_label", "SOURCE_HYPOTHESIS", ["SRC"],
               value_hz=v))
    add(_f("F030", "465*44 = 20460 Hz candidate",
           "arithmetic_motif", "SOURCE_HYPOTHESIS", ["HYP"],
           value_hz=20460.0, relation="465*44",
           exact_miss_hz=20.0,
           note="20 Hz below 20480; separation recorded exactly"))
    add(_f("F031", "787*26 = 20462 Hz candidate",
           "arithmetic_motif", "SOURCE_HYPOTHESIS", ["HYP"],
           value_hz=20462.0, relation="787*26", exact_miss_hz=18.0))
    add(_f("F032", "210.42*98 = 20621.16 Hz candidate",
           "arithmetic_motif", "SOURCE_HYPOTHESIS", ["HYP"],
           value_hz=20621.16, relation="210.42*98"))
    add(_f("F033", "4160*5 = 20800 Hz neighbor",
           "arithmetic_motif", "ENGINEERING_PROTOTYPE", ["ENG"],
           value_hz=20800.0, relation="4160*5"))
    add(_f("F034", "4225*5 = 21125 Hz neighbor",
           "arithmetic_motif", "ENGINEERING_PROTOTYPE", ["ENG"],
           value_hz=21125.0, relation="4225*5"))
    add(_f("F035", "4225*8 = 33800 Hz extended",
           "arithmetic_motif", "ENGINEERING_PROTOTYPE", ["ENG"],
           value_hz=33800.0, relation="4225*8"))
    add(_f("F036", "10,20,30,50,80,130,210,340,550 Hz vortex "
           "sequence", "arithmetic_motif", "SOURCE_HYPOTHESIS",
           ["SRC", "HYP"],
           sequence_hz=[10, 20, 30, 50, 80, 130, 210, 340, 550],
           note="additive (Fibonacci-like) recurrence a(n)=a(n-1)+"
                "a(n-2) holds from the third term (verified)"))
    add(_f("F037", "symbolic families 7,9,14,21,42",
           "arithmetic_motif", "SOURCE_HYPOTHESIS", ["HYP"],
           sequence=[7, 9, 14, 21, 42],
           note="hypothesis only; no physical unit attached"))
    add(_f("F038", "multiples-of-9 audit", "arithmetic_motif",
           "SOURCE_HYPOTHESIS", ["HYP"],
           note="symbolic harmonic audit; look-elsewhere model "
                "applies"))
    add(_f("F039", "51.843deg x20 chains (x128/x256/x4096)",
           "angle_derived_motif", "SOURCE_HYPOTHESIS", ["HYP"],
           base=51.843, products={"x20": 1036.86,
                                  "x20x128": 132718.08,
                                  "x20x256": 265436.16},
           note="an angle in degrees times integers is NOT a "
                "frequency; dimensional status: numeric motif only"))
    add(_f("F040", "60 x 4096 phase-factor branch",
           "angle_derived_motif", "SOURCE_HYPOTHESIS", ["HYP"],
           product=245760.0,
           note="DIMENSIONAL AUDIT: degrees x hertz has units "
                "deg*Hz, not Hz; retained as numeric motif"))
    add(_f("F041", "46 ms pulse-timing candidate", "timing_inverse",
           "SOURCE_HYPOTHESIS", ["HYP"], period_s=0.046,
           inverse_hz=1 / 0.046))
    add(_f("F042", "60*pi/4096 s timing relation", "timing_inverse",
           "SOURCE_HYPOTHESIS", ["DER", "HYP"],
           period_s=60 * math.pi / 4096,
           note="= 0.0460194 s; within 0.05 ms of the 46 ms F041 "
                "candidate (relation recorded, not promoted)"))
    add(_f("F043", "192-cycle binary timing", "timing_inverse",
           "SOURCE_HYPOTHESIS", ["HYP"], cycles=192,
           period_at_4096_s=192 / 4096.0,
           note="192/4096 = 0.046875 s (exact)"))
    add(_f("F044", "phi^8 timing", "dimensionless_ratio",
           "SOURCE_HYPOTHESIS", ["HYP"], value=PHI ** 8,
           note="phi^8 = 46.9787...; dimensionless unless a unit is "
                "declared; proximity to 46-47 ms is a numeric motif"))
    add(_f("F045", "552 ms macrocycle", "timing_inverse",
           "SOURCE_HYPOTHESIS", ["HYP"], period_s=0.552))
    add(_f("F046", "2260.992 cycles at 4096 Hz in 552 ms",
           "arithmetic_motif", "CORE_VALIDATED", ["DER"],
           value=2260.992, relation="4096*0.552",
           note="exact arithmetic; NON-INTEGER cycle count -> the "
                "552 ms window does NOT close at 4096 Hz"))
    add(_f("F047", "1507.328 cycles half-spacing branch",
           "arithmetic_motif", "CORE_VALIDATED", ["DER"],
           value=1507.328, relation="(2/3)*2260.992",
           note="exactly two-thirds of F046; also non-integer"))
    add(_f("F048", "density ladder 64*8^(n-1)", "arithmetic_motif",
           "SOURCE_HYPOTHESIS", ["SRC", "HYP"],
           ladder=[64 * 8 ** n for n in range(0, 6)],
           source_ids=["SRC-V4X-LORE-DECKS"]))
    add(_f("F049", "2.45 GHz powers-of-eight audit",
           "arithmetic_motif", "SOURCE_HYPOTHESIS", ["HYP"],
           value_hz=2.45e9,
           audit="2.45e9 / 8^10 = 2.2817... (NOT integral); "
                 "2.45e9/4096 = 598144.53 (NOT integral); no exact "
                 "powers-of-eight relation exists — recorded as a "
                 "numerical miss",))
    add(_f("F050", "454 Omega source value", "non_frequency_value",
           "SOURCE_HYPOTHESIS", ["SRC"], value_ohm=454.0,
           note="resistance, preserved as a non-frequency value; "
                "never treated as Hz"))
    add(_f("F051", "7.6 Hz phi-EEG lead", "source_label",
           "SOURCE_HYPOTHESIS", ["SRC", "HYP"], value_hz=7.6,
           treatment="literature replication candidate (T-lane)"))
    add(_f("F052", "f(n) = f0*phi^n neural lattice hypothesis",
           "dimensionless_ratio", "SOURCE_HYPOTHESIS", ["HYP"],
           ratio=PHI,
           failure_conditions=["EEG peak spacing not phi-distributed "
                               "under the look-elsewhere model"]))
    return R


def coincidence_significance(candidate_hz: float, targets_hz: list,
                             tolerance_hz: float,
                             band_hz: tuple,
                             n_candidates_tried: int = 1) -> dict:
    """Look-elsewhere null model (gate G11): under a uniform null on
    the band, P(a single candidate lands within +/-tol of ANY of K
    targets) ~ K*2*tol/W; with M tried candidates the expected number
    of hits is E = M*K*2*tol/W. A 'match' with E >~ 1 is NOT
    significant. No promotion by coincidence alone, ever."""
    lo, hi = band_hz
    if not (hi > lo and tolerance_hz >= 0):
        raise ValueError("bad band/tolerance")
    W = hi - lo
    K = len(targets_hz)
    p_single = min(1.0, K * 2.0 * tolerance_hz / W)
    expected_hits = n_candidates_tried * p_single
    nearest = min(targets_hz, key=lambda t: abs(t - candidate_hz)) \
        if targets_hz else None
    sep = abs(nearest - candidate_hz) if nearest is not None else None
    hit = sep is not None and sep <= tolerance_hz
    return {"nearest_target_hz": nearest, "separation_hz": sep,
            "within_tolerance": hit,
            "p_single_candidate": p_single,
            "expected_chance_hits": expected_hits,
            "significant": bool(hit and expected_hits < 0.05),
            "rule": "no promotion by numerical coincidence alone; "
                    "matches with expected_chance_hits >= 0.05 are "
                    "NOT significant (look-elsewhere)"}
