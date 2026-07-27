"""R10.9 T11 finite candidate recovery (Phase 4, R109-PKT-05).

The refined 11-octal-digit family uses an interleave that is similar to
but different from T10, and the exact permutation is NOT known. This
module therefore does the only honest thing: it declares a FINITE,
bounded candidate space, tests every candidate against the training
constraints on BOTH parent-child pairs, symmetry-reduces duplicates,
and reports every survivor as an alias. No candidate is promoted to
production authority for fitting one pair; no named-location special
case exists anywhere in the evaluation (the constraint checker takes
arbitrary (refined, compact) pairs).

Declared bounded space
======================

Frame: the 33-bit zero-padded binary of the wire value (11 octal
digits). The four semantic fields F5(5) + Q22(22) + C3(3) + S3(3) sum
to exactly 33 bits, so the space is:

- ``FIELD_ORDER_*``: all 24 contiguous orderings of (F, Q, C, S) in
  the 33-bit frame;
- ``OCTAL_DELETE_k``: the 11 digit-deletion models (refined octal =
  compact octal with one inserted octal digit at position k, the
  inserted digit being the child);
- ``COMPACT_SHIFT_k``: refined = compact word shifted left by 3 with
  the child inserted as the k-th 3-bit group boundary (k in 0..10),
  i.e. bit-level insertion of one octal group.

Anything outside this space is out of scope for this phase and stays
UNRESOLVED rather than invented.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from r109.types import CodecTypeError, CompactAddress, RefinedAddress, WireAddress

FRAME_BITS = 33
FIELDS = {"F": 5, "Q": 22, "C": 3, "S": 3}


@dataclass(frozen=True)
class T11Candidate:
    """One fully declared candidate transform."""

    candidate_id: str
    kind: str                      # FIELD_ORDER | OCTAL_DELETE | COMPACT_SHIFT
    spec: tuple                    # kind-specific parameters
    assumptions: str

    # ---------------------------------------------------------- decode
    def decode(self, raw: int) -> RefinedAddress | None:
        """Return a RefinedAddress, or None if the candidate cannot
        represent this word (an honest structural failure)."""
        if raw < (1 << 30) or raw >= (1 << FRAME_BITS):
            raise CodecTypeError("T11 candidates take 31..33-bit words only")
        if self.kind == "FIELD_ORDER":
            return self._decode_field_order(raw)
        if self.kind == "OCTAL_DELETE":
            return self._decode_octal_delete(raw)
        if self.kind == "COMPACT_SHIFT":
            return self._decode_compact_shift(raw)
        raise CodecTypeError(f"unknown candidate kind {self.kind}")

    def _decode_field_order(self, raw: int) -> RefinedAddress | None:
        bits = format(raw, f"0{FRAME_BITS}b")
        pos = 0
        got: dict[str, str] = {}
        for name in self.spec:
            got[name] = bits[pos:pos + FIELDS[name]]
            pos += FIELDS[name]
        f5 = int(got["F"], 2)
        path = tuple(int(got["Q"][i:i + 2], 2) for i in range(0, 22, 2))
        child = int(got["C"], 2)
        shell = int(got["S"], 2)
        if f5 > 19:
            return None                     # reserved face — cannot decode
        return RefinedAddress(source_face=f5, path=path, child_digit=child,
                              shell=shell, epoch_state=None,
                              parent_compact=CompactAddress(f5, path, shell),
                              alias_id=self.candidate_id)

    def _decode_octal_delete(self, raw: int) -> RefinedAddress | None:
        octal = format(raw, f"011o")
        (k,) = self.spec
        child = int(octal[k], 8)
        parent_octal = octal[:k] + octal[k + 1:]
        parent_raw = int(parent_octal, 8)
        if parent_raw >= (1 << 30):
            return None
        from rgcs_coordinate.codecs import federation_terra_30 as t10
        try:
            tr = t10.decode(parent_raw)
        except t10.PacketError:
            return None
        if tr.face_status != "valid-source-face-range":
            return None
        parent = CompactAddress(tr.face_id, tr.q22_path, tr.extracted_shell)
        return RefinedAddress(source_face=parent.f5, path=parent.q22_path,
                              child_digit=child, shell=parent.s3,
                              epoch_state=None, parent_compact=parent,
                              alias_id=self.candidate_id)

    def _decode_compact_shift(self, raw: int) -> RefinedAddress | None:
        (k,) = self.spec
        bits = format(raw, f"0{FRAME_BITS}b")
        start = 3 * k
        child_bits = bits[start:start + 3]
        parent_bits = bits[:start] + bits[start + 3:]
        parent_raw = int(parent_bits, 2)
        if parent_raw >= (1 << 30):
            return None
        from rgcs_coordinate.codecs import federation_terra_30 as t10
        try:
            tr = t10.decode(parent_raw)
        except t10.PacketError:
            return None
        if tr.face_status != "valid-source-face-range":
            return None
        parent = CompactAddress(tr.face_id, tr.q22_path, tr.extracted_shell)
        return RefinedAddress(source_face=parent.f5, path=parent.q22_path,
                              child_digit=int(child_bits, 2), shell=parent.s3,
                              epoch_state=None, parent_compact=parent,
                              alias_id=self.candidate_id)

    # ---------------------------------------------------------- encode
    def encode(self, refined: RefinedAddress) -> int | None:
        """Exact inverse of :meth:`decode` (bijective per candidate)."""
        if self.kind == "FIELD_ORDER":
            parts = {
                "F": format(refined.source_face, "05b"),
                "Q": "".join(format(p, "02b") for p in refined.path),
                "C": format(refined.child_digit, "03b"),
                "S": format(refined.shell, "03b"),
            }
            return int("".join(parts[n] for n in self.spec), 2)
        if self.kind in ("OCTAL_DELETE", "COMPACT_SHIFT"):
            if refined.parent_compact is None:
                return None
            from r109.codec import encode_compact
            parent_raw = encode_compact(refined.parent_compact)
            (k,) = self.spec
            if self.kind == "OCTAL_DELETE":
                po = format(parent_raw, "010o")
                oct11 = po[:k] + format(refined.child_digit, "o") + po[k:]
                return int(oct11, 8)
            pb = format(parent_raw, "030b")
            start = 3 * k
            bits = pb[:start] + format(refined.child_digit, "03b") + pb[start:]
            return int(bits, 2)
        return None

    def parent_reduce(self, refined: RefinedAddress) -> CompactAddress | None:
        """Drop the child digit -> the compact parent."""
        return refined.parent_compact


def candidate_space() -> tuple[T11Candidate, ...]:
    """The declared, bounded, finite candidate space (46 candidates)."""
    out: list[T11Candidate] = []
    for order in itertools.permutations("FQCS"):
        out.append(T11Candidate(
            candidate_id="T11_CANDIDATE_ORDER_" + "".join(order),
            kind="FIELD_ORDER", spec=tuple(order),
            assumptions="contiguous fields in the 33-bit frame, order "
                        + ">".join(order)))
    for k in range(11):
        out.append(T11Candidate(
            candidate_id=f"T11_CANDIDATE_OCTAL_DELETE_{k}",
            kind="OCTAL_DELETE", spec=(k,),
            assumptions=f"refined octal11 = compact octal10 with the child "
                        f"digit inserted at octal position {k}"))
    for k in range(11):
        out.append(T11Candidate(
            candidate_id=f"T11_CANDIDATE_BITSHIFT_GROUP_{k}",
            kind="COMPACT_SHIFT", spec=(k,),
            assumptions=f"refined bits = compact bits with one 3-bit child "
                        f"group inserted at bit offset {3 * k}"))
    return tuple(out)


@dataclass
class PairCheck:
    refined_raw: int
    compact_raw: int
    decodes: bool = False
    roundtrip: bool = False
    same_face: bool = False
    same_shell_class: bool = False
    contained: bool = False

    @property
    def passes(self) -> bool:
        return (self.decodes and self.roundtrip and self.same_face
                and self.same_shell_class and self.contained)


def check_pair(cand: T11Candidate, refined_raw: int,
               compact_raw: int) -> PairCheck:
    """Generic training-pair constraint check. NO location names in the
    logic — any (refined, compact) pair is checked identically."""
    from r109.codec import decode_compact
    from r109.types import WireAddress

    res = PairCheck(refined_raw=refined_raw, compact_raw=compact_raw)
    compact, _ = decode_compact(
        WireAddress.from_raw(compact_raw, "check"))
    refined = cand.decode(refined_raw)
    if refined is None:
        return res
    res.decodes = True
    back = cand.encode(refined)
    res.roundtrip = (back == refined_raw)
    res.same_face = (refined.source_face == compact.f5)
    res.same_shell_class = (refined.shell == compact.s3)
    # Containment: one appended 8-way child refines the compact cell,
    # so the refined parent path must EQUAL the compact path.
    res.contained = (refined.path == compact.q22_path
                     and refined.parent_compact is not None
                     and refined.parent_compact.q22_path == compact.q22_path)
    return res


def evaluate(pairs: list[tuple[int, int]]) -> dict:
    """Run every candidate against every pair; symmetry-reduce
    survivors that produce identical decodes on all pairs."""
    results = []
    survivors = []
    for cand in candidate_space():
        checks = [check_pair(cand, r, c) for (r, c) in pairs]
        ok = all(ch.passes for ch in checks)
        results.append({
            "candidate": cand.candidate_id,
            "kind": cand.kind,
            "assumptions": cand.assumptions,
            "pair_results": [
                {"refined": ch.refined_raw, "compact": ch.compact_raw,
                 "decodes": ch.decodes, "roundtrip": ch.roundtrip,
                 "same_face": ch.same_face,
                 "same_shell_class": ch.same_shell_class,
                 "contained": ch.contained, "passes": ch.passes}
                for ch in checks],
            "passes_all_pairs": ok,
        })
        if ok:
            survivors.append(cand)
    # symmetry reduction: identical (face, path, child, shell) decodes
    # across all pairs => same equivalence class
    reduced: dict[tuple, list[str]] = {}
    for cand in survivors:
        sig = tuple(
            (d.source_face, d.path, d.child_digit, d.shell)
            for d in (cand.decode(r) for (r, _) in pairs) if d is not None)
        reduced.setdefault(sig, []).append(cand.candidate_id)
    return {
        "schema": "rgcs.r109.t11-evaluation.v1",
        "candidate_count": len(results),
        "survivor_count": len(survivors),
        "equivalence_classes": [
            {"decode_signature_len": len(sig), "members": members}
            for sig, members in reduced.items()],
        "results": results,
        "status": ("UNIQUE" if len(reduced) == 1 and len(survivors) >= 1
                   else "ALIASES" if len(reduced) > 1
                   else "NO_CANDIDATE_IN_BOUNDED_SPACE"),
    }
