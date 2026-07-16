"""Registered material and reference-system records (Agent M2).

Alpha quartz keeps exactly its v4.0.0 validated capabilities and is
mechanically barred from every magnetic/quantum-material mechanism
(exclusion matrix, M1). Reference systems are `reference_only=True`
and can never be mistaken for quartz (fixture validator in tests)."""

from __future__ import annotations

from .capabilities import (CAPABILITY_KEYS, CapabilityRecord,
                           MaterialCapabilities)

_U = CapabilityRecord            # UNSUPPORTED default


def _caps(**overrides) -> dict:
    """All 24 keys default UNSUPPORTED; override the supported ones."""
    base = {k: _U(reason=f"no registered {k} capability")
            for k in CAPABILITY_KEYS}
    base.update(overrides)
    return base


def _sup(classification="CORE_VALIDATED", sources=(), psets=(),
         reason=None, **kw) -> CapabilityRecord:
    return CapabilityRecord("SUPPORTED", classification,
                            tuple(psets), tuple(sources),
                            reason=reason, **kw)


def _ref(classification="REDUCED_ORDER_VALIDATED", sources=(),
         reason=None) -> CapabilityRecord:
    return CapabilityRecord("REFERENCE_ONLY", classification,
                            source_ids=tuple(sources), reason=reason)


_QUARTZ_BAN = ("frozen boundary 6: alpha quartz may not acquire this "
               "mechanism without a quartz-specific registered source "
               "and implementation")

ALPHA_QUARTZ = MaterialCapabilities(
    material_id="material.alpha_quartz",
    display_name="alpha quartz (canonical RGCS application)",
    material_family="piezoelectric trigonal crystal (class 32)",
    reference_only=False,
    source_ids=("SRC-V4-00",),
    symmetry="trigonal 32 (P3121/P3221 enantiomorphs)",
    coordinate_frame="crystal C-axis = body +Z (v4.0.0 authority)",
    temperature_range={"kelvin": [0, 846],
                       "note": "alpha phase below ~846 K"},
    notes=("v4.0.0 CORE_VALIDATED stack: fem/quartz/piezo/"
           "projections/eye",),
    capabilities=_caps(
        elasticity_isotropic=_sup(reason="benchmark path"),
        elasticity_anisotropic=_sup(sources=("SRC-V4-00",)),
        piezoelectric=_sup(sources=("SRC-V4-00",)),
        dielectric_anisotropic=_sup(),
        photoelastic=_sup(),
        optical_birefringent=_sup(),
        nonlinear_optical=CapabilityRecord(
            "INTERFACE_ONLY", "INTERFACE_ONLY",
            reason="declared, not implemented for quartz in v4"),
        spin_orbit_coupling=_U(reason=_QUARTZ_BAN),
        magnetic_order=_U(reason=_QUARTZ_BAN),
        magnon_modes=_U(reason=_QUARTZ_BAN),
        exciton_frenkel=_U(reason=_QUARTZ_BAN),
        exciton_wannier=_U(reason=_QUARTZ_BAN),
        exciton_charge_transfer=_U(reason=_QUARTZ_BAN),
        exciton_magnon_coupling=_U(reason=_QUARTZ_BAN),
        spin_phonon_coupling=_U(reason=_QUARTZ_BAN),
        chiral_phonons=_U(reason=_QUARTZ_BAN + " (no registered "
                          "quartz g-factor)"),
        magnetoelectric_dynamic=_U(reason=_QUARTZ_BAN),
        plasmonic_near_field=_U(reason=_QUARTZ_BAN),
        quantum_statistical_response=_U(reason=_QUARTZ_BAN),
        microscopic_tunnelling_model=_U(reason=_QUARTZ_BAN),
        ferrotoroidic_order=_U(reason=_QUARTZ_BAN),
        directional_optical_response=_U(reason=_QUARTZ_BAN),
        domain_writing=_U(reason=_QUARTZ_BAN),
        thermal_domain_selection=_U(reason=_QUARTZ_BAN),
    ))


def _mechanical_reference(mid, name, extra_notes=()):
    return MaterialCapabilities(
        material_id=mid, display_name=name,
        material_family="isotropic elastic reference",
        reference_only=True, source_ids=("SRC-V4-00",),
        symmetry="isotropic", coordinate_frame="cartesian body frame",
        temperature_range={"kelvin": [0, 1000]},
        notes=tuple(extra_notes) or (
            "validated mechanical reference (v4.0.0)",),
        capabilities=_caps(
            elasticity_isotropic=_sup(),
        ))


ISOTROPIC_BENCHMARK = _mechanical_reference(
    "reference.isotropic_benchmark", "generic isotropic elastic block")
CANTILEVER = _mechanical_reference(
    "reference.cantilever", "cantilever beam (EB/Timoshenko anchors)")
TUNING_FORK = _mechanical_reference(
    "reference.tuning_fork", "tuning fork (weak-coupling pair, V.9)")
