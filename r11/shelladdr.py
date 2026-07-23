"""R11 — moving-shell observations and compressed binary-to-octal
address envelopes.

Two things arrive together in the R11 material and this module keeps
them apart, because they are different kinds of object.

**Part 1 — three range readings of one moving shell.** One object is
reported at three ranges, closer each time: 3478, 1903 and 1238 miles.
The candidate order is ordered inward, and the module retains it as
given. What the module refuses to do is the thing the sequence invites:

    Three ranges with MISSING timestamps forbid speed, orbit and ETA.

Speed is a range difference divided by a time difference. Without the
times there is no denominator -- not an uncertain one, not a wide one,
*none*. An orbit needs at least position and velocity (or three
timed positions); with the clock removed, an infinite family of
trajectories passes through the same three radii, from a slow descent
over weeks to a hypersonic pass in minutes, and nothing in the readings
distinguishes them. An arrival time is a speed extrapolated forward, so
it inherits the same emptiness twice over. Supplying a plausible
interval would not estimate the missing quantity; it would *manufacture*
it, and the resulting number would look exactly like a measurement.
So :func:`refuse_speed`, :func:`refuse_orbit` and :func:`refuse_eta`
raise, and the timestamps stay explicitly ``None`` rather than being
quietly omitted from the record.

The order is also protected. The three ranges are a CANDIDATE order --
the order in which they were reported, not an order established by a
clock. A model that fits better under some permutation has not found a
better fit; it has chosen its data. :func:`refuse_reordering` raises,
and any re-ordering must be an explicit, externally justified event.

**Part 2 — one twelve-digit address, viewed through envelopes.** The
raw decimal is preserved exactly, together with its bit length and its
octal and binary renderings, all four mutually consistent. Around it
sit several envelopes: a 42-bit decimal-preserving frame (2-bit header
plus 40-bit payload, serialized as fourteen octal digits), a 36-bit
frame of twelve octal digits, a seven-field mixed-radix address, and
BCD and digit-reversal negative controls.

The load-bearing idea is carried forward from the R10.6/R10.7 codec
work and is the whole point of the exercise:

    A reversible envelope RELOCATES information; it never CREATES it.

Every bit that comes out of a lossless envelope was already in. A clean
round-trip therefore proves the *frame* is faithful and proves nothing
whatever about *content* -- a perfectly reversible envelope over
meaningless input yields perfectly reversible meaningless output.

The 36-bit frame makes the complementary point from the other side.
Thirty-six bits cannot hold a thirty-nine-bit value: three bits are
lost, and each surviving code stands for eight distinct inputs. That is
stated as explicit information-loss accounting, and
:func:`refuse_lossy_as_lossless` raises rather than let a truncated
address be presented as a faithful one. Compression that discards is
not compression that reveals.

Two further refusals guard the reading. Decimal digit strings are never
parsed as octal -- the symbols 8 and 9 do not exist in base 8, so a
string containing them has no octal value at all, and
:func:`refuse_decimal_digits_as_octal` raises instead of silently
mangling it. And header semantics are never inferred from the target
vector: a header meaning read off the one number it was chosen to fit
is retrofitted, not tested, so :func:`refuse_header_semantics_from_target`
raises and points at SYNTHETIC holdouts instead.

Nothing here is measured. No range, no radius, no address and no
envelope is a physical observation made by this software; the ranges
are reported values and the arithmetic on them is exact unit
conversion, nothing more. The standing verdict is
**MOVING_SHELL_SEQUENCE_RETAINED_WITHOUT_KINEMATICS**.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

# --- exact unit constants ----------------------------------------------

#: 1 mile = 1.609344 km, exactly (international mile, by definition).
MILE_KM = Fraction("1.609344")

#: The Earth radius that reproduces the reference R_E ratios exactly.
#:
#: The reference radii were formed as ``1 + range / R_E`` with R_E taken
#: as 3958.7613 miles. Converted with the same exact mile factor that is
#: 6371.0087455872 km. A rounded 6371.0 km does NOT reproduce them: it
#: gives 1.8785588497881023 against the reference 1.8785576437760974,
#: a disagreement of about 1.2e-6, far outside the 1e-9 tolerance. So
#: the R_E that reproduces the references is the one asserted here, and
#: the rounded value is retained below as a documented near-miss.
EARTH_RADIUS_MI = Fraction("3958.7613")
EARTH_RADIUS_KM = EARTH_RADIUS_MI * MILE_KM          # 6371.0087455872
EARTH_RADIUS_KM_ROUNDED = Fraction("6371.0")         # does NOT reproduce

#: Tolerance at which the reference radii must reproduce.
RADIUS_TOLERANCE = 1e-9

# --- address widths ----------------------------------------------------

DECIMAL_WIDTH = 12                       # decimal digits in the address
DECIMAL_MODULUS = 10 ** DECIMAL_WIDTH    # 10**12

ENV42_HEADER_BITS = 2                    # header field, 0..3
ENV42_PAYLOAD_BITS = 40                  # 2**39 < 10**12 <= 2**40
ENV42_TOTAL_BITS = ENV42_HEADER_BITS + ENV42_PAYLOAD_BITS      # 42
ENV42_OCTAL_DIGITS = ENV42_TOTAL_BITS // 3                     # 14

ENV36_BITS = 36                          # HCM-native frame
ENV36_OCTAL_DIGITS = ENV36_BITS // 3     # 12


class ShellAddrError(ValueError):
    """Raised on a refused kinematic derivation, a refused reordering, a
    lossy envelope presented as lossless, a decimal string parsed as
    octal, an out-of-range field, or a retrofitted header semantics."""


class EnvelopeClass(Enum):
    DECIMAL_PRESERVING_42 = "DECIMAL_PRESERVING_42_BIT"
    HCM_NATIVE_36 = "HCM_NATIVE_36_BIT"
    MIXED_RADIX_7 = "MIXED_RADIX_SEVEN_FIELD"
    NEGATIVE_CONTROL = "NEGATIVE_CONTROL"


class LossClass(Enum):
    LOSSLESS = "LOSSLESS"
    LOSSY = "LOSSY"


class TimestampClass(Enum):
    PRESENT = "TIMESTAMPS_PRESENT"
    MISSING = "TIMESTAMPS_MISSING"


class OrderClass(Enum):
    CANDIDATE = "CANDIDATE_ORDER"
    ESTABLISHED = "CLOCK_ESTABLISHED_ORDER"


# =======================================================================
# Part 1 -- the moving shell sequence
# =======================================================================

@dataclass(frozen=True)
class ShellObservation:
    """One reported range to a moving shell.

    ``timestamp`` is ``None`` and that ``None`` is load-bearing: the
    exact times are MISSING, and the record says so explicitly rather
    than leaving the field out and letting a reader assume it was never
    relevant."""

    obs_id: str
    range_miles: Fraction
    timestamp: object | None = None
    candidate_index: int = 0

    @property
    def range_km(self) -> Fraction:
        return miles_to_km(self.range_miles)

    @property
    def radius_earth_radii(self) -> Fraction:
        return radius_in_earth_radii(self.range_miles)


#: The three reported ranges, in the CANDIDATE order in which they were
#: given: one object, moving closer to Earth. Public neutral alias.
MOVING_SHELL_SEQUENCE_A = (
    ShellObservation("SHELL_A_OBS_1", Fraction(3478), None, 0),
    ShellObservation("SHELL_A_OBS_2", Fraction(1903), None, 1),
    ShellObservation("SHELL_A_OBS_3", Fraction(1238), None, 2),
)

#: Explicitly retained: there are no timestamps.
SHELL_TIMESTAMPS = None
SHELL_TIMESTAMP_CLASS = TimestampClass.MISSING
SHELL_ORDER_CLASS = OrderClass.CANDIDATE


def miles_to_km(miles) -> Fraction:
    """Exact mile -> kilometre conversion. 1 mile = 1.609344 km."""
    return Fraction(miles) * MILE_KM


def km_to_miles(km) -> Fraction:
    """Exact inverse of :func:`miles_to_km`."""
    return Fraction(km) / MILE_KM


def radius_in_earth_radii(miles) -> Fraction:
    """Geocentric radius in Earth radii for a range read as an altitude.

    The reference radii are ``1 + range / R_E``: the reported range is
    read as a height above the surface, so the radius is the surface
    plus that height. That reading is a DECLARED interpretation of the
    reported numbers, not a measured geometry, and it is the reading
    under which the reference values reproduce exactly."""
    return 1 + Fraction(miles) / EARTH_RADIUS_MI


def altitude_in_earth_radii(miles) -> Fraction:
    """The height component alone, in Earth radii."""
    return Fraction(miles) / EARTH_RADIUS_MI


def observation_table(sequence=MOVING_SHELL_SEQUENCE_A) -> list:
    """Render the sequence with exact conversions and float renderings."""
    rows = []
    for obs in sequence:
        rows.append({
            "obs_id": obs.obs_id,
            "candidate_index": obs.candidate_index,
            "range_miles": float(obs.range_miles),
            "range_km_exact": str(obs.range_km),
            "range_km": float(obs.range_km),
            "radius_earth_radii_exact": str(obs.radius_earth_radii),
            "radius_earth_radii": float(obs.radius_earth_radii),
            "timestamp": obs.timestamp,
            "timestamp_class": SHELL_TIMESTAMP_CLASS.value,
        })
    return rows


def is_ordered_inward(sequence=MOVING_SHELL_SEQUENCE_A) -> bool:
    """True iff each reported range is strictly smaller than the last."""
    ranges = [o.range_miles for o in sequence]
    return all(a > b for a, b in zip(ranges, ranges[1:]))


def sequence_record(sequence=MOVING_SHELL_SEQUENCE_A) -> dict:
    """The retained sequence: ordered inward, timestamps explicitly None.

    This is everything the readings support. There is no derived rate,
    no fitted trajectory and no projected arrival, because none of those
    exist without a clock."""
    return {
        "sequence_id": "MOVING_SHELL_SEQUENCE_A",
        "observations": observation_table(sequence),
        "ordered_inward": is_ordered_inward(sequence),
        "order_class": SHELL_ORDER_CLASS.value,
        "timestamps": SHELL_TIMESTAMPS,             # explicitly None
        "timestamp_class": SHELL_TIMESTAMP_CLASS.value,
        "mile_km_exact": str(MILE_KM),
        "earth_radius_mi": str(EARTH_RADIUS_MI),
        "earth_radius_km": str(EARTH_RADIUS_KM),
        "derived_kinematics": None,
        "retained_because": (
            "the three readings are a faithful record of what was "
            "reported; the record is retained in full and nothing is "
            "derived from it that the missing clock does not license"),
    }


def reference_radius_check(sequence=MOVING_SHELL_SEQUENCE_A) -> dict:
    """Do the reference km and R_E values reproduce, and with which R_E?

    Reports both the R_E that reproduces (3958.7613 mi) and the rounded
    6371.0 km that does not, so the choice is auditable rather than
    silent."""
    references = {
        3478: (5597.298432, 1.8785576437760974),
        1903: (3062.581632, 1.4807059218245868),
        1238: (1992.367872, 1.3127240836672824),
    }
    rows = []
    for obs in sequence:
        miles = int(obs.range_miles)
        ref_km, ref_re = references[miles]
        got_km = float(obs.range_km)
        got_re = float(obs.radius_earth_radii)
        rounded_re = float(1 + obs.range_km / EARTH_RADIUS_KM_ROUNDED)
        rows.append({
            "range_miles": miles,
            "reference_km": ref_km,
            "computed_km": got_km,
            "km_matches": abs(got_km - ref_km) < RADIUS_TOLERANCE,
            "reference_earth_radii": ref_re,
            "computed_earth_radii": got_re,
            "earth_radii_matches": abs(got_re - ref_re) < RADIUS_TOLERANCE,
            "rounded_6371_earth_radii": rounded_re,
            "rounded_6371_matches": abs(rounded_re - ref_re)
            < RADIUS_TOLERANCE,
        })
    return {
        "rows": rows,
        "earth_radius_used_mi": str(EARTH_RADIUS_MI),
        "earth_radius_used_km": str(EARTH_RADIUS_KM),
        "all_km_match": all(r["km_matches"] for r in rows),
        "all_earth_radii_match": all(r["earth_radii_matches"]
                                     for r in rows),
        "rounded_6371_reproduces": all(r["rounded_6371_matches"]
                                       for r in rows),
        "tolerance": RADIUS_TOLERANCE,
        "note": (
            "R_E = 3958.7613 mi = 6371.0087455872 km reproduces every "
            "reference radius to better than 1e-9; a rounded 6371.0 km "
            "does not, missing by about 1.2e-6. The reproducing value "
            "is the one asserted throughout"),
    }


# --- the kinematic refusals --------------------------------------------

def refuse_speed(*_args, **_kwargs) -> None:
    """Refuse a speed. There is no time difference to divide by.

    Speed is (range difference) / (time difference). The ranges are
    reported; the times are MISSING. Choosing an interval -- an hour, a
    minute, "the gap between sightings" -- does not estimate the speed,
    it invents the denominator, and the quotient would then look like a
    measurement of the object rather than a restatement of the guess."""
    raise ShellAddrError(
        "refused: no speed. Speed is a range difference divided by a "
        "time difference, and the exact times of the three readings are "
        "MISSING. There is no denominator to divide by -- not a wide "
        "one, none -- so any velocity would come entirely from an "
        "assumed interval and would be an invention wearing the "
        "appearance of a measurement.")


def refuse_orbit(*_args, **_kwargs) -> None:
    """Refuse an orbit. Three untimed radii determine no trajectory."""
    raise ShellAddrError(
        "refused: no orbit. An orbit requires position and velocity, or "
        "three positions with their times. With the clock removed, an "
        "infinite family of trajectories passes through these three "
        "radii -- a slow descent over weeks and a hypersonic pass in "
        "minutes fit the readings equally well -- and nothing in the "
        "data distinguishes them. No orbital element, period, "
        "inclination or eccentricity is derivable.")


def refuse_eta(*_args, **_kwargs) -> None:
    """Refuse an arrival time. It is a refused speed, extrapolated."""
    raise ShellAddrError(
        "refused: no arrival time. An ETA is a speed projected forward, "
        "so it inherits the missing denominator and then compounds it "
        "with an assumed continuation of the trend. The readings do not "
        "say the approach continues, or at what rate, or whether the "
        "object arrives at all.")


def refuse_reordering(sequence=MOVING_SHELL_SEQUENCE_A,
                      proposed_order=None) -> None:
    """Refuse a silent permutation of the observation order.

    The three ranges are a CANDIDATE order -- the order in which they
    were reported, not an order a clock established. A model that fits
    better under some permutation has not found a better fit; it has
    selected its data. Any re-ordering must be an explicit, externally
    justified event, not a convenience inside a fit."""
    raise ShellAddrError(
        "refused: the observation order is a CANDIDATE order, recorded "
        "as reported and not established by any clock. It may not be "
        "silently permuted to improve a model's fit: choosing the "
        "permutation that fits is choosing the data. A re-ordering "
        f"(proposed: {proposed_order!r}) must be an explicit, "
        "externally justified event with its own record.")


# =======================================================================
# Part 2 -- the compressed binary-to-octal address
# =======================================================================

#: The raw decimal address, preserved exactly. Public neutral alias.
CANDIDATE_VECTOR_A = 344478312553
CANDIDATE_VECTOR_A_BIT_LENGTH = 39
CANDIDATE_VECTOR_A_OCTAL = "5006440364151"
CANDIDATE_VECTOR_A_BINARY = "101000000110100100000011110100001101001"


def vector_consistency(value: int = CANDIDATE_VECTOR_A, *,
                       bit_length: int = CANDIDATE_VECTOR_A_BIT_LENGTH,
                       octal: str = CANDIDATE_VECTOR_A_OCTAL,
                       binary: str = CANDIDATE_VECTOR_A_BINARY) -> dict:
    """Check the decimal, bit length, octal and binary all agree.

    Four renderings of one integer. They are relabelings of each other,
    so agreement is a consistency check on the record, not evidence
    about content."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ShellAddrError("vector must be a plain int")
    if value < 0:
        raise ShellAddrError("vector must be non-negative")
    computed_octal = format(value, "o")
    computed_binary = format(value, "b")
    return {
        "decimal": value,
        "decimal_digits": len(str(value)),
        "bit_length": value.bit_length(),
        "bit_length_matches": value.bit_length() == bit_length,
        "octal": computed_octal,
        "octal_matches": computed_octal == octal,
        "binary": computed_binary,
        "binary_matches": computed_binary == binary,
        "octal_round_trip": int(octal, 8) == value,
        "binary_round_trip": int(binary, 2) == value,
        "all_consistent": (value.bit_length() == bit_length
                           and computed_octal == octal
                           and computed_binary == binary
                           and int(octal, 8) == value
                           and int(binary, 2) == value),
        "fits_40_bit_payload": value < (1 << ENV42_PAYLOAD_BITS),
        "fits_12_decimal_digits": value < DECIMAL_MODULUS,
    }


