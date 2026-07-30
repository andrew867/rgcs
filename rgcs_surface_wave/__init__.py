"""RGCS R10.15 — phase-gated dielectric-loaded annular surface-wave
research model.

WHAT THIS IS. A public, evidence-governed research package for a
*candidate* device architecture: a conducting annulus carrying an
engineered (patterned) surface with 35 angular cells, 33 of them
active, loaded by a dielectric slab, driven by a phase-gated
time-modulated excitation. The package computes mask spectra, reduced
surface-impedance dispersion, annular eigenmodes, Floquet sidebands,
Maxwell-stress forces on closed surfaces, and momentum/energy closure.

WHAT THIS IS NOT. No result here is a measurement, and nothing here
supports antigravity, reactionless thrust, gravity modification, free
energy, anomalous propulsion, or extraterrestrial manufacture. A
computed Maxwell-stress value is not a measured force. Every solver
labels its evidence class and refuses operations that would let an
approximation masquerade as a result -- notably, a static field
solution may never be used to claim a force from a time-modulated
system, and a net force is never reported without a closed-surface
momentum balance.

Publication status: HOLD.
"""

__version__ = "0.10.15"
PUBLICATION_STATUS = "HOLD"

#: The single sentence every public artifact carries.
NONCLAIM = ("Computed values are simulation outputs, not measurements. "
            "This work does not demonstrate antigravity, reactionless "
            "thrust, gravity modification, free energy, or anomalous "
            "propulsion, and makes no claim about the origin or "
            "authorship of the source material.")

#: Language the evidence policy forbids in public claim text.
FORBIDDEN_CLAIM_TERMS = (
    "antigravity", "anti-gravity", "gravity control", "reactionless",
    "free energy", "over-unity", "overunity", "warp drive",
    "validated alien technology", "proven crop-circle blueprint",
    "phryll measured", "anomalous propulsion",
)