ACOUSTIC_CAVITY = MaterialCapabilities(
    material_id="reference.acoustic_cavity",
    display_name="rigid-wall acoustic cavity (exact Helmholtz)",
    material_family="acoustic reference", reference_only=True,
    source_ids=("SRC-V4-00",), symmetry="rectangular",
    coordinate_frame="cartesian", temperature_range={"kelvin": [200, 400]},
    capabilities=_caps())

OPTICAL_VORTEX_FIELD = MaterialCapabilities(
    material_id="reference.optical_vortex_field",
    display_name="optical vortex beam (known topological charge)",
    material_family="free-space optical field reference",
    reference_only=True, source_ids=("SRC-V4-00", "SRC-V4-14"),
    symmetry="paraxial beam", coordinate_frame="beam frame (z = k)",
    temperature_range={},
    capabilities=_caps(
        optical_birefringent=_U(reason="free-space field"),
    ))

CHIRAL_PHONON_REF = MaterialCapabilities(
    material_id="reference.chiral_phonon",
    display_name="chiral two-mode phonon reference",
    material_family="degenerate two-mode lattice reference",
    reference_only=True, source_ids=("SRC-V4-13",),
    symmetry="C3-like degenerate pair",
    coordinate_frame="mode plane (qx, qy)", temperature_range={},
    capabilities=_caps(
        chiral_phonons=_ref(sources=("SRC-V4-13",)),
        spin_phonon_coupling=CapabilityRecord(
            "INTERFACE_ONLY", "INTERFACE_ONLY",
            reason="Zeeman splitting interface; g_eff must be "
                   "material-supplied"),
    ))

EXCITON_MAGNON_REF = MaterialCapabilities(
    material_id="reference.exciton_magnon",
    display_name="exciton-magnon modulation reference (vdW-magnet-like)",
    material_family="reduced-order magnetic reference",
    reference_only=True, source_ids=("SRC-V4-06",),
    symmetry="uniaxial AFM (declared)", coordinate_frame="spin frame",
    temperature_range={"kelvin": [0, 150]},
    capabilities=_caps(
        magnetic_order=_ref(sources=("SRC-V4-06",)),
        magnon_modes=_ref(sources=("SRC-V4-06",)),
        exciton_frenkel=_ref(sources=("SRC-V4-06",)),
        exciton_magnon_coupling=_ref(sources=("SRC-V4-06",)),
    ))

SOE_PHONON_REF = MaterialCapabilities(
    material_id="reference.soe_phonon",
    display_name="spin-orbit-exciton / phonon avoided-crossing reference",
    material_family="reduced-order coupled-mode reference",
    reference_only=True, source_ids=("SRC-V4-13",),
    symmetry="two/three coupled modes", coordinate_frame="mode space",
    temperature_range={"kelvin": [0, 300]},
    capabilities=_caps(
        exciton_frenkel=_ref(sources=("SRC-V4-13",)),
        spin_orbit_coupling=_ref(sources=("SRC-V4-13",)),
        spin_phonon_coupling=_ref(sources=("SRC-V4-13",)),
    ))

DYNAMIC_ME_REF = MaterialCapabilities(
    material_id="reference.dynamic_magnetoelectric",
    display_name="dynamical magnetoelectric oscillator reference",
    material_family="reduced-order multiferroic reference",
    reference_only=True, source_ids=("SRC-V4-12",),
    symmetry="declared per tensor fixture",
    coordinate_frame="tensor frame (declared)",
    temperature_range={"kelvin": [0, 300]},
    capabilities=_caps(
        magnetic_order=_ref(sources=("SRC-V4-12",)),
        magnetoelectric_dynamic=_ref(sources=("SRC-V4-12",)),
    ))

METACRYSTAL_REF = MaterialCapabilities(
    material_id="reference.metacrystal",
    display_name="quantum-statistical plasmonic metacrystal reference",
    material_family="statistical optical reference (NOT bulk quartz)",
    reference_only=True, source_ids=("SRC-V4-09",),
    symmetry="meta-atom arrangement (declared)",
    coordinate_frame="array frame", temperature_range={},
    capabilities=_caps(
        plasmonic_near_field=CapabilityRecord(
            "INTERFACE_ONLY", "INTERFACE_ONLY",
            reason="no microscopic plasmonic solver"),
        quantum_statistical_response=_ref(sources=("SRC-V4-09",)),
    ))

LINIPO4_REF = MaterialCapabilities(
    material_id="reference.linipo4",
    display_name="LiNiPO4 ferrotoroidic IOME reference",
    material_family="orthorhombic AFM/ferrotoroidic reference",
    reference_only=True, source_ids=("SRC-V4-01",),
    symmetry="Pnma; toroidal axis || b (declared phase)",
    coordinate_frame="orthorhombic abc",
    temperature_range={"kelvin": [0, 21],
                       "note": "AFM/toroidal phase below ~20.8 K "
                               "(registered transition)"},
    capabilities=_caps(
        magnetic_order=_ref(sources=("SRC-V4-01",)),
        ferrotoroidic_order=_ref(sources=("SRC-V4-01",)),
        magnetoelectric_dynamic=_ref(sources=("SRC-V4-01",)),
        directional_optical_response=_ref(sources=("SRC-V4-01",)),
        domain_writing=_ref(sources=("SRC-V4-01",)),
        thermal_domain_selection=_ref(sources=("SRC-V4-01",)),
    ))

