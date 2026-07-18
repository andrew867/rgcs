"""A03 — exact arithmetic and frozen constant fixtures.

Every candidate frequency in the v4.6 register is derived here from
integers and exact powers, never from binary floats, and checked
against a frozen decimal fixture. If a derivation ever stops
reproducing its fixture the test suite fails — the register cannot
drift silently.

Precision policy (transfer firewall 8), applied per-derivation:

- The **2.45 GHz fold family** descends from a *nominal* 2.45 GHz
  (three significant figures). ``2.45e9 / 8**9`` is exactly
  ``18.25392246246337890625`` Hz as arithmetic, and is
  ``18.3`` Hz as physics. Both are recorded; only the latter may
  appear in a physical statement.
- The **optical candidate** descends from ``4096 x 2**37 = 2**49``,
  exact integers, and the SI-defined speed of light. Its long decimal
  expansion is exact by definition, not an empirical overclaim.

None of these values is evidence that any specimen prefers any
frequency. Status labels come from the pack register: DERIVED_ARITHMETIC
(pure arithmetic), REGISTERED_CANDIDATE / REGISTERED_TARGET (things the
programme may later test), SOURCE_CLAIM (preserved source assertion),
CONTROL (deliberate neighbour controls).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .units import C_VACUUM, Quantity, exact

#: Nominal source figure. Three significant figures — this is the
#: single most important precision fact in the programme.
NOMINAL_2_45_GHZ_SIG_FIGS = 3

SOURCE_2_45_GHZ = Quantity.of(
    "2450000000", "Hz", NOMINAL_2_45_GHZ_SIG_FIGS,
    provenance="SRC-JH-DAN-2024-FRACTAL-4096-001: '2.45 GHz is "
               "described as the frequency of water' (nominal)",
    evidence_class="SOURCE_CLAIM")

#: 4096 Hz: an exact integer as arithmetic; a candidate, not a measurement.
F_4096 = Quantity.of(4096, "Hz", None,
                     provenance="source/derived master candidate",
                     evidence_class="DERIVED_ARITHMETIC")


@dataclass(frozen=True)
class Candidate:
    id: str
    quantity: Quantity
    derivation: str
    status: str
    fixture: str          # frozen exact decimal, in `unit`
    unit: str = "Hz"
    note: str = ""

    @property
    def exact_hz(self) -> Fraction:
        return self.quantity.in_unit(self.unit)

    def verify(self) -> bool:
        return self.exact_hz == exact(self.fixture)

    def physical_str(self) -> str:
        """The value as it may be quoted in a physical statement."""
        return self.quantity.significant_str(self.unit)


def _fold(n: int, fixture: str, status: str, note: str = "") -> Candidate:
    """2.45 GHz / 8**n — inherits the nominal input's 3 s.f."""
    q = SOURCE_2_45_GHZ / Quantity.of(8 ** n, "", None)
    return Candidate(f"FKEY-CSPC-FOLD-{n}", q, f"2.45e9 / 8^{n}",
                     status, fixture, "Hz", note)


# --- the register --------------------------------------------------------

#: 36-bit DDS least-significant bit: 2.45 GHz / 2**36.
DDS_36BIT_LSB = Candidate(
    "FKEY-CSPC-DELTA",
    SOURCE_2_45_GHZ / Quantity.of(2 ** 36, "", None),
    "2.45e9 / 2^36", "DERIVED_ARITHMETIC",
    "0.03565219230949878692626953125", "Hz",
    "abstract 36-bit DDS LSB; period 536870912/19140625 s "
    "(~28.0487660147 s)")

FOLDS = {
    5: _fold(5, "74768.06640625", "REGISTERED_CANDIDATE"),
    6: _fold(6, "9346.00830078125", "REGISTERED_CANDIDATE"),
    7: _fold(7, "1168.25103759765625", "REGISTERED_CANDIDATE"),
    8: _fold(8, "146.03137969970703125", "REGISTERED_CANDIDATE"),
    9: _fold(9, "18.25392246246337890625", "REGISTERED_CANDIDATE",
             "primary low-frequency fold candidate"),
    10: _fold(10, "2.28174030780792236328125", "REGISTERED_CANDIDATE"),
    11: _fold(11, "0.28521753847599029541015625",
              "REGISTERED_CANDIDATE"),
}

