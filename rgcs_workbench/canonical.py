"""Canonical data model (v4.5 pack, P01/05_DATA_MODEL).

Typed records with stable IDs, schema version, provenance, evidence
class, privacy class, and revision lineage. The store is populated
FROM the live repository modules (fkey_instrument, resonator_platform,
rscs2_core Eye analysis, sources registry) — never from spreadsheet
cells — so the workbook is always a downstream projection.

Nothing here fabricates a physical result: every physical row is
SOURCE_CLAIM, ANALYTIC_MODEL, NUMERICAL_SIMULATION, or SYNTHETIC_RUN,
and the pre-arrival specimen stays PREARRIVAL_UNVERIFIED."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field

from . import EVIDENCE_CLASSES, PRIVACY_CLASSES, SCHEMA_VERSION


class CanonicalError(ValueError):
    pass


def _rid(kind: str, *parts) -> str:
    h = hashlib.sha256("|".join(str(p) for p in parts)
                       .encode()).hexdigest()[:10]
    return f"{kind}-{h}"


@dataclass
class Record:
    id: str
    kind: str
    evidence_class: str
    privacy_class: str = "PUBLIC"
    provenance: str = ""
    fields: dict = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        if self.evidence_class not in EVIDENCE_CLASSES:
            raise CanonicalError(
                f"{self.id}: unknown evidence class "
                f"{self.evidence_class!r}")
        if self.privacy_class not in PRIVACY_CLASSES:
            raise CanonicalError(
                f"{self.id}: unknown privacy class "
                f"{self.privacy_class!r}")

    def as_row(self) -> dict:
        return {"id": self.id, "kind": self.kind,
                "evidence_class": self.evidence_class,
                "privacy_class": self.privacy_class,
                "provenance": self.provenance, **self.fields}


class CanonicalStore:
    """The authoritative registry. build() populates it deterministically
    from the live modules; export honours a privacy filter."""

    def __init__(self):
        self.tables: dict[str, list[Record]] = {}

    def add(self, table: str, rec: Record) -> None:
        self.tables.setdefault(table, []).append(rec)

    def rows(self, table: str, include_private: bool = False) -> list:
        out = []
        for r in self.tables.get(table, []):
            if not include_private and r.privacy_class == "PRIVATE":
                continue
            out.append(r.as_row())
        return out

    def counts(self) -> dict:
        return {t: len(v) for t, v in self.tables.items()}


# --- population from live modules ---------------------------------------------

def _frequency_keys(store: CanonicalStore) -> None:
    from fkey_instrument.relations import key_registry
    for kid, k in key_registry().items():
        store.add("frequency_keys", Record(
            id=kid, kind="frequency_key",
            evidence_class="SOURCE_CLAIM" if k["status"]
            == "SOURCE_CLAIM" else "DERIVED_ARITHMETIC",
            provenance=k["provenance"],
            fields={"hz": str(k["hz"]),
                    "hz_float": float(k["hz"]),
                    "status": k["status"],
                    "tags": ",".join(k["tags"])}))


def _relations(store: CanonicalStore) -> None:
    from fkey_instrument.relations import rank, seed_relations
    for i, r in enumerate(rank(seed_relations())):
        inp = " + ".join(f"{c}x{f}" for c, f in r.inputs)
        store.add("harmonic_relations", Record(
            id=_rid("REL", inp, r.output_hz),
            kind="frequency_relation",
            evidence_class="DERIVED_ARITHMETIC",
            provenance="fkey_instrument.relations.seed_relations",
            fields={"expression": inp,
                    "output_hz": str(r.output_hz),
                    "target_hz": str(r.target_hz),
                    "primary_class": r.primary_class,
                    "order": r.order,
                    "exact": r.exact,
                    "abs_error_hz": str(r.abs_error_hz),
                    "note": r.note}))


def _specimens(store: CanonicalStore) -> None:
    from fkey_instrument.crystal_mode import (candidate_band,
                                              prearrival_record,
                                              screening_modes,
                                              target_errors)
    rec = prearrival_record()
    store.add("specimens", Record(
        id=rec["specimen_id"], kind="specimen_revision",
        evidence_class="SOURCE_CLAIM",
        privacy_class="PUBLIC_SAFE",   # listing id is public-safe;
        #                                seller/order details are not
        provenance="pack data specimen_prearrival.json",
        fields={"revision": rec["revision"], "status": rec["status"],
                "length_mm": rec["claimed_geometry"]["length_mm"],
                "facets": rec["claimed_geometry"]["facets"],
                "material_claim": rec["material_claim"],
                "warning": rec["warning"]}))
    m = screening_modes()
    band = candidate_band()
    err = target_errors()
    store.add("mode_estimates", Record(
        id=_rid("MODE", rec["specimen_id"], "quarter"),
        kind="mode_estimate",
        evidence_class="ANALYTIC_MODEL",
        provenance="crystal_mode.screening_modes (LEVEL0_1D_ROD)",
        fields={"model_level": m["model_level"],
                "quarter_wave_hz": float(
                    m["longitudinal"]["quarter_wave_hz"]),
                "half_wave_hz": float(
                    m["longitudinal"]["half_wave_hz"]),
                "target_hz": 20480,
                "rel_error": float(err["quarter_vs_20480"]["rel"]),
                "band_lo_hz": float(band["band_lo_hz"]),
                "band_hi_hz": float(band["band_hi_hz"]),
                "note": "search band, not a magic frequency; seller "
                        "geometry, unmeasured"}))


def _timing_recipes(store: CanonicalStore) -> None:
    from fkey_instrument.optimizer import candidate_families
    for fam in candidate_families():
        store.add("timing_recipes", Record(
            id=_rid("RCP", fam["family"]),
            kind="drive_recipe",
            evidence_class="ANALYTIC_MODEL",
            provenance="fkey_instrument.optimizer.candidate_families",
            fields={"family": fam["family"], "kind": fam["kind"],
                    "frequency_hz": fam["f"],
                    "mechanism": fam["mechanism"],
                    "order": fam["order"],
                    "hypothesis": fam.get("hypothesis", ""),
                    "is_control": bool(fam.get("control"))}))


def _hypotheses(store: CanonicalStore) -> None:
    from fkey_instrument.optimizer import hypothesis_register
    for hid, h in hypothesis_register().items():
        store.add("hypotheses", Record(
            id=hid, kind="hypothesis",
            evidence_class="ANALYTIC_MODEL",
            provenance="fkey_instrument.optimizer.HYPOTHESES",
            fields={"statement": h["statement"],
                    "mechanism": h["mechanism"],
                    "status": h["status"],
                    "prediction": h["prediction"],
                    "disconfirmed_by": h["disconfirmed_by"]}))


def _eye(store: CanonicalStore) -> None:
    from rscs2_core.eye_ladder_analysis import (CANONICAL_V41,
                                                V421_LADDER)
    store.add("eye_results", Record(
        id="EYE-V41-CANONICAL", kind="eye_record",
        evidence_class="NUMERICAL_SIMULATION",
        provenance="rscs2_core.eye_ladder_analysis.CANONICAL_V41",
        fields={"candidate_mm": str(CANONICAL_V41["candidate_mm"]),
                "station_mm": str(CANONICAL_V41["station_mm"]),
                "separation_mm": CANONICAL_V41["separation_mm"],
                "halfwidth_mm": CANONICAL_V41["halfwidth_mm"],
                "status": "resolution-limited; preserved unchanged",
                "note": "computational, idealized model; the physical "
                        "Eye hypothesis is UNTESTED"}))
    lv = V421_LADDER["levels"]["cl1.5"]
    store.add("eye_results", Record(
        id="EYE-V421-V5", kind="eye_record",
        evidence_class="NUMERICAL_SIMULATION",
        provenance="rscs2_core.eye_ladder_analysis.V421_LADDER",
        fields={"candidate_mm": str(lv["centroid_mm"]),
                "spacing_mm": lv["spacing_mm"],
                "separation_mm": V421_LADDER["separation_mm"],
                "halfwidth_mm": V421_LADDER["halfwidth_mm"],
                "status": V421_LADDER["verdict"],
                "note": "finer ladder; one apex feature, two "
                        "estimates (see EYE_CLAIM_CARD v4)"}))


def _resonator(store: CanonicalStore) -> None:
    from resonator_platform.campaign import run_campaign
    r = run_campaign(seed=7)
    cert = r["certificate"]
    store.add("resonator_platform", Record(
        id=cert["specimen_id"], kind="resonator_certificate",
        evidence_class="SYNTHETIC_RUN",
        provenance="resonator_platform.campaign.run_campaign(seed=7)",
        fields={"predicted_hz": round(r["predicted_f01_hz"], 3),
                "target_hz": round(r["target_hz"], 3),
                "final_fitted_hz": round(r["final_fitted_hz"], 3),
                "accepted": r["accepted"],
                "iterations": r["iterations"],
                "synthetic": True,
                "banner": cert["banner"][:60]}))


def _hardware(store: CanonicalStore) -> None:
    from fkey_instrument.boards import BOARD_PROFILES
    for name, p in BOARD_PROFILES.items():
        if name in ("UNKNOWN", "SIMULATOR"):
            continue
        store.add("hardware_bom", Record(
            id=_rid("HW", name), kind="board_profile",
            evidence_class="SOURCE_CLAIM",
            provenance="fkey_instrument.boards (community docs)",
            fields={"board": name,
                    "verified": p.get("verified", False),
                    "candidate_output_pins":
                        str(p.get("candidate_output_pins")),
                    "note": "candidate profile; verify via A14 "
                            "self-test before naming an output pin"}))
    for item in ("ESP32-CYD board", "logic-level MOSFET (3.3V gate "
                 "verified)", "piezo disc x2", "op-amp pickup front "
                 "end", "DS18B20 temperature", "fused current-limited "
                 "supply"):
        store.add("hardware_bom", Record(
            id=_rid("BOM", item), kind="bom_item",
            evidence_class="ANALYTIC_MODEL",
            provenance="docs/v4/fkey/BOM_WIRING_GEN0.md",
            fields={"item": item, "status": "NOT_PURCHASED"}))


def _experiments(store: CanonicalStore) -> None:
    from fkey_instrument.optimizer import CAMPAIGNS
    for i, c in enumerate(CAMPAIGNS):
        store.add("experiment_queue", Record(
            id=_rid("EXP", c), kind="experiment",
            evidence_class="ANALYTIC_MODEL",
            provenance="fkey_instrument.optimizer.CAMPAIGNS",
            fields={"order": i + 1, "campaign": c,
                    "status": "PROTOCOL_READY_HARDWARE_REQUIRED"}))


def _corrections(store: CanonicalStore) -> None:
    corr = [
        ("FK-CORR-001", "quarter-wave and half-wave percentage errors "
         "are ONE v/L ratio, not two agreements",
         "fkey_instrument.crystal_mode.target_errors"),
        ("V4X-D-005", "cusp metric measured its own sampling density; "
         "arc-length weighting fixed it (10.576x, finite)",
         "docs/v4/V4X_DEFECT_REGISTER.md"),
        ("EYE-CARD-v4", "v4.1 and v4.2.1 Eye coordinates are two "
         "resolution-dependent estimates of ONE apex feature",
         "docs/v4/EYE_CLAIM_CARD.md"),
        ("V4X-D-004", "681-vs-682 test-count drift; counts now derive "
         "from a real run and are guard-verified",
         "docs/v4/V4X_DEFECT_REGISTER.md"),
    ]
    for cid, stmt, prov in corr:
        store.add("corrections", Record(
            id=cid, kind="correction",
            evidence_class="DERIVED_ARITHMETIC",
            provenance=prov, fields={"statement": stmt}))


def _cspc(store: CanonicalStore) -> None:
    """v4.6 Crystalline Spacetime Coordinate Program (A32).

    Reads the canonical CSCP modules — never a spreadsheet — so the
    workbook shows the same numbers the tests verify. Every row is
    DERIVED_ARITHMETIC, ANALYTIC_MODEL, SOURCE_CLAIM or UNSUPPORTED;
    nothing here is a measurement.
    """
    from cspc.exact import registry as cspc_registry
    from cspc.experiments import compile_experiments, water_2g45_correction
    from cspc.provenance import CORRECTIONS as CSPC_CORRECTIONS
    from cspc.spacetime import TRAVEL_CLAIMS, energy_audit
    from cspc.tetra import ambiguity_report, build_all, sync_summary

    # frequency candidates with the exact/supported precision split
    for cid, c in cspc_registry().items():
        audit = c.quantity.precision_audit(c.unit)
        store.add("cspc_candidates", Record(
            id=cid, kind="cspc_candidate",
            evidence_class="DERIVED_ARITHMETIC",
            provenance=c.derivation,
            fields={"exact_value": audit["exact"],
                    "unit": c.unit,
                    "physically_supported_value": audit["supported"],
                    "significant_figures": audit["sig_figs"] or "exact",
                    "overclaims_if_quoted_exactly":
                        audit["overclaims_if_quoted_exactly"],
                    "status": c.status, "note": c.note}))

    # the 64-tetrahedron readings and their spectra
    amb = ambiguity_report()
    store.add("cspc_tetrahedron", Record(
        id="TETRA-AMBIGUITY", kind="ambiguity",
        evidence_class="SOURCE_CLAIM",
        provenance="cspc.tetra.ambiguity_report",
        fields={"source_phrase": amb["source_phrase"],
                "status": amb["status"],
                "n_readings": amb["n_readings"],
                "resolution": amb["resolution"]}))
    for name, cx in build_all().items():
        s = sync_summary(cx)
        store.add("cspc_tetrahedron", Record(
            id=f"TETRA-{name}", kind="complex",
            evidence_class="DERIVED_ARITHMETIC",
            provenance=f"cspc.tetra reading={cx.reading}",
            fields={"vertices": s["n_vertices"], "edges": s["n_edges"],
                    "tetrahedral_cells": s["n_cells"],
                    "algebraic_connectivity":
                        round(s["algebraic_connectivity"], 6),
                    "note": cx.note}))

    # spacetime audit
    a = energy_audit(100.0, 3600.0)
    store.add("cspc_spacetime", Record(
        id="ENERGY-AUDIT-100W-1H", kind="energy_audit",
        evidence_class="ANALYTIC_MODEL",
        provenance="cspc.spacetime.energy_audit",
        fields={"apparatus": "100 W for 3600 s",
                "energy_j": a["energy_j"],
                "equivalent_mass_kg": a["equivalent_mass_kg"],
                "schwarzschild_radius_m": a["schwarzschild_radius_m"],
                "orders_of_magnitude_below_proton":
                    round(a["orders_of_magnitude_below_proton"], 1),
                "verdict": a["verdict"]}))
    for t in TRAVEL_CLAIMS:
        store.add("cspc_spacetime", Record(
            id=t.id, kind="travel_claim",
            evidence_class="UNSUPPORTED",
            provenance="cspc.spacetime.TRAVEL_CLAIMS",
            fields={"claim": t.claim, "status": t.status,
                    "required_evidence": t.required_evidence,
                    "why_unsupported":
                        t.why_current_work_does_not_support_it}))

    # preregistered experiments (plans only)
    for eid, plan in compile_experiments()["experiments"].items():
        store.add("cspc_experiments", Record(
            id=eid, kind="preregistration",
            evidence_class="ANALYTIC_MODEL",
            provenance="cspc.experiments",
            fields={"question": plan["question"],
                    "n_controls": len(plan["control_hz"]),
                    "n_per_condition": plan["n_per_condition"],
                    "blinding": plan["blinding"],
                    "stopping_rule": plan["stopping_rule"],
                    "apparatus_status": plan["apparatus_status"],
                    "data_status": plan["data_status"]}))

    # CSCP corrections join the existing correction ledger
    for c in CSPC_CORRECTIONS:
        store.add("corrections", Record(
            id=c.id, kind="correction",
            evidence_class="DERIVED_ARITHMETIC",
            provenance=c.basis,
            fields={"statement": f"{c.subject}: {c.correction}"}))
    w = water_2g45_correction()
    store.add("corrections", Record(
        id="CSPC-CORR-001-QUANT", kind="correction",
        evidence_class="ANALYTIC_MODEL",
        provenance="cspc.experiments.water_2g45_correction",
        fields={"statement":
                f"Debye loss peak {w['debye_loss_peak_ghz']:.1f} GHz; "
                f"2.45 GHz carries "
                f"{w['loss_at_2g45_relative_to_peak'] * 100:.0f}% of "
                f"peak loss and is not a resonance."}))


def _pmwr(store: CanonicalStore) -> None:
    """v4.7 Phase Memory / Worldline Recovery / Phryll lane (A71).

    Reads the canonical pmwr modules. Every row is arithmetic, an
    analytic model, or a plan; the Phryll rows carry ladder states
    with no DETECTED state anywhere.
    """
    from pmwr import FIREWALLS
    from pmwr.benches import compile_benches
    from pmwr.crystal import pyramid_ratio_audit
    from pmwr.ingest import (NOVELTY_BOUNDARY, OPERATOR_NOTE_STATUS,
                             operator_note_fingerprint)
    from pmwr.recovery import closure_delay_ambiguity, dual_lattice_probe
    from pmwr.worldline import two_geodesic_case

    c = closure_delay_ambiguity(["4096", "20480", "40960"], 1.0)
    store.add("pmwr_recovery", Record(
        id="PMWR-CLOSURE-ALIAS", kind="ambiguity",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="pmwr.recovery.closure_delay_ambiguity",
        fields={"closure_window_s": c["closure_window_s"],
                "aliases_per_second": c["aliases_within_max_delay"],
                "statement": c["statement"]}))
    d = dual_lattice_probe(["4096", "20480"], ["4375"])
    store.add("pmwr_recovery", Record(
        id="PMWR-DUAL-LATTICE", kind="probe_design",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="pmwr.recovery.dual_lattice_probe",
        fields={"window_a_s": d["window_a_s"],
                "window_b_s": d["window_b_s"],
                "combined_range_s": d["combined_unambiguous_range_s"],
                "improvement": d["improvement_over_a"]}))
    t = two_geodesic_case()
    store.add("pmwr_recovery", Record(
        id="PMWR-TWO-GEODESIC", kind="worldline_channel",
        evidence_class="ANALYTIC_MODEL",
        provenance="pmwr.worldline.two_geodesic_case",
        fields={"differential_rate": t["differential_rate"],
                "phase_cycles_per_day":
                    t["differential_phase_cycles_per_day"],
                "interpretation": t["not_an_interpretation"]}))

    audit = pyramid_ratio_audit()
    for label, row in audit["angles"].items():
        store.add("pmwr_crystal", Record(
            id=f"ANGLE-{label}", kind="geometry_candidate",
            evidence_class="GEOMETRY_IDENTITY",
            provenance="pmwr.crystal.pyramid_ratio_audit",
            fields={"theta_deg": row["theta_deg"],
                    "h_over_half_base": round(row["h_over_half_base"], 12),
                    "full_base_over_height":
                        round(row["full_base_over_height"], 12),
                    "abs_diff_from_pi_over_2":
                        round(row["abs_diff_from_pi_over_2"], 9),
                    "mechanism_claim": "REFUSED"}))

    store.add("pmwr_phryll", Record(
        id="PHRYLL-OPERATIONALIZATION", kind="latent_definition",
        evidence_class="SOURCE_CLAIM",
        provenance="pack core/06; pmwr.crystal.PROMOTION_GATES",
        fields={"ladder": " -> ".join(
                    ("SOURCE_CLAIM", "OPERATIONAL_HYPOTHESIS",
                     "UNEXPLAINED_INSTRUMENT_RESIDUAL",
                     "REPLICATED_ANOMALY", "CANDIDATE_NEW_MECHANISM")),
                "detected_state_exists": False,
                "operator_note_sha256": operator_note_fingerprint(),
                "note_status": ",".join(OPERATOR_NOTE_STATUS)}))
    for key, why in FIREWALLS.items():
        store.add("pmwr_phryll", Record(
            id=f"FIREWALL-{key}", kind="firewall",
            evidence_class="DERIVED_ARITHMETIC",
            provenance="pmwr.FIREWALLS",
            fields={"refusal": why}))
    b = compile_benches()
    for bid, plan in b["benches"].items():
        store.add("pmwr_phryll", Record(
            id=bid, kind="bench_preregistration",
            evidence_class="ANALYTIC_MODEL",
            provenance="pmwr.benches",
            fields={"question": plan["question"],
                    "apparatus_status": plan["apparatus_status"],
                    "data_status": plan["data_status"]}))
    store.add("pmwr_recovery", Record(
        id="PMWR-NOVELTY", kind="novelty_boundary",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="pmwr.ingest.NOVELTY_BOUNDARY",
        fields={"textbook_not_novel":
                    "; ".join(NOVELTY_BOUNDARY["textbook_not_novel"]),
                "programme_specific":
                    "; ".join(NOVELTY_BOUNDARY["programme_specific"])}))


def _sources(store: CanonicalStore) -> None:
    from sources.registry.v4x2_source_registry import SOURCES
    for sid, s in SOURCES.items():
        store.add("source_registry", Record(
            id=sid, kind="source",
            evidence_class="SOURCE_CLAIM",
            provenance=f"local hash {s['sha256_prefix']}",
            fields={"title": s["title"], "doi": s["doi"],
                    "system": s["system"],
                    "publication_state": s["publication_state"],
                    "forbidden_transfers":
                        "; ".join(s["forbidden_transfers"])}))


def _lore(store: CanonicalStore) -> None:
    # PUBLIC_SAFE lore only: the mechanism/policy, never private
    # content. Private lore lives local-only (L01) and is never
    # exported to a public workbook.
    store.add("lore_registry", Record(
        id="LORE-POLICY", kind="lore_policy",
        evidence_class="LORE", privacy_class="PUBLIC_SAFE",
        provenance="docs/v4/resonator/LORE_AND_INTUITION_POLICY.md",
        fields={"statement": "private lore is preserved local-only "
                             "with consent control; observation is "
                             "separated from interpretation; nothing "
                             "in the lore lane is evidence",
                "note": "public workbooks exclude private rows"}))


def _release_meta(store: CanonicalStore) -> None:
    store.add("installer_metadata", Record(
        id="REL-v4.5.0", kind="release_metadata",
        evidence_class="DERIVED_ARITHMETIC",
        provenance="pyproject.toml + build",
        fields={"product": "RGCS Workbench",
                "install_scope": "per-user (%LOCALAPPDATA%)",
                "signed": False,
                "telemetry": False,
                "network": "loopback only, no auto-start",
                "claim_boundary": "SOFTWARE only; no physical crystal "
                                  "resonance, Eye, or anomalous "
                                  "channel is validated"}))


def build(version: str = "4.5.0") -> CanonicalStore:
    """Deterministic population from the live repository."""
    store = CanonicalStore()
    _frequency_keys(store)
    _relations(store)
    _specimens(store)
    _timing_recipes(store)
    _hypotheses(store)
    _eye(store)
    _resonator(store)
    _hardware(store)
    _experiments(store)
    _corrections(store)
    _cspc(store)
    _pmwr(store)
    _sources(store)
    _lore(store)
    _release_meta(store)
    # stamp the version on the release row
    for r in store.tables.get("installer_metadata", []):
        r.fields["version"] = version
    return store
