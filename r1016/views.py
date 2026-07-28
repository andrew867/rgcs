"""R10.16 — the five declared numeric views.

A wire is a decimal string ``16 | payload | terminal``. Before any
projection can be attempted, the wire has to be turned into a 30-bit
word for the frozen F5|Q22|S3 packet parser. There is more than one
defensible way to do that, so ALL of them are enumerated and ranked by
anchor fit -- never chosen by how the resulting place name reads.

  A  PAYLOAD_OCTAL      payload digits read as OCTAL digits
  B  FULL_WIRE_OCTAL    whole wire read as OCTAL digits
  C  PAYLOAD_PLUS_TERM  payload+terminal digits read as DECIMAL
  D  WINDOW_FULL_30     sliding 30-bit windows over int(full wire)
  E  WINDOW_PAYLOAD_30  sliding 30-bit windows over int(payload)

Views A and B require every digit to be <= 7; a wire containing an 8
or a 9 has no octal reading and the view REFUSES for that wire rather
than silently dropping or remapping the digit.
"""

from __future__ import annotations

#: "Payload-octal" has TWO defensible senses and both are run, because
#: choosing one silently would be an unrecorded modelling decision:
#:
#:   *_DIGITS  read the DECIMAL DIGIT STRING as octal digits. Exact,
#:             but undefined whenever a digit is 8 or 9.
#:   *_INT     take the decimal INTEGER and let the frozen parser read
#:             its 30-bit value as ten octal digits. Always defined.
#:
#: The first sense is what "read it in octal" means lexically; the
#: second is what the frozen F5|Q22|S3 parser actually does. They are
#: different operations and are ranked separately.
VIEW_IDS = ("A_PAYLOAD_OCTAL_DIGITS", "A2_PAYLOAD_INT",
            "B_FULL_WIRE_OCTAL_DIGITS", "B2_FULL_WIRE_INT",
            "C_PAYLOAD_PLUS_TERMINAL", "D_WINDOW_FULL_30",
            "E_WINDOW_PAYLOAD_30")

MASK30 = (1 << 30) - 1


class ViewError(ValueError):
    pass


def split(wire: str) -> tuple[str, str, str]:
    """'16' | payload | terminal."""
    s = str(wire).strip()
    if not s.isdigit():
        raise ViewError(f"wire {wire!r} is not decimal digits")
    if not s.startswith("16") or len(s) < 4:
        raise ViewError(f"wire {s} is not a 16-headed wire")
    return s[:2], s[2:-1], s[-1]


def _octal_value(digits: str):
    if any(c in "89" for c in digits):
        return None                      # no octal reading exists
    return int(digits, 8)


def candidates(wire: str) -> list[dict]:
    """Every (view, window) candidate 30-bit word for one wire."""
    head, payload, terminal = split(wire)
    out: list[dict] = []

    v = _octal_value(payload)
    if v is None:
        out.append({"view": "A_PAYLOAD_OCTAL_DIGITS", "window": None,
                    "word": None,
                    "refusal": "payload contains an 8 or 9; it has no "
                               "octal reading and is not remapped"})
    elif v <= MASK30:
        out.append({"view": "A_PAYLOAD_OCTAL_DIGITS", "window": None,
                    "word": v})
    else:
        out.append({"view": "A_PAYLOAD_OCTAL_DIGITS", "window": None,
                    "word": None,
                    "refusal": f"octal payload {v} exceeds 30 bits and "
                               "is never truncated"})

    v = _octal_value(str(wire))
    if v is None:
        out.append({"view": "B_FULL_WIRE_OCTAL_DIGITS", "window": None,
                    "word": None,
                    "refusal": "wire contains an 8 or 9; no octal "
                               "reading"})
    elif v <= MASK30:
        out.append({"view": "B_FULL_WIRE_OCTAL_DIGITS", "window": None,
                    "word": v})
    else:
        out.append({"view": "B_FULL_WIRE_OCTAL_DIGITS", "window": None,
                    "word": None,
                    "refusal": f"octal wire {v} exceeds 30 bits and is "
                               "never truncated"})

    # A2 / B2: the INTEGER senses, always defined
    for vid, value in (("A2_PAYLOAD_INT", int(payload)),
                       ("B2_FULL_WIRE_INT", int(wire))):
        out.append({"view": vid, "window": None,
                    "word": value if value <= MASK30 else None,
                    **({} if value <= MASK30 else
                       {"refusal": f"{value} exceeds 30 bits and is "
                                   "never truncated"})})

    v = int(payload + terminal)
    out.append({"view": "C_PAYLOAD_PLUS_TERMINAL", "window": None,
                "word": v if v <= MASK30 else None,
                **({} if v <= MASK30 else
                   {"refusal": f"{v} exceeds 30 bits"})})

    for view_id, source in (("D_WINDOW_FULL_30", int(wire)),
                            ("E_WINDOW_PAYLOAD_30", int(payload))):
        bits = source.bit_length()
        if bits < 30:
            out.append({"view": view_id, "window": None, "word": None,
                        "refusal": f"integer is only {bits} bits; no "
                                   "30-bit window exists"})
            continue
        for shift in range(0, bits - 30 + 1):
            out.append({"view": view_id, "window": shift,
                        "word": (source >> shift) & MASK30})
    return out


def usable(wire: str) -> list[dict]:
    return [c for c in candidates(wire) if c.get("word") is not None]