#: Optical candidate: 4096 * 2**37 == 2**49 Hz, exact integers.
OPTICAL_HZ = Candidate(
    "FKEY-CSPC-OPT",
    Quantity.of(2 ** 49, "Hz", None,
                provenance="4096 * 2^37 = 2^49 (exact integers)"),
    "4096 * 2^37 = 2^49", "DERIVED_ARITHMETIC",
    "562949953421312", "Hz",
    "exact integer arithmetic; NOT evidence of optical coupling")

#: Vacuum wavelength of the optical candidate: c / f, both exact.
OPTICAL_WAVELENGTH = Candidate(
    "FKEY-CSPC-OPT-LAMBDA",
    C_VACUUM / Quantity.of(2 ** 49, "Hz", None),
    "c / (4096 * 2^37), c exact by SI definition",
    "DERIVED_ARITHMETIC",
    "532.538383168912332621403038501739501953125", "nm",
    "exact by definition; the pack quotes it as 532.5383831689123 nm")

#: Binary / harmonic family (exact integers).
INTEGER_KEYS = {
    "FKEY-4096": Candidate("FKEY-4096", F_4096, "source/derived master",
                           "REGISTERED_CANDIDATE", "4096"),
    "FKEY-20480": Candidate(
        "FKEY-20480", F_4096 * 5, "4096 * 5", "REGISTERED_TARGET",
        "20480", "Hz",
        "exact fifth harmonic IF the drive waveform contains one; a "
        "pure sine does not"),
    "FKEY-32768": Candidate(
        "FKEY-32768", Quantity.of(32768, "Hz", None), "2^15",
        "REGISTERED_CANDIDATE", "32768", "Hz",
        "standard quartz clock crystal, for comparison"),
    "FKEY-40960": Candidate(
        "FKEY-40960", F_4096 * 10, "20480 * 2", "REGISTERED_TARGET",
        "40960"),
    "FKEY-20_48": Candidate(
        "FKEY-20_48", F_4096 / Quantity.of(200, "", None), "4096 / 200",
        "REGISTERED_CANDIDATE", "20.48"),
    "FKEY-40_96": Candidate(
        "FKEY-40_96", F_4096 / Quantity.of(100, "", None), "4096 / 100",
        "REGISTERED_CANDIDATE", "40.96"),
    "FKEY-8HZ": Candidate(
        "FKEY-8HZ", Quantity.of(8, "Hz", None), "historical/base",
        "REGISTERED_CANDIDATE", "8"),
}

#: Neighbour controls required for any low-frequency experiment
#: (core/07 mandates 18.0, 18.5, 19.8, 20.0, 20.48 and 21.0 Hz
#: alongside the 18.2539... candidate). Controls are first-class: an
#: effect that also appears here is not specific to the candidate.
CONTROLS_HZ = ("18.0", "18.5", "19.8", "20.0", "20.48", "21.0")


def registry() -> dict:
    """Full v4.6 candidate register, keyed by id."""
    out: dict[str, Candidate] = {DDS_36BIT_LSB.id: DDS_36BIT_LSB}
    out.update({c.id: c for c in FOLDS.values()})
    out[OPTICAL_HZ.id] = OPTICAL_HZ
    out[OPTICAL_WAVELENGTH.id] = OPTICAL_WAVELENGTH
    out.update(INTEGER_KEYS)
    return out


def verify_all() -> dict:
    """Check every derivation against its frozen fixture."""
    reg = registry()
    failures = [cid for cid, c in reg.items() if not c.verify()]
    return {"checked": len(reg), "failures": failures,
            "ok": not failures}


def dds_period_s() -> Fraction:
    """Exact period of the 36-bit LSB tone, in seconds."""
    return 1 / DDS_36BIT_LSB.exact_hz


def common_532nm_offset() -> dict:
    """How far a common 532.0 nm laser sits from the exact candidate.

    A stock green laser is NOT the candidate; quoting it as such would
    be a 0.1% substitution.
    """
    f_532 = C_VACUUM / Quantity.of("532", "nm", None)
    f_cand = OPTICAL_HZ.exact_hz
    rel = (f_532.in_unit("Hz") - f_cand) / f_cand
    return {"candidate_hz": f_cand,
            "common_laser_hz": f_532.in_unit("Hz"),
            "relative_offset": rel,
            "percent": float(rel) * 100,
            "note": "a common 532.0 nm source is ~0.1012% higher in "
                    "frequency; it must be labelled as a near-neighbour, "
                    "never as the candidate"}
