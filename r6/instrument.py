"""P05 — the instrument matrix and the Phryll residual boundary.

Phryll remains undefined (core/07). The only defensible thing R6 can do
with it is to make the *absence* of a Phryll instrument explicit, bound
every ordinary channel that a real instrument can reach, and then treat
whatever is left over as a measurement that is not yet understood.

Two structural commitments follow from that.

First, the instrument matrix. All eighteen channels in
:data:`r6.ORDINARY_CHANNELS` must have at least one declared instrument
before a residual may be registered at all. A residual is by definition
"what the instruments did not account for", so an incomplete instrument
set does not produce a small residual — it produces a meaningless one.
:func:`coverage_report` is the gate.

Second, the ladder. Promotion runs

    SOURCE_CLAIM
    OPERATIONAL_HYPOTHESIS
    ORDINARY_CHANNEL_RESULT
    UNEXPLAINED_INSTRUMENT_RESIDUAL
    REPLICATED_ANOMALY
    CANDIDATE_NEW_MECHANISM

and stops there. There is no state above CANDIDATE_NEW_MECHANISM and
there is no detection state; the names R6 refuses to hold are listed in
:data:`r6.FORBIDDEN_STATES` and adding one is a test failure. A
candidate mechanism is a mechanism someone has proposed and someone
else could falsify — it is not a substance that has been found (r6
FORBIDDEN_COLLAPSES: RESIDUAL_IS_ONTOLOGY).

**Nothing in this module is bench data.** No instrument listed here is
owned, borrowed, quoted or calibrated by the programme. Every range,
resolution and uncertainty is a *catalogue-class* figure: the order of
magnitude a commercially available laboratory instrument of that
description would plausibly deliver, recorded so that the experiment
can be costed and so that a claimed residual can be checked against a
realistic noise floor. Before any of these numbers is used in anger it
must be replaced by the calibration certificate of the actual unit.
No coil has been wound, no drive has been run, no residual observed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace, asdict, field

from . import ORDINARY_CHANNELS, PHRYLL_CLASSES, FORBIDDEN_STATES


class RefusedError(RuntimeError):
    """Raised when an operation is refused rather than approximated.

    Refusals in R6 are first-class returns, not silent failures. If a
    residual cannot honestly be registered, this is raised with a
    message naming exactly what is missing.
    """


# --------------------------------------------------------------------
# Calibration standing
# --------------------------------------------------------------------

#: What kind of calibration an instrument's uncertainty rests on.
CALIBRATION_STATUSES = (
    #: Traceable to a national metrology institute via an unbroken
    #: chain of comparisons with stated uncertainties.
    "CALIBRATED_TRACEABLE",
    #: Calibrated against a traceable in-house reference; adequate for
    #: relative work, weaker for absolute claims.
    "CALIBRATED_IN_HOUSE",
    #: The quantity the device claims to measure has no accepted
    #: standard, so no calibration is possible even in principle.
    "UNCALIBRATED_NO_STANDARD",
)

#: The reference epoch used for the catalogue-class calibration due
#: dates below (Unix seconds, 2027-01-01T00:00:00Z). Fixed and
#: explicit so the records are deterministic rather than dependent on
#: when the module happens to be imported.
CALIBRATION_EPOCH_2027 = 1_798_761_600.0


# --------------------------------------------------------------------
# Instruments
# --------------------------------------------------------------------

@dataclass(frozen=True)
class Instrument:
    """One declared instrument on one declared ordinary channel.

    ``uncertainty`` is an absolute standard uncertainty (k = 1) in
    ``unit``, quoted at the reference condition in ``notes``. It is
    deliberately absolute rather than fractional: a residual is
    compared against a combined uncertainty in physical units, and
    percentages of unstated full scales are how instrument budgets get
    quietly optimistic.

    None of these figures is a measurement of a device the programme
    owns. See the module docstring.
    """

    id: str
    channel: str
    quantity: str
    unit: str
    range_min: float
    range_max: float
    resolution: float
    uncertainty: float
    calibration_id: str
    calibration_due_epoch: float
    calibration_status: str = "CALIBRATED_TRACEABLE"
    notes: str = ""
    provenance: str = "catalogue-class specification, not owned equipment"

    def __post_init__(self) -> None:
        if self.channel not in ORDINARY_CHANNELS:
            raise ValueError(
                f"instrument {self.id}: channel {self.channel!r} is not a "
                f"declared ordinary channel. The eighteen channels are "
                f"{ORDINARY_CHANNELS}. An instrument for an undeclared "
                f"channel is measuring something the programme has not "
                f"defined.")
        if self.calibration_status not in CALIBRATION_STATUSES:
            raise ValueError(
                f"instrument {self.id}: unknown calibration status "
                f"{self.calibration_status!r}")
        if self.calibration_status == "UNCALIBRATED_NO_STANDARD":
            raise ValueError(
                f"instrument {self.id}: a device whose quantity has no "
                f"accepted calibration standard cannot be registered as "
                f"an Instrument on an ordinary channel. Register it with "
                f"UNCALIBRATED_DEVICES instead, where it carries no "
                f"measurement weight.")
        if not self.range_max > self.range_min:
            raise ValueError(
                f"instrument {self.id}: range_max must exceed range_min")
        if self.resolution <= 0:
            raise ValueError(
                f"instrument {self.id}: resolution must be positive")
        if self.uncertainty <= 0:
            raise ValueError(
                f"instrument {self.id}: uncertainty must be positive. An "
                f"instrument with zero uncertainty would make every "
                f"residual significant.")
        if self.uncertainty < self.resolution:
            raise ValueError(
                f"instrument {self.id}: uncertainty {self.uncertainty} is "
                f"below its own resolution {self.resolution}; the display "
                f"cannot be more certain than its least count")

    def as_record(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class UncalibratedDevice:
    """A device with no accepted calibration standard for its quantity.

    This class exists so that "we have nothing that measures this" is
    inspectable data rather than an absence. Such a device has **no
    channel**: it does not appear in :func:`coverage_report`, it cannot
    contribute a :class:`ChannelMeasurement`, and its output can never
    bound anything or raise a residual above the noise floor.
    """

    id: str
    claimed_quantity: str
    reason: str
    calibration_status: str = "UNCALIBRATED_NO_STANDARD"
    provenance: str = "catalogue-class description, not owned equipment"

    def __post_init__(self) -> None:
        if self.calibration_status != "UNCALIBRATED_NO_STANDARD":
            raise ValueError(
                f"{self.id}: UncalibratedDevice exists precisely to hold "
                f"UNCALIBRATED_NO_STANDARD")

    def as_record(self) -> dict:
        return asdict(self)


def _i(*a, **k) -> Instrument:
    return Instrument(*a, **k)


_DUE = CALIBRATION_EPOCH_2027

#: The instrument matrix. Every one of the eighteen ordinary channels
#: has at least one entry. Ranges, resolutions and uncertainties are
#: catalogue-class figures for commercially available laboratory
#: instruments of the stated description — they are NOT measurements of
#: equipment the programme owns, and they are NOT quotations. They are
#: here so the experiment can be costed and so a claimed residual can
#: be checked against a realistic noise floor.
INSTRUMENT_MATRIX: tuple[Instrument, ...] = (

    # 1. drive voltage ------------------------------------------------
    _i(id="INS-V-DMM-01", channel="drive_voltage",
       quantity="DC and low-frequency RMS voltage", unit="V",
       range_min=0.0, range_max=1000.0,
       resolution=1e-5, uncertainty=1e-3,
       calibration_id="CAL-V-DMM-01", calibration_due_epoch=_DUE,
       notes="6.5-digit bench DMM class; uncertainty at 100 V DC, k=1"),
    _i(id="INS-V-DIFFPROBE-01", channel="drive_voltage",
       quantity="differential drive waveform voltage", unit="V",
       range_min=-1400.0, range_max=1400.0,
       resolution=1e-3, uncertainty=2.0,
       calibration_id="CAL-V-DIFFPROBE-01", calibration_due_epoch=_DUE,
       notes="200 MHz high-voltage differential probe class; ~2% of "
             "100 V reading, so it bounds the drive but never resolves "
             "a small residual on it"),

    # 2. drive current ------------------------------------------------
    _i(id="INS-I-SHUNT-01", channel="drive_current",
       quantity="drive current via coaxial shunt", unit="A",
       range_min=-20.0, range_max=20.0,
       resolution=1e-4, uncertainty=5e-3,
       calibration_id="CAL-I-SHUNT-01", calibration_due_epoch=_DUE,
       notes="coaxial current shunt with isolated amplifier, DC-50 MHz"),
    _i(id="INS-I-CT-01", channel="drive_current",
       quantity="wideband AC drive current", unit="A",
       range_min=-5.0, range_max=5.0,
       resolution=1e-4, uncertainty=1e-2,
       calibration_id="CAL-I-CT-01", calibration_due_epoch=_DUE,
       notes="current transformer class, 100 Hz-120 MHz; AC only, so "
             "it cannot see a DC drive offset and must be paired with "
             "the shunt"),

    # 3. impedance and mutual inductance -------------------------------
    _i(id="INS-Z-LCR-01", channel="impedance_and_mutual_inductance",
       quantity="complex impedance, L, C, R, Q", unit="ohm",
       range_min=1e-3, range_max=1e8,
       resolution=1e-3, uncertainty=5e-2,
       calibration_id="CAL-Z-LCR-01", calibration_due_epoch=_DUE,
       notes="precision LCR meter class, 20 Hz-5 MHz, ~0.05% basic "
             "accuracy; measures the copper/silver winding pair and "
             "their mutual inductance versus orientation (claim "
             "R6-C-001)"),
    _i(id="INS-Z-VNA-01", channel="impedance_and_mutual_inductance",
       quantity="S-parameters and derived impedance", unit="ohm",
       range_min=1e-2, range_max=1e6,
       resolution=1e-2, uncertainty=0.5,
       calibration_id="CAL-Z-VNA-01", calibration_due_epoch=_DUE,
       notes="2-port vector network analyser class, 9 kHz-10 GHz. This "
             "is the source's requested E/M/RF coverage to 10 GHz on "
             "the network side; the field probes below cover the "
             "radiated side of the same band"),

    # 4. electric field ------------------------------------------------
    _i(id="INS-E-ISOPROBE-01", channel="electric_field",
       quantity="isotropic RMS electric field strength", unit="V/m",
       range_min=0.5, range_max=800.0,
       resolution=0.1, uncertainty=1.0,
       calibration_id="CAL-E-ISOPROBE-01", calibration_due_epoch=_DUE,
       notes="three-axis isotropic E-field probe class, 100 kHz-10 GHz "
             "(source's requested E/M/RF to 10 GHz, radiated side); "
             "~1 dB absolute, which is why relative sweeps beat "
             "absolute claims"),
    _i(id="INS-E-LFPROBE-01", channel="electric_field",
       quantity="low-frequency electric field strength", unit="V/m",
       range_min=0.01, range_max=1e5,
       resolution=0.01, uncertainty=0.05,
       calibration_id="CAL-E-LFPROBE-01", calibration_due_epoch=_DUE,
       notes="ELF/VLF E-field probe class, 5 Hz-400 kHz, covering the "
             "acoustic-rate drive band the RF probe cannot reach"),

    # 5. magnetic field ------------------------------------------------
    _i(id="INS-B-FLUX3-01", channel="magnetic_field",
       quantity="three-axis vector magnetic flux density", unit="nT",
       range_min=-1e5, range_max=1e5,
       resolution=0.1, uncertainty=5.0,
       calibration_id="CAL-B-FLUX3-01", calibration_due_epoch=_DUE,
       notes="three-axis fluxgate magnetometer class, DC-3 kHz. The "
             "source's requested DC-MHz three-axis magnetics at the DC "
             "end; also supplies the local geomagnetic vector for the "
             "orientation discriminator (claim R6-C-003)"),
    _i(id="INS-B-FLUX1-01", channel="magnetic_field",
       quantity="single-axis magnetic flux density", unit="nT",
       range_min=-1e6, range_max=1e6,
       resolution=1.0, uncertainty=20.0,
       calibration_id="CAL-B-FLUX1-01", calibration_due_epoch=_DUE,
       notes="single-axis fluxgate class, DC-1 kHz, higher range for "
             "close-in drive fields that saturate the three-axis unit"),
    _i(id="INS-B-LOOP-01", channel="magnetic_field",
       quantity="AC magnetic field strength", unit="A/m",
       range_min=1e-3, range_max=1e3,
       resolution=1e-3, uncertainty=1e-2,
       calibration_id="CAL-B-LOOP-01", calibration_due_epoch=_DUE,
       notes="calibrated loop antenna / H-field probe class, 9 kHz-"
             "30 MHz. Completes the source's requested DC-to-MHz "
             "magnetic coverage: no single sensor spans DC to MHz, so "
             "the band is covered by three overlapping instruments and "
             "the overlaps must be cross-checked"),

    # 6. crystal charge ------------------------------------------------
    _i(id="INS-Q-CHARGEAMP-01", channel="crystal_charge",
       quantity="piezoelectric charge from the specimen electrodes",
       unit="pC",
       range_min=-1e5, range_max=1e5,
       resolution=0.1, uncertainty=1.0,
       calibration_id="CAL-Q-CHARGEAMP-01", calibration_due_epoch=_DUE,
       notes="laboratory charge amplifier class, 0.1 Hz-200 kHz; drift "
             "and cable triboelectric noise dominate below 1 Hz"),

    # 7. displacement and strain ---------------------------------------
    _i(id="INS-D-LDV-01", channel="displacement_and_strain",
       quantity="out-of-plane surface displacement", unit="m",
       range_min=-1e-4, range_max=1e-4,
       resolution=1e-12, uncertainty=1e-11,
       calibration_id="CAL-D-LDV-01", calibration_due_epoch=_DUE,
       notes="single-point laser Doppler vibrometer class, DC-25 MHz; "
             "supplies the modal-Q measurement for the winding "
             "mass-loading claim (R6-C-004)"),
    _i(id="INS-D-SG-01", channel="displacement_and_strain",
       quantity="surface strain", unit="microstrain",
       range_min=-5000.0, range_max=5000.0,
       resolution=0.1, uncertainty=2.0,
       calibration_id="CAL-D-SG-01", calibration_due_epoch=_DUE,
       notes="foil strain gauge with quarter-bridge conditioner class; "
             "bonded gauges load the specimen and must be included in "
             "the modal model rather than ignored"),

    # 8. sound and ultrasound ------------------------------------------
    _i(id="INS-A-MIC-01", channel="sound_and_ultrasound",
       quantity="free-field sound pressure", unit="Pa",
       range_min=2e-5, range_max=200.0,
       resolution=2e-5, uncertainty=1e-3,
       calibration_id="CAL-A-MIC-01", calibration_due_epoch=_DUE,
       notes="quarter-inch free-field measurement microphone class, "
             "4 Hz-100 kHz, pistonphone-checked. This is the source's "
             "requested sound channel, and it doubles as an artifact "
             "witness: audible drive coupling is a classic false "
             "positive"),
    _i(id="INS-A-UT-01", channel="sound_and_ultrasound",
       quantity="ultrasonic pressure amplitude", unit="Pa",
       range_min=1e-2, range_max=1e5,
       resolution=1e-2, uncertainty=5.0,
       calibration_id="CAL-A-UT-01", calibration_due_epoch=_DUE,
       notes="broadband immersion/contact ultrasonic transducer class, "
             "100 kHz-5 MHz, covering the 1496/644/587 Hz harmonics "
             "and the crystal's own modes (claim R6-C-006)"),

    # 9. optical --------------------------------------------------------
    _i(id="INS-O-SPEC-VIS-01", channel="optical",
       quantity="spectral irradiance, 200-1100 nm", unit="uW/cm2/nm",
       range_min=0.0, range_max=1e3,
       resolution=1e-4, uncertainty=5e-3,
       calibration_id="CAL-O-SPEC-VIS-01", calibration_due_epoch=_DUE,
       notes="fibre-coupled CCD spectrometer class, ~1 nm resolution"),
    _i(id="INS-O-SPEC-NIR-01", channel="optical",
       quantity="spectral irradiance, 900-1800 nm", unit="uW/cm2/nm",
       range_min=0.0, range_max=1e3,
       resolution=1e-3, uncertainty=2e-2,
       calibration_id="CAL-O-SPEC-NIR-01", calibration_due_epoch=_DUE,
       notes="cooled InGaAs spectrometer class. The source asked for "
             "optical coverage 200-1800 nm; no single grating and "
             "detector spans that, so it takes a Si instrument and an "
             "InGaAs instrument with an overlap region (900-1100 nm) "
             "that must be cross-calibrated or the join will itself "
             "look like a feature"),
    _i(id="INS-O-POL-01", channel="optical",
       quantity="Stokes polarization parameters", unit="dimensionless",
       range_min=-1.0, range_max=1.0,
       resolution=1e-4, uncertainty=1e-3,
       calibration_id="CAL-O-POL-01", calibration_due_epoch=_DUE,
       notes="rotating-waveplate polarimeter class; the chirality and "
             "magnetochiral work is a polarization measurement before "
             "it is anything else"),

    # 10. thermal state --------------------------------------------------
    _i(id="INS-T-IR-01", channel="thermal_state",
       quantity="surface temperature field, radiometric", unit="K",
       range_min=253.15, range_max=923.15,
       resolution=0.03, uncertainty=2.0,
       calibration_id="CAL-T-IR-01", calibration_due_epoch=_DUE,
       notes="640x480 microbolometer thermal camera class, NETD "
             "~30 mK. This is the source's requested IR thermal "
             "channel. Note the gap between resolution and absolute "
             "uncertainty: it resolves 30 mK of *change* but its "
             "absolute reading is good to ~2 K and depends on an "
             "assumed emissivity, so it may be used for differential "
             "work only"),
    _i(id="INS-T-RTD-01", channel="thermal_state",
       quantity="contact temperature", unit="K",
       range_min=73.15, range_max=773.15,
       resolution=1e-3, uncertainty=0.03,
       calibration_id="CAL-T-RTD-01", calibration_due_epoch=_DUE,
       notes="4-wire Pt100 class A with bridge; the absolute reference "
             "the thermal camera is tied to"),

    # 11. electrostatic / ion / ozone / humidity / airflow ---------------
    _i(id="INS-ES-FIELDMILL-01",
       channel="electrostatic_ion_ozone_humidity_airflow",
       quantity="quasi-static electrostatic field", unit="kV/m",
       range_min=-200.0, range_max=200.0,
       resolution=1e-2, uncertainty=0.5,
       calibration_id="CAL-ES-FIELDMILL-01", calibration_due_epoch=_DUE,
       notes="rotating-vane field mill class, DC-1 kHz"),
    _i(id="INS-ES-IONCTR-01",
       channel="electrostatic_ion_ozone_humidity_airflow",
       quantity="small air ion concentration", unit="ions/cm3",
       range_min=0.0, range_max=2e6,
       resolution=10.0, uncertainty=2e3,
       calibration_id="CAL-ES-IONCTR-01", calibration_due_epoch=_DUE,
       notes="Gerdien-condenser air ion counter class; corona from a "
             "high-voltage drive is the single most likely ordinary "
             "explanation for a 'field' someone can feel"),
    _i(id="INS-ES-O3-01",
       channel="electrostatic_ion_ozone_humidity_airflow",
       quantity="ozone concentration", unit="ppb",
       range_min=0.0, range_max=1e4,
       resolution=0.5, uncertainty=2.0,
       calibration_id="CAL-ES-O3-01", calibration_due_epoch=_DUE,
       notes="UV-absorption ozone analyser class; the chemical "
             "signature of the same corona, and a safety channel"),
    _i(id="INS-ES-RH-01",
       channel="electrostatic_ion_ozone_humidity_airflow",
       quantity="relative humidity", unit="%RH",
       range_min=0.0, range_max=100.0,
       resolution=0.1, uncertainty=1.5,
       calibration_id="CAL-ES-RH-01", calibration_due_epoch=_DUE,
       notes="capacitive RH/T probe class; humidity moves surface "
             "leakage by orders of magnitude and is the usual reason "
             "an electrostatic result fails to replicate in another "
             "season"),
    _i(id="INS-ES-AIR-01",
       channel="electrostatic_ion_ozone_humidity_airflow",
       quantity="air speed", unit="m/s",
       range_min=0.0, range_max=20.0,
       resolution=1e-2, uncertainty=0.05,
       calibration_id="CAL-ES-AIR-01", calibration_due_epoch=_DUE,
       notes="hot-wire anemometer class; electrohydrodynamic airflow "
             "(ion wind) is a real force-producing mechanism and must "
             "be measured, not assumed absent"),

    # 12. force and torque ----------------------------------------------
    _i(id="INS-F-FT6-01", channel="force_and_torque",
       quantity="six-axis force and torque", unit="N",
       range_min=-100.0, range_max=100.0,
       resolution=1e-3, uncertainty=2e-2,
       calibration_id="CAL-F-FT6-01", calibration_due_epoch=_DUE,
       notes="six-axis strain-gauge force/torque transducer class; "
             "torque axes quoted separately in N*m in the calibration "
             "certificate"),
    _i(id="INS-F-BALANCE-01", channel="force_and_torque",
       quantity="apparent weight change under drive", unit="N",
       range_min=-2.0, range_max=2.0,
       resolution=1e-6, uncertainty=1e-5,
       calibration_id="CAL-F-BALANCE-01", calibration_due_epoch=_DUE,
       notes="microbalance class in a draft shield; the shield is not "
             "optional, since the anemometer channel exists precisely "
             "because air movement mimics a force"),

    # 13. collector charge ------------------------------------------------
    _i(id="INS-C-ELECTROMETER-01", channel="collector_charge",
       quantity="collected charge", unit="C",
       range_min=-2e-6, range_max=2e-6,
       resolution=1e-14, uncertainty=1e-13,
       calibration_id="CAL-C-ELECTROMETER-01", calibration_due_epoch=_DUE,
       notes="guarded electrometer class, 10 fC-2 uC, triaxial input"),
    _i(id="INS-C-CONE52-01", channel="collector_charge",
       quantity="charge accumulated on the 52-degree copper cone",
       unit="C",
       range_min=-2e-6, range_max=2e-6,
       resolution=1e-14, uncertainty=5e-13,
       calibration_id="CAL-C-CONE52-01", calibration_due_epoch=_DUE,
       notes="the source's requested 52-degree copper cone/pyramid "
             "collector (claim R6-C-008). The cone is a FIXTURE, not "
             "an instrument: it is an electrode whose geometric "
             "capacitance must be modeled and measured, read out by "
             "INS-C-ELECTROMETER-01. Its extra uncertainty over the "
             "bare electrometer is the capacitance model. Photons are "
             "electrically neutral, so this measures collector charge "
             "and not 'charge in the photonic field'"),

    # 14. oscillator phase and frequency ---------------------------------
    _i(id="INS-OSC-OCXO-A", channel="oscillator_phase_and_frequency",
       quantity="10 MHz reference frequency", unit="Hz",
       range_min=9_999_999.9, range_max=10_000_000.1,
       resolution=1e-6, uncertainty=1e-5,
       calibration_id="CAL-OSC-OCXO-A", calibration_due_epoch=_DUE,
       notes="first of the source's requested MATCHED PRECISION "
             "OSCILLATOR pair; double-oven OCXO class, Allan deviation "
             "~1e-12 at 1 s. A matched pair is required because a "
             "single oscillator cannot measure its own instability"),
    _i(id="INS-OSC-OCXO-B", channel="oscillator_phase_and_frequency",
       quantity="10 MHz reference frequency", unit="Hz",
       range_min=9_999_999.9, range_max=10_000_000.1,
       resolution=1e-6, uncertainty=1e-5,
       calibration_id="CAL-OSC-OCXO-B", calibration_due_epoch=_DUE,
       notes="second of the matched pair, same production lot, "
             "separately calibrated. Common-mode temperature is the "
             "dominant shared error and is why the thermal channel is "
             "recorded alongside"),
    _i(id="INS-OSC-CTR-01", channel="oscillator_phase_and_frequency",
       quantity="frequency and time interval", unit="Hz",
       range_min=1e-3, range_max=3e9,
       resolution=1e-6, uncertainty=1e-4,
       calibration_id="CAL-OSC-CTR-01", calibration_due_epoch=_DUE,
       notes="12-digit reciprocal frequency counter class with an "
             "external reference input fed from the OCXO pair"),
    _i(id="INS-OSC-PN-01", channel="oscillator_phase_and_frequency",
       quantity="phase noise and Allan deviation",
       unit="dimensionless",
       range_min=1e-15, range_max=1e-6,
       resolution=1e-15, uncertainty=1e-14,
       calibration_id="CAL-OSC-PN-01", calibration_due_epoch=_DUE,
       notes="cross-correlation phase noise test set class. This is "
             "the instrument that makes r6.witness.ClockWitness "
             "possible at all: without a measured instability there is "
             "no clock, only an oscillator"),

    # 15. radiation --------------------------------------------------------
    _i(id="INS-R-GM-01", channel="radiation",
       quantity="gross beta/gamma count rate", unit="counts/s",
       range_min=0.0, range_max=1e5,
       resolution=0.1, uncertainty=1.0,
       calibration_id="CAL-R-GM-01", calibration_due_epoch=_DUE,
       notes="pancake Geiger-Mueller probe class; the source's "
             "requested radiation channel at the survey end"),
    _i(id="INS-R-NAI-01", channel="radiation",
       quantity="gamma spectrum, 30 keV-3 MeV", unit="counts/s/keV",
       range_min=0.0, range_max=1e4,
       resolution=1e-2, uncertainty=0.1,
       calibration_id="CAL-R-NAI-01", calibration_due_epoch=_DUE,
       notes="2x2 inch NaI(Tl) scintillation spectrometer class; a "
             "spectrum discriminates a real source from a count-rate "
             "artifact, which a bare survey meter cannot"),
    _i(id="INS-R-EPD-01", channel="radiation",
       quantity="ambient dose equivalent rate", unit="uSv/h",
       range_min=0.01, range_max=1e4,
       resolution=0.01, uncertainty=0.1,
       calibration_id="CAL-R-EPD-01", calibration_due_epoch=_DUE,
       notes="electronic personal dosimeter class; a safety channel "
             "as much as a measurement channel"),

    # 16. chemistry and material change ------------------------------------
    _i(id="INS-CH-FTIR-01", channel="chemistry_material_change",
       quantity="infrared absorbance, 400-4000 1/cm",
       unit="absorbance",
       range_min=0.0, range_max=4.0,
       resolution=1e-4, uncertainty=2e-3,
       calibration_id="CAL-CH-FTIR-01", calibration_due_epoch=_DUE,
       notes="benchtop FTIR with ATR class; detects surface chemical "
             "change on the specimen and on the windings"),
    _i(id="INS-CH-BALANCE-01", channel="chemistry_material_change",
       quantity="specimen mass", unit="g",
       range_min=0.0, range_max=220.0,
       resolution=1e-5, uncertainty=5e-5,
       calibration_id="CAL-CH-BALANCE-01", calibration_due_epoch=_DUE,
       notes="analytical balance class; mass loss from outgassing or "
             "oxidation is slow, cumulative and easy to mistake for "
             "drift in every other channel"),
    _i(id="INS-CH-PROFILE-01", channel="chemistry_material_change",
       quantity="surface height / roughness", unit="m",
       range_min=0.0, range_max=1e-3,
       resolution=1e-9, uncertainty=1e-8,
       calibration_id="CAL-CH-PROFILE-01", calibration_due_epoch=_DUE,
       notes="optical profilometer class; electrode erosion and "
             "silver tarnish are material changes that alter the "
             "impedance channel over a long run"),

    # 17. environmental and instrumentation cross-talk ----------------------
    _i(id="INS-X-SA-01",
       channel="environmental_and_instrumentation_crosstalk",
       quantity="received RF power spectral density", unit="dBm",
       range_min=-160.0, range_max=30.0,
       resolution=0.1, uncertainty=1.5,
       calibration_id="CAL-X-SA-01", calibration_due_epoch=_DUE,
       notes="spectrum analyser class, 9 kHz-13.6 GHz, with EMI "
             "pre-amp; finds mains harmonics, switching supplies and "
             "the broadcast band before they are called a result"),
    _i(id="INS-X-DUMMY-01",
       channel="environmental_and_instrumentation_crosstalk",
       quantity="terminated dummy-sensor output", unit="V",
       range_min=-10.0, range_max=10.0,
       resolution=1e-6, uncertainty=1e-5,
       calibration_id="CAL-X-DUMMY-01", calibration_due_epoch=_DUE,
       notes="an identical acquisition chain terminated into a dummy "
             "load, recorded simultaneously. Anything that appears "
             "here appeared in the electronics, not in the apparatus. "
             "It is the cheapest instrument in the matrix and the one "
             "most often left out"),
    _i(id="INS-X-ACC-01",
       channel="environmental_and_instrumentation_crosstalk",
       quantity="ambient triaxial acceleration", unit="m/s2",
       range_min=-20.0, range_max=20.0,
       resolution=1e-5, uncertainty=1e-4,
       calibration_id="CAL-X-ACC-01", calibration_due_epoch=_DUE,
       notes="MEMS/piezo triaxial accelerometer class; building "
             "vibration couples into the vibrometer, the balance and "
             "the charge amplifier cabling"),
    _i(id="INS-X-MAINS-01",
       channel="environmental_and_instrumentation_crosstalk",
       quantity="mains supply voltage and line frequency", unit="V",
       range_min=0.0, range_max=300.0,
       resolution=1e-3, uncertainty=0.1,
       calibration_id="CAL-X-MAINS-01", calibration_due_epoch=_DUE,
       notes="power quality logger class; mains sag correlates with "
             "building HVAC, which correlates with temperature, which "
             "correlates with everything"),

    # 18. sham drive ---------------------------------------------------------
    _i(id="INS-SH-SWITCH-01", channel="sham_drive",
       quantity="drive-enable state under a blinded schedule",
       unit="dimensionless",
       range_min=0.0, range_max=1.0,
       resolution=1.0, uncertainty=1.0,
       calibration_id="CAL-SH-SWITCH-01", calibration_due_epoch=_DUE,
       notes="sealed relay unit that connects or disconnects the drive "
             "under a pre-generated randomized schedule the operator "
             "cannot read. Its 'measurement' is one bit per epoch, so "
             "resolution and uncertainty are both 1 by construction: "
             "the epoch is either sham or live and the record is "
             "unsealed only at analysis"),
    _i(id="INS-SH-IMON-01", channel="sham_drive",
       quantity="verification current during sham epochs", unit="A",
       range_min=-1e-3, range_max=1e-3,
       resolution=1e-9, uncertainty=1e-8,
       calibration_id="CAL-SH-IMON-01", calibration_due_epoch=_DUE,
       notes="independent low-range current monitor that confirms the "
             "sham epochs really carried no drive current. A sham "
             "control nobody verified is not a control"),
)


#: Devices the source asked for whose claimed quantity has no accepted
#: calibration standard. They are registered so the refusal is visible
#: data rather than an omission, and they carry no measurement weight
#: anywhere in R6.
UNCALIBRATED_DEVICES: tuple[UncalibratedDevice, ...] = (
    UncalibratedDevice(
        id="DEV-CADUCEUS-TORSION-01",
        claimed_quantity="scalar / torsion field amplitude",
        reason=(
            "A scalar or torsion sensor built from caduceus (bifilar "
            "counter-wound) coils has NO accepted calibration standard, "
            "because there is no agreed reference source of the "
            "quantity it claims to measure, no traceability chain and "
            "no unit. Its output is a voltage on an unbalanced winding "
            "and responds to ordinary electromagnetic pickup, thermal "
            "EMF and mechanical microphonics — all of which are "
            "already covered by calibrated instruments in "
            "INSTRUMENT_MATRIX. It is therefore NOT a measurement "
            "channel: it cannot bound anything, cannot contribute to a "
            "combined uncertainty, and cannot raise or support a "
            "residual. If it is built at all it is built as an "
            "apparatus element whose ordinary response is characterized "
            "by the calibrated instruments, never as a detector."),
    ),
)


# --------------------------------------------------------------------
# Coverage
# --------------------------------------------------------------------

def instruments_by_channel() -> dict[str, tuple[Instrument, ...]]:
    """The matrix indexed by ordinary channel. Raises on duplicate ids."""
    seen: set[str] = set()
    out: dict[str, list[Instrument]] = {c: [] for c in ORDINARY_CHANNELS}
    for ins in INSTRUMENT_MATRIX:
        if ins.id in seen:
            raise ValueError(f"duplicate instrument id {ins.id!r}")
        seen.add(ins.id)
        out[ins.channel].append(ins)
    return {c: tuple(v) for c, v in out.items()}


def instrument(instrument_id: str) -> Instrument:
    """Look up one instrument by id."""
    for ins in INSTRUMENT_MATRIX:
        if ins.id == instrument_id:
            return ins
    raise KeyError(
        f"no instrument {instrument_id!r} in INSTRUMENT_MATRIX. If this "
        f"is an uncalibrated device see UNCALIBRATED_DEVICES; it is not "
        f"a measurement channel.")


def coverage_report() -> dict:
    """Which ordinary channels have instruments and which do not.

    The gate on everything downstream. ``complete`` must be True before
    any residual may be registered: a residual computed against a
    partial instrument set is not a small residual, it is an
    undefined one.
    """
    by_channel = instruments_by_channel()
    covered = tuple(c for c in ORDINARY_CHANNELS if by_channel[c])
    missing = tuple(c for c in ORDINARY_CHANNELS if not by_channel[c])
    return {
        "n_channels": len(ORDINARY_CHANNELS),
        "n_instruments": len(INSTRUMENT_MATRIX),
        "covered": covered,
        "missing": missing,
        "complete": not missing,
        "instruments_per_channel": {
            c: tuple(i.id for i in by_channel[c]) for c in ORDINARY_CHANNELS
        },
        "uncalibrated_devices": tuple(d.id for d in UNCALIBRATED_DEVICES),
        "note": (
            "Catalogue-class specifications, not owned equipment and "
            "not bench data. Uncalibrated devices are listed separately "
            "and cover no channel."),
    }


# --------------------------------------------------------------------
# Measurements and the sham control
# --------------------------------------------------------------------

@dataclass(frozen=True)
class ChannelMeasurement:
    """One ordinary channel, measured and bounded, by one instrument.

    ``bounded`` is the honest flag: an instrument can be pointed at a
    channel and still fail to bound it (out of range, out of band,
    saturated, or uncalibrated at the condition of interest). An
    unbounded channel counts as missing.

    Not bench data: values supplied here are model or planning figures
    until a calibration certificate and a raw capture back them.
    """

    channel: str
    instrument_id: str
    value: float
    unit: str
    uncertainty: float
    bounded: bool = True
    notes: str = ""

    def __post_init__(self) -> None:
        if self.channel not in ORDINARY_CHANNELS:
            raise ValueError(
                f"{self.channel!r} is not a declared ordinary channel")
        ins = instrument(self.instrument_id)
        if ins.channel != self.channel:
            raise ValueError(
                f"instrument {ins.id} is registered on channel "
                f"{ins.channel!r}, not {self.channel!r}")
        if self.uncertainty <= 0:
            raise ValueError(
                f"{self.channel}: uncertainty must be positive")

    def as_record(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ShamControl:
    """A blinded sham-drive control run.

    Every field is a precondition, not a description. A sham control
    that was not blinded, not randomized, or not verified to have
    carried no drive current is not a control, and
    :func:`register_residual` refuses on it.
    """

    control_id: str
    n_sham_epochs: int
    n_live_epochs: int
    blinded_to_operator: bool
    randomized_order: bool
    drive_current_verified_zero: bool
    verification_instrument_id: str = "INS-SH-IMON-01"
    schedule_seed: int = 20260718
    notes: str = ""

    def deficiencies(self) -> tuple[str, ...]:
        """Everything wrong with this control, named."""
        bad: list[str] = []
        if not self.blinded_to_operator:
            bad.append(
                "not blinded to the operator: the operator knows which "
                "epochs are live and expectancy is a real effect on "
                "every hand-placed sensor")
        if not self.randomized_order:
            bad.append(
                "epoch order not randomized: any monotonic drift "
                "(warm-up, humidity, electrode tarnish) aliases "
                "directly onto the sham/live contrast")
        if not self.drive_current_verified_zero:
            bad.append(
                "sham epochs not verified to carry zero drive current "
                "by an independent monitor")
        if self.n_sham_epochs < 1:
            bad.append("no sham epochs were run")
        if self.n_live_epochs < 1:
            bad.append("no live epochs were run")
        return tuple(bad)

    def as_record(self) -> dict:
        d = asdict(self)
        d["deficiencies"] = list(self.deficiencies())
        return d


def sham_drive_protocol() -> dict:
    """The blinded sham-drive control, as an inspectable specification.

    The sham drive is the eighteenth ordinary channel and the cheapest
    decisive one. Apparatus, cabling, sensors, operator, room and
    schedule are identical between sham and live epochs; the single
    difference is whether drive current flows.
    """
    return {
        "id": "PROTO-SHAM-DRIVE-01",
        "principle": (
            "The sham epoch differs from the live epoch in exactly one "
            "respect: no drive current. Everything else — apparatus, "
            "fixturing, cabling, sensor placement, operator, room, time "
            "of day distribution, acquisition settings — is identical."),
        "steps": (
            "1. Build the drive-enable schedule in advance from a "
            "declared seed, with sham and live epochs in randomized "
            "order and balanced counts.",
            "2. Seal the schedule. The operator and anyone who touches "
            "a sensor or reads a display must not know which epoch is "
            "which. The relay unit (INS-SH-SWITCH-01) is audibly and "
            "visually identical in both states.",
            "3. Keep the drive electronics powered and the amplifier "
            "biased in both conditions; disconnect only the current "
            "path, so supply noise and fan acoustics are common-mode.",
            "4. Verify with an independent low-range current monitor "
            "(INS-SH-IMON-01) that sham epochs carried no drive "
            "current. Record the verification, do not assume it.",
            "5. Record every other ordinary channel identically in both "
            "conditions, including the terminated dummy-sensor chain "
            "(INS-X-DUMMY-01).",
            "6. Interleave and repeat, so slow drift cannot align with "
            "the condition.",
            "7. Unseal the schedule only after the analysis is frozen. "
            "Analyse sham and live with identical code paths.",
        ),
        "blinding": (
            "Blinded to the operator, to anyone handling sensors, and "
            "to the analyst until the analysis is frozen."),
        "randomization": (
            "Randomized epoch order from a declared seed; the seed is "
            "recorded so the schedule is reproducible after unsealing."),
        "failure_modes_this_catches": (
            "operator expectancy and handling",
            "warm-up and thermal drift misread as a drive response",
            "supply and switching noise entering the acquisition chain",
            "acoustic and vibrational coupling from the drive hardware",
            "corona, ion wind and humidity change",
        ),
        "note": (
            "Specification only. No sham run has been performed; "
            "nothing here is bench data."),
    }


# --------------------------------------------------------------------
# Residual records
# --------------------------------------------------------------------

#: What each rung of the ladder demands before it may be entered. Kept
#: as data so the gate is inspectable rather than buried in branches.
PROMOTION_REQUIREMENTS: dict[str, str] = {
    "SOURCE_CLAIM":
        "nothing; this is where a verbatim source statement enters",
    "OPERATIONAL_HYPOTHESIS":
        "an operational definition: a named observable, the instrument "
        "that would measure it, and the outcome that would count "
        "against the hypothesis",
    "ORDINARY_CHANNEL_RESULT":
        "all eighteen ordinary channels measured and bounded, plus a "
        "blinded sham-drive control with no deficiencies",
    "UNEXPLAINED_INSTRUMENT_RESIDUAL":
        "a residual magnitude exceeding k_sigma times the combined "
        "instrument uncertainty, on a complete and sham-controlled "
        "channel set",
    "REPLICATED_ANOMALY":
        "an independent replication record: a different group, "
        "different apparatus, blinded, consistent result",
    "CANDIDATE_NEW_MECHANISM":
        "a proposed mechanism together with at least one falsifiable "
        "prediction that would distinguish it from the ordinary "
        "explanations already bounded",
}


@dataclass(frozen=True)
class Replication:
    """An independent replication attempt."""

    replication_id: str
    group: str
    apparatus_id: str
    blinded: bool
    result_consistent: bool
    notes: str = ""

    def as_record(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ResidualRecord:
    """A residual, or a claim on its way to becoming one.

    ``evidence_class`` is restricted to :data:`r6.PHRYLL_CLASSES`. The
    top of that ladder is CANDIDATE_NEW_MECHANISM: a mechanism someone
    proposed and someone else can falsify. It is not a discovery, and
    there is deliberately no rung above it and no detection state (r6
    FORBIDDEN_COLLAPSES: RESIDUAL_IS_ONTOLOGY).

    Not bench data. Every record produced by this module describes a
    planned or modeled measurement.
    """

    record_id: str
    observable: str
    evidence_class: str
    group: str = "ORIGINATING_GROUP"
    magnitude: float = 0.0
    magnitude_unit: str = "dimensionless"
    combined_uncertainty: float = 0.0
    k_sigma: float = 3.0
    measurements: tuple[ChannelMeasurement, ...] = ()
    sham_control: ShamControl | None = None
    operational_definition: str | None = None
    replications: tuple[Replication, ...] = ()
    proposed_mechanism: str | None = None
    falsifiable_prediction: str | None = None
    notes: tuple[str, ...] = ()
    provenance: str = "R6 P05 model record; not bench data"

    def __post_init__(self) -> None:
        if self.evidence_class not in PHRYLL_CLASSES:
            raise ValueError(
                f"record {self.record_id}: evidence_class "
                f"{self.evidence_class!r} is not on the ladder "
                f"{PHRYLL_CLASSES}")
        if self.evidence_class in FORBIDDEN_STATES:
            raise ValueError(
                f"record {self.record_id}: {self.evidence_class!r} is a "
                f"forbidden state (r6.FORBIDDEN_STATES)")
        if self.k_sigma <= 0:
            raise ValueError("k_sigma must be positive")

    # -- derived ------------------------------------------------------

    def measured_channels(self) -> tuple[str, ...]:
        return tuple(sorted({m.channel for m in self.measurements
                             if m.bounded}))

    def missing_channels(self) -> tuple[str, ...]:
        """Ordinary channels not yet measured *and bounded*."""
        have = set(self.measured_channels())
        return tuple(c for c in ORDINARY_CHANNELS if c not in have)

    def significant(self) -> bool:
        """Whether the residual clears the combined uncertainty."""
        if self.combined_uncertainty <= 0:
            return False
        return abs(self.magnitude) > self.k_sigma * self.combined_uncertainty

    def independent_replications(self) -> tuple[Replication, ...]:
        return tuple(r for r in self.replications
                     if r.group != self.group and r.blinded
                     and r.result_consistent)

    def as_record(self) -> dict:
        return {
            "record_id": self.record_id,
            "observable": self.observable,
            "evidence_class": self.evidence_class,
            "group": self.group,
            "magnitude": self.magnitude,
            "magnitude_unit": self.magnitude_unit,
            "combined_uncertainty": self.combined_uncertainty,
            "k_sigma": self.k_sigma,
            "significant": self.significant(),
            "measured_channels": list(self.measured_channels()),
            "missing_channels": list(self.missing_channels()),
            "sham_control": (self.sham_control.as_record()
                             if self.sham_control else None),
            "operational_definition": self.operational_definition,
            "replications": [r.as_record() for r in self.replications],
            "n_independent_replications":
                len(self.independent_replications()),
            "proposed_mechanism": self.proposed_mechanism,
            "falsifiable_prediction": self.falsifiable_prediction,
            "notes": list(self.notes),
            "provenance": self.provenance,
            "ceiling": (
                "CANDIDATE_NEW_MECHANISM is the top of the ladder. A "
                "residual names a measurement that is not yet "
                "understood, not a substance."),
        }


def seed_record(record_id: str, observable: str, *,
                group: str = "ORIGINATING_GROUP",
                evidence_class: str = "SOURCE_CLAIM",
                notes: tuple[str, ...] = (),
                ) -> ResidualRecord:
    """Enter a claim at the bottom of the ladder.

    Carries no measurement: magnitude and uncertainty are zero and
    :meth:`ResidualRecord.significant` is False until a real
    measurement set is attached by :func:`register_residual`.
    """
    return ResidualRecord(record_id=record_id, observable=observable,
                          evidence_class=evidence_class, group=group,
                          notes=notes)


def combined_uncertainty(measurements) -> float:
    """Root-sum-square of the per-channel standard uncertainties.

    RSS assumes the channel uncertainties are independent. They are
    not, in general: a shared temperature or a shared reference moves
    several at once, and correlated terms make the true combined
    uncertainty *larger* than this. RSS is therefore the optimistic
    bound, and a residual that only just clears it has not cleared it.
    """
    return math.sqrt(sum(m.uncertainty ** 2 for m in measurements))


def register_residual(*,
                      record_id: str,
                      observable: str,
                      magnitude: float,
                      magnitude_unit: str,
                      measurements,
                      sham_control: ShamControl | None,
                      group: str = "ORIGINATING_GROUP",
                      k_sigma: float = 3.0,
                      notes: tuple[str, ...] = (),
                      ) -> ResidualRecord:
    """Register an UNEXPLAINED_INSTRUMENT_RESIDUAL, or refuse.

    Refuses — loudly, naming what is missing — unless all three hold:

    1. the instrument matrix covers every ordinary channel, AND every
       one of the eighteen channels has been measured and bounded in
       this run;
    2. a blinded sham-drive control was run with no deficiencies;
    3. the residual magnitude exceeds ``k_sigma`` times the combined
       instrument uncertainty.

    :raises RefusedError: with the missing channels named.
    """
    measurements = tuple(measurements)

    cov = coverage_report()
    if not cov["complete"]:
        raise RefusedError(
            "refused: the instrument matrix does not cover every "
            "ordinary channel, so a residual is undefined rather than "
            "small. Channels with no instrument: "
            f"{', '.join(cov['missing'])}")

    for m in measurements:
        if m.instrument_id not in {i.id for i in INSTRUMENT_MATRIX}:
            raise RefusedError(
                f"refused: measurement on {m.channel!r} cites "
                f"{m.instrument_id!r}, which is not in the instrument "
                f"matrix")

    bounded = {m.channel for m in measurements if m.bounded}
    unbounded = sorted({m.channel for m in measurements if not m.bounded})
    missing = [c for c in ORDINARY_CHANNELS if c not in bounded]
    if missing:
        detail = ""
        if unbounded:
            detail = (f" (instruments were present but did not bound: "
                      f"{', '.join(unbounded)})")
        raise RefusedError(
            f"refused: {len(missing)} of {len(ORDINARY_CHANNELS)} "
            f"ordinary channels are unmeasured or unbounded, so there "
            f"is nothing a residual is residual *to*. Missing: "
            f"{', '.join(missing)}{detail}")

    if sham_control is None:
        raise RefusedError(
            "refused: no sham-drive control was run. Without a blinded "
            "sham control the contrast is between 'drive on' and "
            "'nothing recorded', which cannot separate the drive from "
            "the act of running the apparatus. See "
            "sham_drive_protocol().")
    deficiencies = sham_control.deficiencies()
    if deficiencies:
        raise RefusedError(
            f"refused: sham control {sham_control.control_id!r} is not "
            f"a control: {'; '.join(deficiencies)}")

    u = combined_uncertainty(measurements)
    if u <= 0:
        raise RefusedError(
            "refused: the combined instrument uncertainty is zero, "
            "which no real instrument set has")
    if abs(magnitude) <= k_sigma * u:
        raise RefusedError(
            f"refused: residual magnitude {magnitude:.6g} "
            f"{magnitude_unit} does not exceed {k_sigma} x the combined "
            f"instrument uncertainty ({k_sigma * u:.6g}). This is a "
            f"null result on {observable!r}, and a null result is a "
            f"result — record it as ORDINARY_CHANNEL_RESULT rather "
            f"than as a residual.")

    return ResidualRecord(
        record_id=record_id,
        observable=observable,
        evidence_class="UNEXPLAINED_INSTRUMENT_RESIDUAL",
        group=group,
        magnitude=float(magnitude),
        magnitude_unit=magnitude_unit,
        combined_uncertainty=u,
        k_sigma=float(k_sigma),
        measurements=measurements,
        sham_control=sham_control,
        notes=tuple(notes) + (
            "UNEXPLAINED_INSTRUMENT_RESIDUAL names a measurement that "
            "is not yet understood. It names no substance and no "
            "mechanism.",
            "RSS combined uncertainty assumes independent channels; "
            "correlated environmental terms make the true figure "
            "larger.",
            "Not bench data.",
        ))


def promote(record: ResidualRecord, target_class: str, *,
            operational_definition: str | None = None,
            replication: Replication | None = None,
            proposed_mechanism: str | None = None,
            falsifiable_prediction: str | None = None,
            ) -> ResidualRecord:
    """Move a record exactly one rung up the ladder, or refuse.

    The ladder is :data:`r6.PHRYLL_CLASSES` and the requirements are
    :data:`PROMOTION_REQUIREMENTS`. Promotion is gated on evidence, not
    on intent, and there is **no state above CANDIDATE_NEW_MECHANISM**
    and no detection state at any rung.

    :raises RefusedError: naming the requirement that was not met.
    """
    if target_class in FORBIDDEN_STATES:
        raise RefusedError(
            f"refused: {target_class!r} is in r6.FORBIDDEN_STATES and "
            f"cannot exist anywhere in R6")
    if target_class not in PHRYLL_CLASSES:
        raise RefusedError(
            f"refused: {target_class!r} is not on the ladder "
            f"{PHRYLL_CLASSES}. The top rung is "
            f"{PHRYLL_CLASSES[-1]!r} and there is nothing above it: no "
            f"detection state, no confirmation state, no ontology.")

    here = PHRYLL_CLASSES.index(record.evidence_class)
    there = PHRYLL_CLASSES.index(target_class)
    if there <= here:
        raise RefusedError(
            f"refused: {record.record_id} is already at "
            f"{record.evidence_class!r}; promotion only moves up")
    if there != here + 1:
        raise RefusedError(
            f"refused: cannot jump from {record.evidence_class!r} to "
            f"{target_class!r}. Every intermediate rung has its own "
            f"evidence requirement; the next one is "
            f"{PHRYLL_CLASSES[here + 1]!r}, which requires "
            f"{PROMOTION_REQUIREMENTS[PHRYLL_CLASSES[here + 1]]}.")

    changes: dict = {"evidence_class": target_class}

    if target_class == "OPERATIONAL_HYPOTHESIS":
        definition = operational_definition or record.operational_definition
        if not definition:
            raise RefusedError(
                "refused: OPERATIONAL_HYPOTHESIS requires "
                + PROMOTION_REQUIREMENTS["OPERATIONAL_HYPOTHESIS"])
        changes["operational_definition"] = definition

    elif target_class == "ORDINARY_CHANNEL_RESULT":
        missing = record.missing_channels()
        if missing:
            raise RefusedError(
                f"refused: ORDINARY_CHANNEL_RESULT requires all "
                f"{len(ORDINARY_CHANNELS)} ordinary channels measured "
                f"and bounded. Missing: {', '.join(missing)}")
        if record.sham_control is None:
            raise RefusedError(
                "refused: ORDINARY_CHANNEL_RESULT requires a blinded "
                "sham-drive control; none was attached. See "
                "sham_drive_protocol().")
        deficiencies = record.sham_control.deficiencies()
        if deficiencies:
            raise RefusedError(
                f"refused: the attached sham control is not a control: "
                f"{'; '.join(deficiencies)}")

    elif target_class == "UNEXPLAINED_INSTRUMENT_RESIDUAL":
        if not record.significant():
            raise RefusedError(
                f"refused: UNEXPLAINED_INSTRUMENT_RESIDUAL requires a "
                f"magnitude above {record.k_sigma} x the combined "
                f"instrument uncertainty "
                f"({record.k_sigma * record.combined_uncertainty:.6g}); "
                f"this record has {record.magnitude:.6g}. A residual "
                f"inside the noise floor is the noise floor.")

    elif target_class == "REPLICATED_ANOMALY":
        reps = list(record.replications)
        if replication is not None:
            reps.append(replication)
        candidate = replace(record, replications=tuple(reps))
        independent = candidate.independent_replications()
        if not independent:
            problems: list[str] = []
            if replication is None and not record.replications:
                problems.append("no replication record was supplied")
            for r in reps:
                if r.group == record.group:
                    problems.append(
                        f"{r.replication_id}: same group as the "
                        f"originating record ({r.group!r}); a group "
                        f"reproducing itself reproduces its own "
                        f"systematics")
                elif not r.blinded:
                    problems.append(
                        f"{r.replication_id}: not blinded")
                elif not r.result_consistent:
                    problems.append(
                        f"{r.replication_id}: result not consistent "
                        f"with the original")
            raise RefusedError(
                "refused: REPLICATED_ANOMALY requires "
                + PROMOTION_REQUIREMENTS["REPLICATED_ANOMALY"]
                + ". " + "; ".join(problems))
        changes["replications"] = tuple(reps)

    elif target_class == "CANDIDATE_NEW_MECHANISM":
        mech = proposed_mechanism or record.proposed_mechanism
        pred = falsifiable_prediction or record.falsifiable_prediction
        if not mech:
            raise RefusedError(
                "refused: CANDIDATE_NEW_MECHANISM requires a proposed "
                "mechanism. 'Unexplained' is not a mechanism.")
        if not pred:
            raise RefusedError(
                "refused: CANDIDATE_NEW_MECHANISM requires a "
                "falsifiable prediction — an outcome that would kill "
                "the proposed mechanism and that the ordinary "
                "explanations already bounded do not predict.")
        changes["proposed_mechanism"] = mech
        changes["falsifiable_prediction"] = pred
        changes["notes"] = record.notes + (
            "CANDIDATE_NEW_MECHANISM is the top of the ladder. It "
            "means a mechanism has been proposed and can be "
            "falsified. It does not mean anything has been detected, "
            "and no rung exists above it.",
        )

    return replace(record, **changes)


def ladder_ceiling() -> dict:
    """The top of the ladder, stated so it is inspectable."""
    return {
        "ladder": PHRYLL_CLASSES,
        "top": PHRYLL_CLASSES[-1],
        "nothing_above": (
            "There is no rung above CANDIDATE_NEW_MECHANISM and no "
            "detection state at any rung. The names R6 refuses to hold "
            "are in r6.FORBIDDEN_STATES."),
        "requirements": dict(PROMOTION_REQUIREMENTS),
        "forbidden_collapse": "RESIDUAL_IS_ONTOLOGY",
    }