# --- octal hygiene: 8 and 9 are not octal symbols ----------------------

def refuse_decimal_digits_as_octal(s: str) -> None:
    """Refuse to read a decimal string as octal when it cannot be one.

    Base 8 has the symbols 0..7. A string containing 8 or 9 has no
    octal value whatever; parsing it as octal is not a lenient reading,
    it is a category error that silently produces a different number.
    This is the R10.6 lesson restated: "unpack from base 10" is not
    "read the digits as octal"."""
    if not isinstance(s, str):
        raise ShellAddrError("octal candidate must be a string")
    bad = sorted({c for c in s if c in "89"})
    if bad:
        raise ShellAddrError(
            f"refused: {s!r} contains the decimal digit(s) "
            f"{','.join(bad)}, which are not octal symbols. Base 8 has "
            f"only 0..7, so this string has no octal value at all. "
            f"Reading it as octal would quietly yield a different "
            f"number and present it as the same one.")
    for c in s:
        if c not in "01234567":
            raise ShellAddrError(
                f"refused: {s!r} contains {c!r}, which is not an octal "
                f"symbol")


def parse_octal(s: str) -> int:
    """Parse an octal string, refusing 8 and 9 explicitly first."""
    refuse_decimal_digits_as_octal(s)
    if not s:
        raise ShellAddrError("empty octal string")
    return int(s, 8)


