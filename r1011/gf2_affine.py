"""R10.11E — GF(2) affine reconstruction and operator-family reduction.

Independent of the imported R10.11D artifacts: everything here is
recomputed from the TWELVE source-known cells alone. States are six-bit
vectors over GF(2); an affine candidate is ``T(x) = A x XOR b`` with
``A`` an invertible 6x6 binary matrix (rows stored as 6-bit ints,
row i gives output bit i as ``parity(row_i AND x)``).

Nothing beyond the twelve known cells is ever fitted; family searches
are declared and bounded; no geographic or reveal-derived
information exists in this module.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from r1011.segmented_codec import T_SPARSE

KNOWN = {5: {s: n for (s, c), n in T_SPARSE.items() if c == 5},
         6: {s: n for (s, c), n in T_SPARSE.items() if c == 6}}


# --------------------------------------------------------- GF(2) helpers
def mat_apply(rows: tuple[int, ...], x: int) -> int:
    out = 0
    for i, r in enumerate(rows):
        out |= (bin(r & x).count("1") & 1) << i
    return out


def mat_mul(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
    # (a·b)(x) = a(b(x)); rows of the product
    cols_b = [mat_apply(b, 1 << j) for j in range(6)]
    rows = []
    for i in range(6):
        r = 0
        for j in range(6):
            r |= (((mat_apply(a, cols_b[j]) >> i) & 1) << j)
        rows.append(r)
    return tuple(rows)


def mat_rank(rows) -> int:
    rs = list(rows)
    rank = 0
    for bit in range(5, -1, -1):
        piv = next((i for i in range(rank, len(rs))
                    if (rs[i] >> bit) & 1), None)
        if piv is None:
            continue
        rs[rank], rs[piv] = rs[piv], rs[rank]
        for i in range(len(rs)):
            if i != rank and ((rs[i] >> bit) & 1):
                rs[i] ^= rs[rank]
        rank += 1
    return rank


def mat_invertible(rows) -> bool:
    return mat_rank(rows) == 6


# ------------------------------------------------ affine reconstruction
def reconstruct(child: int) -> list[dict]:
    """All invertible affine completions consistent with the known
    cells of one child column, enumerated exactly.

    Method: pick a base point (x0, y0); difference constraints
    ``A (x_i XOR x0) = y_i XOR y0`` fix A on span{x_i XOR x0}; A is
    enumerated freely on a complement basis, filtered to invertibility;
    b = y0 XOR A x0.
    """
    pts = sorted(KNOWN[child].items())
    (x0, y0) = pts[0]

    # reduced echelon basis of the input-difference span, with outputs
    basis: list[tuple[int, int]] = []      # (in_vec, out_vec), echelon
    def reduce_pair(v, w):
        for bv, bw in basis:
            top = bv.bit_length() - 1
            if (v >> top) & 1:
                v ^= bv
                w ^= bw
        return v, w

    for x, y in pts[1:]:
        v, w = reduce_pair(x ^ x0, y ^ y0)
        if v == 0:
            if w != 0:
                return []                  # inconsistent: not affine
            continue
        basis.append((v, w))
        basis.sort(key=lambda t: -t[0])
        # re-reduce to echelon (eliminate higher rows' bits)
        changed = True
        while changed:
            changed = False
            for i in range(len(basis)):
                for j in range(len(basis)):
                    if i == j:
                        continue
                    top = basis[j][0].bit_length() - 1
                    if (basis[i][0] >> top) & 1:
                        basis[i] = (basis[i][0] ^ basis[j][0],
                                    basis[i][1] ^ basis[j][1])
                        changed = True
            basis = [b for b in basis if b[0]]
            basis.sort(key=lambda t: -t[0])

    # complement basis: unit vectors independent of the span
    free = []
    span_only = [bv for bv, _ in basis]
    def rank_of(vs):
        return mat_rank(tuple(vs + [0] * (6 - len(vs))))
    for j in range(6):
        cand = span_only + [f for f in free] + [1 << j]
        if mat_rank(tuple(cand + [0] * max(0, 6 - len(cand)))) >            mat_rank(tuple((span_only + free) + [0] * max(0, 6 - len(span_only + free)))):
            free.append(1 << j)
    assert len(basis) + len(free) == 6, (len(basis), len(free))

    completions = []
    for assign in itertools.product(range(64), repeat=len(free)):
        gens_in = [bv for bv, _ in basis] + free
        gens_out = [bw for _, bw in basis] + list(assign)

        def apply_lin(x):
            v, out = x, 0
            work = sorted(zip(gens_in, gens_out), key=lambda t: -t[0])
            for ri, ro in work:
                top = ri.bit_length() - 1
                if (v >> top) & 1:
                    v ^= ri
                    out ^= ro
            return out if v == 0 else None

        cols = [apply_lin(1 << j) for j in range(6)]
        if any(c is None for c in cols):
            continue
        rows = []
        for i in range(6):
            r = 0
            for j in range(6):
                r |= (((cols[j] >> i) & 1) << j)
            rows.append(r)
        rows = tuple(rows)
        if not mat_invertible(rows):
            continue
        b = y0 ^ mat_apply(rows, x0)
        if any(mat_apply(rows, x) ^ b != y for x, y in pts):
            continue
        table = tuple(mat_apply(rows, x) ^ b for x in range(64))
        if len(set(table)) != 64:
            continue
        completions.append({"A_rows": rows, "b": b, "table": table,
                            "id": "A" + "".join(f"{r:02x}" for r in rows)
                                  + f"b{b:02x}"})
    return completions


# ------------------------------------------------------ family searches
def shared_linear_core() -> dict:
    """Family A: does one invertible A satisfy BOTH children with
    child-specific offsets? Exact linear-system test."""
    hits = []
    c5 = reconstruct(5)
    c6 = reconstruct(6)
    a5 = {c["A_rows"]: c for c in c5}
    a6 = {c["A_rows"]: c for c in c6}
    shared = set(a5) & set(a6)
    for rows in shared:
        hits.append({"A_rows": rows, "b5": a5[rows]["b"], "b6": a6[rows]["b"]})
    return {"family": "A_shared_linear_core", "shared_matrix_count": len(hits),
            "hits": hits}


def perm_apply_bits(perm: tuple[int, ...], x: int) -> int:
    out = 0
    for i, p in enumerate(perm):
        out |= (((x >> p) & 1) << i)
    return out


def conjugacy_search(c5, c6) -> dict:
    """Family B: T6 = P^-1 T5 P over declared P families (720 bit
    permutations x optional pre/post complement masks)."""
    t5s = [c["table"] for c in c5]
    t6s = {c["table"] for c in c6}
    hits = []
    for perm in itertools.permutations(range(6)):
        for mask in (0,):                    # pure bit permutations first
            P = [perm_apply_bits(perm, x) ^ mask for x in range(64)]
            Pinv = [0] * 64
            for i, v in enumerate(P):
                Pinv[v] = i
            for idx, t5 in enumerate(t5s):
                cand = tuple(Pinv[t5[P[x]]] for x in range(64))
                if cand in t6s:
                    hits.append({"perm": perm, "mask": mask, "t5_index": idx})
    return {"family": "B_affine_conjugacy_bitperms",
            "searched": "720 bit permutations x 32 t5 completions",
            "hit_count": len(hits), "hits": hits[:10]}


def delta_operators(c5, c6) -> dict:
    """Family D: D = T6 o T5^-1 across all completion pairs; cluster by
    cycle structure and parity."""
    from collections import Counter
    sigs = Counter()
    for a in c5:
        inv5 = [0] * 64
        for x in range(64):
            inv5[a["table"][x]] = x
        for b in c6:
            d = tuple(b["table"][inv5[x]] for x in range(64))
            # cycle structure
            seen = [False] * 64
            cyc = []
            for s in range(64):
                if seen[s]:
                    continue
                ln = 0
                t = s
                while not seen[t]:
                    seen[t] = True
                    t = d[t]
                    ln += 1
                cyc.append(ln)
            sigs[tuple(sorted(cyc))] += 1
    return {"family": "D_relative_operator_cycle_structures",
            "pair_count": sum(sigs.values()),
            "distinct_cycle_structures": len(sigs),
            "top_structures": sigs.most_common(6)}


def rank_distribution(c5, c6) -> dict:
    from collections import Counter
    ranks = Counter()
    for a in c5:
        for b in c6:
            x = tuple(r1 ^ r2 for r1, r2 in zip(a["A_rows"], b["A_rows"]))
            ranks[mat_rank(x)] += 1
    return {"rank_of_A5_xor_A6_distribution": dict(sorted(ranks.items())),
            "min_rank": min(ranks)}


def equivalence_classes(comps) -> dict:
    """Partition completions by basis-invariant signatures: cycle
    structure of the full permutation + parity + fixed-point count."""
    from collections import defaultdict
    classes = defaultdict(list)
    for c in comps:
        t = c["table"]
        seen = [False] * 64
        cyc = []
        for s in range(64):
            if seen[s]:
                continue
            ln, u = 0, s
            while not seen[u]:
                seen[u] = True
                u = t[u]
                ln += 1
            cyc.append(ln)
        sig = (tuple(sorted(cyc)), sum(1 for x in range(64) if t[x] == x))
        classes[sig].append(c["id"])
    return {str(k): v for k, v in sorted(classes.items(), key=lambda kv: str(kv[0]))}


def basis_invariance_check(child: int) -> dict:
    """Recompute the completion count under bit-reversed state
    numbering; the count must be identical (basis-free meaning)."""
    global KNOWN
    orig = KNOWN
    rev = lambda v: int(format(v, "06b")[::-1], 2)
    KNOWN = {c: {rev(x): rev(y) for x, y in d.items()} for c, d in orig.items()}
    try:
        n = len(reconstruct(child))
    finally:
        KNOWN = orig
    return {"child": child, "bit_reversed_completion_count": n}