MNF2_REF = MaterialCapabilities(
    material_id="reference.mnf2",
    display_name="MnF2 optical-annealing null/comparator reference",
    material_family="rutile AFM comparator",
    reference_only=True, source_ids=("SRC-V4-05",),
    symmetry="tetragonal rutile", coordinate_frame="tetragonal axes",
    temperature_range={"kelvin": [0, 68],
                       "note": "T_N ~ 67-68 K (registered)"},
    capabilities=_caps(
        magnetic_order=_ref(sources=("SRC-V4-05",)),
        thermal_domain_selection=_ref(sources=("SRC-V4-05",)),
        # deliberately NOT directional_optical_response: MnF2 is the
        # polarization/thermal comparator, not an IOME material
    ))

NONLINEAR_AFM_REF = MaterialCapabilities(
    material_id="reference.nonlinear_afm",
    display_name="nonlinear antiferromagnetic switching reference (TmFeO3-like)",
    material_family="orthoferrite reference",
    reference_only=True, source_ids=("SRC-V4-03",),
    symmetry="orthorhombic", coordinate_frame="spin/easy-axis frame",
    temperature_range={"kelvin": [0, 90]},
    capabilities=_caps(
        magnetic_order=_ref(sources=("SRC-V4-03",)),
        magnon_modes=_ref(sources=("SRC-V4-03",)),
    ))

PHONON_EXCHANGE_REF = MaterialCapabilities(
    material_id="reference.phonon_exchange",
    display_name="phonon-controlled exchange reference (DyFeO3-like)",
    material_family="light-driven-phonon reference",
    reference_only=True, source_ids=("SRC-V4-04",),
    symmetry="orthorhombic", coordinate_frame="spin/phonon frame",
    temperature_range={"kelvin": [0, 100]},
    capabilities=_caps(
        magnetic_order=_ref(sources=("SRC-V4-04",)),
        spin_phonon_coupling=_ref(sources=("SRC-V4-04",)),
    ))

FDT_ADAPTER = MaterialCapabilities(
    material_id="source_hypothesis.fdt_adapter",
    display_name="FDT external-theory adapter (QUARANTINED)",
    material_family="source hypothesis (not a material)",
    reference_only=True, source_ids=("SRC-V4-18",),
    symmetry="n/a", coordinate_frame="n/a", temperature_range={},
    notes=("every capability ceiling is SOURCE_HYPOTHESIS; the "
           "adapter can never enter default solvers",),
    capabilities=_caps(**{
        k: CapabilityRecord("INTERFACE_ONLY", "SOURCE_HYPOTHESIS",
                            source_ids=("SRC-V4-18",),
                            reason="quarantined FDT mapping")
        for k in ("directional_optical_response", "domain_writing")}))

MATERIALS: dict[str, MaterialCapabilities] = {
    m.material_id: m for m in (
        ALPHA_QUARTZ, ISOTROPIC_BENCHMARK, CANTILEVER, TUNING_FORK,
        ACOUSTIC_CAVITY, OPTICAL_VORTEX_FIELD, CHIRAL_PHONON_REF,
        EXCITON_MAGNON_REF, SOE_PHONON_REF, DYNAMIC_ME_REF,
        METACRYSTAL_REF, LINIPO4_REF, MNF2_REF, NONLINEAR_AFM_REF,
        PHONON_EXCHANGE_REF, FDT_ADAPTER)}


def get_material(material_id: str) -> MaterialCapabilities:
    """Lookup with alias rejection: a reference system cannot be
    reached through a quartz-flavored alias (fixture validator)."""
    if material_id not in MATERIALS:
        raise KeyError(
            f"unregistered material '{material_id}' — aliases and toy "
            "fixtures may not inherit another material's identity")
    return MATERIALS[material_id]


def capability_matrix_markdown() -> str:
    """Generated public capability matrix (gate C5)."""
    lines = ["# V4 Material Capability Matrix (generated)", "",
             "Statuses: S=SUPPORTED R=REFERENCE_ONLY I=INTERFACE_ONLY"
             " ·=UNSUPPORTED", ""]
    short = {"SUPPORTED": "S", "REFERENCE_ONLY": "R",
             "INTERFACE_ONLY": "I", "UNSUPPORTED": "·",
             "UNKNOWN": "?"}
    header = "| capability | " + " | ".join(
        m.material_id.split(".")[-1] for m in MATERIALS.values()) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(MATERIALS) + 1))
    for k in CAPABILITY_KEYS:
        row = [k]
        for m in MATERIALS.values():
            row.append(short[m.capability(k).status])
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    for m in MATERIALS.values():
        lines.append(f"## {m.material_id} — what is not supported")
        lines.append(", ".join(m.what_is_not_supported()) or "(none)")
        lines.append("")
    return "\n".join(lines)