# --- envelope 1: 42-bit decimal-preserving, 14 octal digits ------------

def encode_envelope42(value: int, header: int = 0) -> str:
    """Pack a 12-digit decimal into 2 header bits + 40 payload bits.

    Forty bits suffice for a twelve-digit decimal because
    ``2**39 < 10**12 <= 2**40``. With the two header bits above them the
    frame is 42 bits, which is exactly fourteen octal digits (14*3=42),
    so the serialization is a whole number of octal symbols with no
    padding and no ambiguity. Exactly inverted by
    :func:`decode_envelope42`."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ShellAddrError("value must be a plain int")
    if not isinstance(header, int) or isinstance(header, bool):
        raise ShellAddrError("header must be a plain int")
    if not 0 <= value < DECIMAL_MODULUS:
        raise ShellAddrError(
            f"value {value} outside the 12-digit range [0, 10**12)")
    if not 0 <= header < (1 << ENV42_HEADER_BITS):
        raise ShellAddrError(
            f"header {header} outside 0..{(1 << ENV42_HEADER_BITS) - 1}")
    code = (header << ENV42_PAYLOAD_BITS) | value
    return format(code, f"0{ENV42_OCTAL_DIGITS}o")


def decode_envelope42(octal_string: str) -> tuple:
    """Invert :func:`encode_envelope42`: (header, value). Exact."""
    if not isinstance(octal_string, str):
        raise ShellAddrError("envelope must be a string")
    if len(octal_string) != ENV42_OCTAL_DIGITS:
        raise ShellAddrError(
            f"42-bit envelope must be exactly {ENV42_OCTAL_DIGITS} "
            f"octal digits, got {len(octal_string)}")
    code = parse_octal(octal_string)
    if code >= (1 << ENV42_TOTAL_BITS):
        raise ShellAddrError("envelope exceeds 42 bits")
    header = code >> ENV42_PAYLOAD_BITS
    value = code & ((1 << ENV42_PAYLOAD_BITS) - 1)
    if value >= DECIMAL_MODULUS:
        raise ShellAddrError(
            f"payload {value} is a valid 40-bit pattern but not a "
            f"12-digit decimal; the 40-bit space is larger than 10**12")
    return header, value


def envelope42_account(value: int = CANDIDATE_VECTOR_A,
                       header: int = 0) -> dict:
    """The 42-bit envelope, with its exactness stated and bounded."""
    serialized = encode_envelope42(value, header)
    back_header, back_value = decode_envelope42(serialized)
    return {
        "envelope_class": EnvelopeClass.DECIMAL_PRESERVING_42.value,
        "loss_class": LossClass.LOSSLESS.value,
        "header_bits": ENV42_HEADER_BITS,
        "payload_bits": ENV42_PAYLOAD_BITS,
        "total_bits": ENV42_TOTAL_BITS,
        "octal_digits": ENV42_OCTAL_DIGITS,
        "octal_digits_exact": ENV42_OCTAL_DIGITS * 3 == ENV42_TOTAL_BITS,
        "serialized": serialized,
        "serialized_length": len(serialized),
        "bits_required": max(1, value.bit_length()),
        "bits_available": ENV42_PAYLOAD_BITS,
        "bits_lost": 0,
        "round_trip": (back_header == header and back_value == value),
        "why_40_bits": "2**39 < 10**12 <= 2**40",
        "lower_holds": 2 ** 39 < DECIMAL_MODULUS,
        "upper_holds": DECIMAL_MODULUS <= 2 ** ENV42_PAYLOAD_BITS,
        "what_the_round_trip_proves": (
            "that the frame is faithful; a reversible envelope "
            "relocates information and never creates it, so an exact "
            "round-trip is necessary but never sufficient to claim the "
            "address has been decoded"),
    }


# --- envelope 2: 36-bit HCM-native, 12 octal digits, LOSSY -------------

def envelope36_loss_account(value: int = CANDIDATE_VECTOR_A) -> dict:
    """Account, explicitly, for what a 36-bit frame throws away.

    Twelve octal digits are 36 bits. The address needs 39. The three
    most significant bits do not fit and are truncated, so 2**3 = 8
    distinct addresses share every surviving code: the frame is not a
    compression of the address, it is a partial erasure of it."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ShellAddrError("value must be a plain int")
    if value < 0:
        raise ShellAddrError("value must be non-negative")
    required = max(1, value.bit_length())
    bits_lost = max(0, required - ENV36_BITS)
    kept = value & ((1 << ENV36_BITS) - 1)
    truncated_high = value >> ENV36_BITS
    return {
        "envelope_class": EnvelopeClass.HCM_NATIVE_36.value,
        "loss_class": (LossClass.LOSSY.value if bits_lost
                       else LossClass.LOSSLESS.value),
        "total_bits": ENV36_BITS,
        "octal_digits": ENV36_OCTAL_DIGITS,
        "octal_digits_exact": ENV36_OCTAL_DIGITS * 3 == ENV36_BITS,
        "bits_required": required,
        "bits_available": ENV36_BITS,
        "bits_lost": bits_lost,
        "truncated_high_bits_value": truncated_high,
        "truncated_high_bits_binary": (format(truncated_high, "b")
                                       if bits_lost else ""),
        "retained_value": kept,
        "aliasing_factor": 1 << bits_lost,
        "exact_round_trip": bits_lost == 0,
        "what_is_truncated": (
            f"the {bits_lost} most significant bit(s) of the address; "
            f"{1 << bits_lost} distinct addresses collide onto each "
            f"surviving 36-bit code" if bits_lost else
            "nothing; the value already fits in 36 bits"),
    }


