"""R10.10 Phase 5 — T11 search V2 (orientation-aware, documented, finite).

The R10.9 search (46 candidates, ZERO survivors) is preserved
unchanged as ``T11_SEARCH_V1_EXHAUSTED`` (:mod:`r109.t11_candidates`).
This module adds ONLY the families the R10.10 spec documents — nothing
is silently widened, no candidate contains a location name, and every
rejection is recorded with its reason.

Declared families
=================

FAM-ORIENT — topology/orientation-aware reading of the canonical
33-bit layout ``F5 | Q22 | C3 | S3`` (child at path end before shell,
as locked). Each wire quaternary symbol d is mapped to a geometric
child c through the CURRENT orientation state, which starts from the
face's dual-graph BFS assignment (Wilkes-rooted, frozen mesh — never a
free per-face permutation) and evolves through the geometrically
derived child-transition table. Documented binary options:

- map rule: ``c = o.perm[d]`` (APPLY) or ``c = o.inverse().perm[d]``
  (UNAPPLY) for d in {0,1,2}; the centre symbol 3 is orientation-fixed;
- seed: BFS assignment or its inverse;
- child digit: untouched, or its low two bits remapped through the
  final orientation state (the 8-way child's corner component).

FAM-ORDER-ORIENT — the same orientation machinery over the three
other field orders that keep path->child->shell ordering
(``Q F C S`` is not one of them; the constraint is Q before C before
S): F at positions 1..3: ``QFCS``, ``QCFS``, ``QCSF``. NOTE
``QCFS`` places F between child and shell and is EXCLUDED (child must
be at the end of the recursive path immediately before shell/epoch
closure would be ambiguous); included orders: ``FQCS`` (in
FAM-ORIENT), ``QFCS``, ``QCSF``.

FAM-NODE — explicit reversible six-bit node-state participation: the
top six bits are a 64-state selector split reversibly as
``state = spin*20 + face`` (spin 0..2, face 0..19; states 60..63
refused, never wrapped). Remaining 27 bits = ``Q22 | C3 | S2`` with
the 2-bit shell class (values 0..3, others unrepresentable and
refused). Options: spin seeds the orientation state (rotation^spin
composed onto the BFS assignment) or spin is carried but inert.

Survivor constraints (both training pairs, generically):
round trip exact; parent face/path/shell equal the compact decode;
one appended child; topology-derived orientation only.
"""

from __future__ import annotations

from dataclasses import dataclass

from rgcs_coordinate.codecs import federation_terra_30 as t10

from r1010.child_orientation import CHILD_TABLE
from r1010.dual_graph import load_faces, propagate
from r1010.orientation import ALL, IDENTITY, Orientation

FRAME_BITS = 33

# face codebook: packet F5 -> source face -> physical mesh face
_OFFSET = 14
_SOURCE_TO_MESH = None
_FACE_ASSIGN = None


def _face_tables():
    global _SOURCE_TO_MESH, _FACE_ASSIGN
    if _SOURCE_TO_MESH is None:
        import csv
        from r1010.dual_graph import V1_DIR
        _SOURCE_TO_MESH = {}
        for row in csv.DictReader(
                open(V1_DIR / "FACE_CODEBOOK_OPTION_A_OFFSET14.csv")):
            _SOURCE_TO_MESH[int(row["source_face_id"])] = \
                int(row["physical_mesh_face"])
        rep = propagate(load_faces())
        _FACE_ASSIGN = {f: Orientation.deserialize(s)
                        for f, s in rep["assignments"].items()}
    return _SOURCE_TO_MESH, _FACE_ASSIGN


def face_orientation(f5: int, invert_seed: bool, spin: int = 0) -> Orientation:
    """Topology-derived base orientation for a packet face."""
    s2m, assign = _face_tables()
    mesh = s2m[(f5 + _OFFSET) % 20]
    o = assign[mesh]
    if invert_seed:
        o = o.inverse()
    if spin:
        rot = Orientation((1, 2, 0))
        for _ in range(spin % 3):
            o = rot.compose(o)
    return o


_ROT = Orientation((1, 2, 0))