def encode_envelope36(value: int = CANDIDATE_VECTOR_A) -> str:
    """Serialize the low 36 bits as twelve octal digits.

    This is a TRUNCATION, not an encoding. It is provided so the loss
    can be measured rather than assumed away; see
    :func:`envelope36_loss_account`, and note that
    :func:`refuse_lossy_as_lossless` blocks presenting the result as a
    faithful address."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ShellAddrError("value must be a plain int")
    if value < 0:
        raise ShellAddrError("value must be non-negative")
    return format(value & ((1 << ENV36_BITS) - 1), f"0{ENV36_OCTAL_DIGITS}o")


def decode_envelope36(octal_string: str) -> int:
    """Read twelve octal digits back. Recovers the retained bits only."""
    if not isinstance(octal_string, str):
        raise ShellAddrError("envelope must be a string")
    if len(octal_string) != ENV36_OCTAL_DIGITS:
        raise ShellAddrError(
            f"36-bit envelope must be exactly {ENV36_OCTAL_DIGITS} "
            f"octal digits, got {len(octal_string)}")
    return parse_octal(octal_string)


def refuse_lossy_as_lossless(value: int = CANDIDATE_VECTOR_A,
                             *_args, **_kwargs) -> None:
    """Refuse to present a truncated 36-bit frame as a faithful one.

    Thirty-six bits cannot hold thirty-nine. Calling the truncated
    result "the address in HCM-native form" would make an erasure look
    like a compression, and the missing high bits would never be
    noticed because the twelve surviving octal digits read perfectly
    well. State the loss or do not use the frame."""
    account = envelope36_loss_account(value)
    if account["bits_lost"] == 0:
        raise ShellAddrError(
            "refused: this refusal is for the LOSSY case; the value "
            "already fits in 36 bits, so the claim under test does not "
            "arise. Use envelope36_loss_account to state that.")
    raise ShellAddrError(
        f"refused: the {ENV36_BITS}-bit envelope is LOSSY for this "
        f"address and may not be presented as lossless. The address "
        f"needs {account['bits_required']} bits, the frame holds "
        f"{ENV36_BITS}, and {account['bits_lost']} high bit(s) are "
        f"truncated -- {account['aliasing_factor']} distinct addresses "
        f"collide onto each surviving code. The twelve octal digits "
        f"still read perfectly well, which is exactly why the loss must "
        f"be stated rather than left to be noticed.")


# --- envelope 3: seven-field mixed-radix address -----------------------

#: Seven declared fields, most significant first, each with its radix.
#: The seventh field (``revision``) is this module's own addition, so
#: the layout is a declared construction and not a decoded one.
MIXED_RADIX_FIELDS = (
    ("shell", 8),                # which shell
    ("face", 6),                 # which face of the frame
    ("local_coord", 67108864),   # face-local coordinates, 8192 x 8192
    ("phase", 4),                # phase quarter
    ("epoch_class", 3),          # epoch class
    ("parity", 2),               # parity bit
    ("revision", 16),            # layout revision (this module's field)
)

MIXED_RADIX_FIELD_NAMES = tuple(name for name, _ in MIXED_RADIX_FIELDS)


def mixed_radix_capacity(fields=MIXED_RADIX_FIELDS) -> int:
    """The number of distinct addresses the declared layout can hold."""
    total = 1
    for _name, radix in fields:
        total *= radix
    return total


def mixed_radix_encode(values, fields=MIXED_RADIX_FIELDS) -> int:
    """Pack declared fields into one integer, most significant first."""
    vals = tuple(values)
    if len(vals) != len(fields):
        raise ShellAddrError(
            f"expected {len(fields)} fields, got {len(vals)}")
    code = 0
    for (name, radix), v in zip(fields, vals):
        if not isinstance(v, int) or isinstance(v, bool):
            raise ShellAddrError(f"field {name!r} must be a plain int")
        if not 0 <= v < radix:
            raise ShellAddrError(
                f"field {name!r} value {v} outside 0..{radix - 1}")
        code = code * radix + v
    return code


def mixed_radix_decode(code: int, fields=MIXED_RADIX_FIELDS) -> tuple:
    """Invert :func:`mixed_radix_encode`. Exact."""
    if not isinstance(code, int) or isinstance(code, bool):
        raise ShellAddrError("code must be a plain int")
    capacity = mixed_radix_capacity(fields)
    if not 0 <= code < capacity:
        raise ShellAddrError(
            f"code {code} outside the layout capacity 0..{capacity - 1}")
    out = []
    rest = code
    for _name, radix in reversed(fields):
        out.append(rest % radix)
        rest //= radix
    return tuple(reversed(out))


def mixed_radix_named(code: int, fields=MIXED_RADIX_FIELDS) -> dict:
    """Decode into a name -> value mapping."""
    vals = mixed_radix_decode(code, fields)
    return {name: v for (name, _radix), v in zip(fields, vals)}


def mixed_radix_account(value: int = CANDIDATE_VECTOR_A,
                        fields=MIXED_RADIX_FIELDS) -> dict:
    """The seven-field view of an address, with its round-trip stated."""
    capacity = mixed_radix_capacity(fields)
    if not 0 <= value < capacity:
        raise ShellAddrError(
            f"value {value} does not fit the declared layout "
            f"(capacity {capacity})")
    decoded = mixed_radix_decode(value, fields)
    return {
        "envelope_class": EnvelopeClass.MIXED_RADIX_7.value,
        "loss_class": LossClass.LOSSLESS.value,
        "fields": [{"name": n, "radix": r, "value": v}
                   for (n, r), v in zip(fields, decoded)],
        "field_count": len(fields),
        "capacity": capacity,
        "value": value,
        "round_trip": mixed_radix_encode(decoded, fields) == value,
        "bits_lost": 0,
        "layout_is_declared_not_decoded": True,
        "note": (
            "the field names and radices are DECLARED by this module. "
            "An exact round-trip shows the layout is faithful; it says "
            "nothing about whether the address is organised this way"),
    }


# --- envelope 4: negative controls -------------------------------------

def bcd_encode(value: int, width: int = DECIMAL_WIDTH) -> str:
    """Binary-coded decimal: four bits per decimal digit.

    A negative control. BCD is exactly reversible and uses 48 bits for
    a twelve-digit number where 40 suffice -- it is *wider* than the
    packed form and carries exactly the same information. Width is not
    content, and neither is narrowness."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ShellAddrError("value must be a plain int")
    if not 0 <= value < 10 ** width:
        raise ShellAddrError(f"value outside the {width}-digit range")
    return "".join(format(int(c), "04b") for c in str(value).zfill(width))