@dataclass(frozen=True)
class OrientCandidate:
    candidate_id: str
    family: str                # FAM_ORIENT | FAM_ORDER_ORIENT | FAM_NODE
    field_order: tuple[str, ...]
    map_rule: str              # APPLY | UNAPPLY
    invert_seed: bool
    remap_child: bool
    spin_active: bool = False  # FAM_NODE only
    assumptions: str = ""

    # ---------------------------------------------------------- helpers
    def _widths(self):
        return ({"F": 5, "Q": 22, "C": 3, "S": 3} if self.family != "FAM_NODE"
                else {"F": 6, "Q": 22, "C": 3, "S": 2})

    def _split(self, raw: int) -> dict | None:
        bits = format(raw, f"0{FRAME_BITS}b")
        w = self._widths()
        pos, got = 0, {}
        for name in self.field_order:
            got[name] = bits[pos:pos + w[name]]
            pos += w[name]
        return got

    def _symbol_map(self, o: Orientation, d: int) -> int:
        if d == 3:
            return 3
        return (o.perm[d] if self.map_rule == "APPLY"
                else o.inverse().perm[d])

    def _symbol_unmap(self, o: Orientation, c: int) -> int:
        if c == 3:
            return 3
        return (o.inverse().perm[c] if self.map_rule == "APPLY"
                else o.perm[c])

    # ------------------------------------------------------------ decode
    def decode(self, raw: int):
        """-> (face5, path11, child, shell, spin) or (None, reason)."""
        if raw < (1 << 30) or raw >= (1 << FRAME_BITS):
            return None, "not an 11-octal-digit word"
        got = self._split(raw)
        if self.family == "FAM_NODE":
            state = int(got["F"], 2)
            if state >= 60:
                return None, f"node state {state} in refused range 60..63"
            spin, face = divmod(state, 20)
            shell = int(got["S"], 2)          # 2-bit shell class
        else:
            face = int(got["F"], 2)
            spin = 0
            shell = int(got["S"], 2)
            if face > 19:
                return None, f"reserved face {face}"
        o = face_orientation(face, self.invert_seed,
                             spin if self.spin_active else 0)
        wire_syms = [int(got["Q"][i:i + 2], 2) for i in range(0, 22, 2)]
        path = []
        for d in wire_syms:
            c = self._symbol_map(o, d)
            path.append(c)
            o = CHILD_TABLE[c]["orientation"].compose(o)
        child = int(got["C"], 2)
        if self.remap_child:
            hi, lo2 = child >> 2, child & 3
            lo2 = self._symbol_map(o, lo2) if lo2 != 3 else 3
            child = (hi << 2) | lo2
        return {"face": face, "path": tuple(path), "child": child,
                "shell": shell, "spin": spin,
                "final_orientation": o.serialize()}, None

    # ------------------------------------------------------------ encode
    def encode(self, dec: dict) -> int | None:
        o = face_orientation(dec["face"], self.invert_seed,
                             dec["spin"] if self.spin_active else 0)
        wire_syms = []
        for c in dec["path"]:
            d = self._symbol_unmap(o, c)
            wire_syms.append(d)
            o = CHILD_TABLE[c]["orientation"].compose(o)
        child = dec["child"]
        if self.remap_child:
            hi, lo2 = child >> 2, child & 3
            lo2 = self._symbol_unmap(o, lo2) if lo2 != 3 else 3
            child = (hi << 2) | lo2
        w = self._widths()
        if self.family == "FAM_NODE":
            state = dec["spin"] * 20 + dec["face"]
            fields = {"F": format(state, "06b"),
                      "S": format(dec["shell"], "02b")}
        else:
            fields = {"F": format(dec["face"], "05b"),
                      "S": format(dec["shell"], "03b")}
        fields["Q"] = "".join(format(d, "02b") for d in wire_syms)
        fields["C"] = format(child, "03b")
        return int("".join(fields[n] for n in self.field_order), 2)