def bcd_decode(bits: str, width: int = DECIMAL_WIDTH) -> int:
    """Invert :func:`bcd_encode`."""
    if not isinstance(bits, str):
        raise ShellAddrError("BCD must be a string")
    if len(bits) != width * 4:
        raise ShellAddrError(f"BCD must be {width * 4} bits")
    digits = []
    for i in range(0, len(bits), 4):
        chunk = bits[i:i + 4]
        if any(c not in "01" for c in chunk):
            raise ShellAddrError("BCD must be binary")
        nib = int(chunk, 2)
        if nib > 9:
            raise ShellAddrError(f"invalid BCD nibble {nib}")
        digits.append(str(nib))
    return int("".join(digits))


def reverse_control(value: int, width: int = DECIMAL_WIDTH) -> str:
    """Reverse the zero-padded decimal digit string.

    A negative control, and an involution: reversing twice returns the
    original string. It is perfectly reversible and completely empty --
    which is the point. Reversibility is a property of the frame, and
    frames that reveal nothing round-trip just as cleanly as frames
    that might."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ShellAddrError("value must be a plain int")
    if not 0 <= value < 10 ** width:
        raise ShellAddrError(f"value outside the {width}-digit range")
    return str(value).zfill(width)[::-1]


def reverse_control_invert(s: str) -> int:
    """Invert :func:`reverse_control`."""
    if not isinstance(s, str) or not s.isdigit():
        raise ShellAddrError("reversal control expects a digit string")
    return int(s[::-1])


def negative_control_account(value: int = CANDIDATE_VECTOR_A) -> dict:
    """Both controls round-trip exactly and both mean nothing."""
    bcd = bcd_encode(value)
    rev = reverse_control(value)
    return {
        "envelope_class": EnvelopeClass.NEGATIVE_CONTROL.value,
        "bcd_bits": len(bcd),
        "bcd_round_trip": bcd_decode(bcd) == value,
        "bcd_is_wider_than_packed": len(bcd) > ENV42_PAYLOAD_BITS,
        "reversal": rev,
        "reversal_round_trip": reverse_control_invert(rev) == value,
        "reversal_is_involution": (
            reverse_control(reverse_control_invert(rev)) == rev),
        "loss_class": LossClass.LOSSLESS.value,
        "why_controls": (
            "both are exactly reversible and neither exposes anything. "
            "They calibrate what a clean round-trip is worth: nothing "
            "on its own"),
    }


# --- no retrofit: header semantics come from holdouts, not the target --

def synthetic_holdout_vectors(count: int = 8, *,
                              seed: str = "R11_SHELLADDR_HOLDOUT") -> tuple:
    """Deterministic SYNTHETIC 12-digit vectors for testing a header rule.

    Generated by hashing a fixed seed, so they are reproducible and are
    demonstrably not the target: a header semantics worth anything must
    predict on these before it is applied to the address of interest."""
    if count < 1:
        raise ShellAddrError("count must be >= 1")
    out = []
    for i in range(count):
        digest = hashlib.sha256(f"{seed}\x1f{i}".encode()).hexdigest()
        out.append(int(digest, 16) % DECIMAL_MODULUS)
    return tuple(out)


def refuse_header_semantics_from_target(*_args, **_kwargs) -> None:
    """Refuse a header meaning read off the target vector.

    A two-bit header has four states. Any story about what those states
    mean, derived by looking at the one address the story was built to
    explain, is fitted rather than tested -- it cannot fail, because it
    was chosen after the answer was seen. Header semantics must be
    frozen first and confirmed on SYNTHETIC holdouts
    (:func:`synthetic_holdout_vectors`), which the target is not."""
    raise ShellAddrError(
        "refused: no header semantics from the target vector. A header "
        "meaning inferred by inspecting the one address it was built to "
        "explain is retrofitted, not tested: it was selected after the "
        "answer was seen and so cannot fail. Freeze the semantics "
        "first, then confirm them on SYNTHETIC holdouts "
        "(synthetic_holdout_vectors), which the target is not. Until "
        "then the header is a field with a width and no meaning.")


# --- fingerprint -------------------------------------------------------

def address_fingerprint(value: int = CANDIDATE_VECTOR_A,
                        header: int = 0) -> str:
    """A stable hash over the reversible views, for an audit trail."""
    parts = (
        str(value),
        format(value, "o"),
        format(value, "b"),
        encode_envelope42(value, header),
        encode_envelope36(value),
        str(mixed_radix_decode(value)),
    )
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


# --- the report --------------------------------------------------------

def shelladdr_report() -> dict:
    return {
        "what_this_is": (
            "three reported ranges of one inward-moving shell, retained "
            "with their timestamps explicitly MISSING, plus a set of "
            "reversible and lossy envelopes over one twelve-digit "
            "address"),
        "shell_sequence": sequence_record(),
        "reference_radius_check": reference_radius_check(),
        "earth_radius_mi": str(EARTH_RADIUS_MI),
        "earth_radius_km": str(EARTH_RADIUS_KM),
        "mile_km": str(MILE_KM),
        "vector_consistency": vector_consistency(),
        "envelope_42_bit": envelope42_account(),
        "envelope_36_bit": envelope36_loss_account(),
        "mixed_radix": mixed_radix_account(),
        "negative_controls": negative_control_account(),
        "refusals": [
            "refuse_speed", "refuse_orbit", "refuse_eta",
            "refuse_reordering", "refuse_lossy_as_lossless",
            "refuse_decimal_digits_as_octal",
            "refuse_header_semantics_from_target",
        ],
        "evidence_class": "SOURCE_CLAIM retained + DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "MOVING_SHELL_SEQUENCE_RETAINED_WITHOUT_KINEMATICS",
        "what_this_does_not_say": (
            "It does not say the three readings are false, and it does "
            "not say nothing was moving. It says three ranges with "
            "MISSING timestamps carry no speed, no orbit and no arrival "
            "time -- speed needs a time difference to divide by, and "
            "there is none -- so any such number would be manufactured "
            "from an assumed interval and would then look like a "
            "measurement. The reported order is a CANDIDATE order and "
            "is not permuted to suit a model. On the address side, it "
            "does not say the twelve-digit value is meaningless and it "
            "does not say no encoding exists; it says a reversible "
            "envelope RELOCATES information and never CREATES it, so an "
            "exact round-trip is necessary but never sufficient to "
            "claim a decoding, and a 36-bit frame that drops three bits "
            "of a 39-bit address is an erasure that must be accounted "
            "for rather than presented as compression. Header meanings "
            "are not read off the target. Nothing here is measured and "
            "no physical validation is claimed."),
    }