def candidate_space() -> tuple[OrientCandidate, ...]:
    out = []
    orders_main = [("F", "Q", "C", "S")]
    orders_order = [("Q", "F", "C", "S"), ("Q", "C", "S", "F")]
    for order in orders_main + orders_order:
        fam = "FAM_ORIENT" if order == ("F", "Q", "C", "S") \
            else "FAM_ORDER_ORIENT"
        for map_rule in ("APPLY", "UNAPPLY"):
            for inv in (False, True):
                for rc in (False, True):
                    out.append(OrientCandidate(
                        candidate_id=(f"T11V2_{fam}_{''.join(order)}_"
                                      f"{map_rule}_seed{'Inv' if inv else 'Fwd'}_"
                                      f"child{'Remap' if rc else 'Raw'}"),
                        family=fam, field_order=order, map_rule=map_rule,
                        invert_seed=inv, remap_child=rc,
                        assumptions=(f"order {'>'.join(order)}; symbol map "
                                     f"{map_rule}; seed "
                                     f"{'inverse ' if inv else ''}BFS "
                                     f"assignment; child "
                                     f"{'remapped' if rc else 'raw'}")))
    for map_rule in ("APPLY", "UNAPPLY"):
        for inv in (False, True):
            for spin_active in (False, True):
                out.append(OrientCandidate(
                    candidate_id=(f"T11V2_FAM_NODE_FQCS_{map_rule}_"
                                  f"seed{'Inv' if inv else 'Fwd'}_"
                                  f"spin{'Act' if spin_active else 'Inert'}"),
                    family="FAM_NODE", field_order=("F", "Q", "C", "S"),
                    map_rule=map_rule, invert_seed=inv, remap_child=False,
                    spin_active=spin_active,
                    assumptions=("six-bit node state = spin*20+face "
                                 "(60..63 refused); 2-bit shell class; "
                                 f"symbol map {map_rule}; seed "
                                 f"{'inverse ' if inv else ''}BFS; spin "
                                 f"{'seeds orientation' if spin_active else 'carried inert'}")))
    return tuple(out)


def evaluate(pairs) -> dict:
    """Every candidate against every pair; every rejection recorded."""
    results, survivors = [], []
    for cand in candidate_space():
        pair_rows, ok_all = [], True
        for refined_raw, compact_raw in pairs:
            ct = t10.decode(compact_raw)
            dec, reason = cand.decode(refined_raw)
            row = {"refined": refined_raw, "compact": compact_raw}
            if dec is None:
                row.update({"decodes": False, "rejection": reason,
                            "passes": False})
                ok_all = False
                pair_rows.append(row)
                continue
            back = cand.encode(dec)
            row.update({
                "decodes": True,
                "roundtrip": back == refined_raw,
                "same_face": dec["face"] == ct.face_id,
                "same_shell_class": dec["shell"] == ct.extracted_shell,
                "parent_path_equal": dec["path"] == ct.q22_path,
            })
            row["passes"] = all((row["roundtrip"], row["same_face"],
                                 row["same_shell_class"],
                                 row["parent_path_equal"]))
            if not row["passes"]:
                row["rejection"] = "; ".join(
                    k for k in ("roundtrip", "same_face",
                                "same_shell_class", "parent_path_equal")
                    if not row[k]) + " failed"
            ok_all = ok_all and row["passes"]
            pair_rows.append(row)
        results.append({"candidate": cand.candidate_id,
                        "family": cand.family,
                        "assumptions": cand.assumptions,
                        "pair_results": pair_rows,
                        "passes_all_pairs": ok_all})
        if ok_all:
            survivors.append(cand)
    reduced: dict[tuple, list[str]] = {}
    for cand in survivors:
        sig = tuple(tuple(sorted(cand.decode(r)[0].items()))
                    for r, _ in pairs)
        reduced.setdefault(sig, []).append(cand.candidate_id)
    return {
        "schema": "rgcs.r1010.t11-search-v2.v1",
        "search_v1": "T11_SEARCH_V1_EXHAUSTED (46 candidates, 0 survivors, preserved in r109.t11_candidates)",
        "candidate_count": len(results),
        "survivor_count": len(survivors),
        "equivalence_classes": [members for _, members in reduced.items()],
        "results": results,
        "status": ("UNIQUE" if len(reduced) == 1 and survivors
                   else "ALIASES" if len(reduced) > 1
                   else "NO_CANDIDATE_IN_EXPANDED_FAMILIES"),
    }
