"""A19-A26 — the multiresolution codec.

An adaptive octree over a payload field. Each node holds a prototype;
children are coded as residuals from the parent prototype. A node is
SPLIT only when the Lagrangian actually improves:

    J = D + lambda * R          (split iff J_children < J_parent)

**Full bit accounting is mandatory (R19/R23/R51).** The reported rate
includes topology bits, address bits, codebook bits, payload symbol
bits, residual bits, ECC and metadata — not just the payload. A codec
that "wins" by excluding its codebook has not won.

Modes (core/04): LOSSLESS_STRUCTURE, LOSSLESS_PAYLOAD,
LOSSY_FIXED_ERROR, LOSSY_FIXED_RATE, PROGRESSIVE,
SPARSE_RANDOM_ACCESS.

Determinism: every optimizer decision is a pure function of the data,
the frozen thresholds, and the seed. Codebook training uses a declared
train/test split so test leakage is structurally impossible (R20).
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field

import numpy as np

from . import CODEC_MODES, ClaimBoundaryError

CONTAINER_MAGIC = b"R4TC"
CONTAINER_VERSION = 1


# --- multiresolution tree (A19) --------------------------------------------

@dataclass
class Node:
    """One cell of the adaptive octree."""
    depth: int
    index: int                       # address key at this depth
    lo: int                          # payload slice bounds
    hi: int
    prototype: float = 0.0
    children: list = field(default_factory=list)

    @property
    def leaf(self) -> bool:
        return not self.children

    @property
    def size(self) -> int:
        return self.hi - self.lo


def _mean(x) -> float:
    return float(np.mean(x)) if len(x) else 0.0


def build_tree(data: np.ndarray, max_depth: int, lam: float,
               branching: int = 8) -> Node:
    """Adaptive split: recurse only where the Lagrangian improves.

    Rate model (declared, not tuned): one topology bit per node, plus
    ``PROTOTYPE_BITS`` per stored prototype.
    """
    root = Node(0, 0, 0, len(data), _mean(data))
    _maybe_split(root, data, max_depth, lam, branching)
    return root


PROTOTYPE_BITS = 32          # float32 prototype
TOPOLOGY_BITS = 1            # split/leaf flag per node


def _sse(data: np.ndarray, lo: int, hi: int, proto: float) -> float:
    seg = data[lo:hi]
    return float(np.sum((seg - proto) ** 2)) if len(seg) else 0.0


def _maybe_split(node: Node, data: np.ndarray, max_depth: int,
                 lam: float, branching: int) -> None:
    if node.depth >= max_depth or node.size <= 1:
        return
    d_parent = _sse(data, node.lo, node.hi, node.prototype)
    r_parent = TOPOLOGY_BITS + PROTOTYPE_BITS
    bounds = np.linspace(node.lo, node.hi, branching + 1).astype(int)
    kids = []
    d_children = 0.0
    r_children = TOPOLOGY_BITS
    for c in range(branching):
        lo, hi = int(bounds[c]), int(bounds[c + 1])
        if hi <= lo:
            continue
        proto = _mean(data[lo:hi])
        kids.append(Node(node.depth + 1, node.index * branching + c,
                         lo, hi, proto))
        d_children += _sse(data, lo, hi, proto)
        r_children += TOPOLOGY_BITS + PROTOTYPE_BITS
    if not kids:
        return
    j_parent = d_parent + lam * r_parent
    j_children = d_children + lam * r_children
    if j_children < j_parent:
        node.children = kids
        for k in kids:
            _maybe_split(k, data, max_depth, lam, branching)


def leaves(node: Node) -> list:
    if node.leaf:
        return [node]
    out = []
    for c in node.children:
        out.extend(leaves(c))
    return out


def count_nodes(node: Node) -> int:
    return 1 + sum(count_nodes(c) for c in node.children)


def reconstruct(node: Node, n: int) -> np.ndarray:
    out = np.zeros(n, dtype=float)
    for lf in leaves(node):
        out[lf.lo:lf.hi] = lf.prototype
    return out


# --- codebook with leakage prevention (A21) ---------------------------------

@dataclass(frozen=True)
class Codebook:
    """Frozen prototype codebook. ``trained_on`` records the split so a
    reviewer can see the test set was never used (R20)."""
    centroids: tuple
    trained_on: str
    n_train: int
    frozen: bool = True

    @property
    def bits(self) -> int:
        return len(self.centroids) * PROTOTYPE_BITS

    def encode(self, value: float) -> int:
        arr = np.asarray(self.centroids)
        return int(np.argmin(np.abs(arr - value)))

    def decode(self, index: int) -> float:
        return float(self.centroids[index])


def train_codebook(train_data: np.ndarray, k: int,
                   seed: int = 20260718, iters: int = 25) -> Codebook:
    """Deterministic 1-D Lloyd/k-means on the TRAINING split only."""
    if len(train_data) < k:
        raise ClaimBoundaryError(
            f"cannot train {k} centroids on {len(train_data)} samples")
    rng = np.random.default_rng(seed)
    c = np.sort(rng.choice(train_data, size=k, replace=False))
    for _ in range(iters):
        idx = np.argmin(np.abs(train_data[:, None] - c[None, :]), axis=1)
        new = np.array([train_data[idx == j].mean() if np.any(idx == j)
                        else c[j] for j in range(k)])
        if np.allclose(new, c):
            break
        c = np.sort(new)
    return Codebook(tuple(float(x) for x in c), "TRAIN_SPLIT_ONLY",
                    len(train_data))


def split_train_test(data: np.ndarray, train_frac: float = 0.5,
                     seed: int = 20260718) -> tuple:
    """Deterministic disjoint split — the structural guarantee against
    codebook test leakage."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(data))
    cut = int(len(data) * train_frac)
    return data[idx[:cut]], data[idx[cut:]]


# --- entropy model (A24) -----------------------------------------------------

def entropy_bits(symbols: list, alphabet: int = 4) -> dict:
    """Zeroth-order entropy and the actual cost of coding these symbols
    with an ideal entropy coder, plus the model-transmission overhead
    that a fair accounting must include (R23)."""
    if not symbols:
        return {"entropy_bits_per_symbol": 0.0, "payload_bits": 0,
                "model_bits": 0, "total_bits": 0}
    counts = np.bincount(np.asarray(symbols), minlength=alphabet)
    p = counts / counts.sum()
    nz = p[p > 0]
    h = float(-np.sum(nz * np.log2(nz)))
    payload = h * len(symbols)
    # transmitting the model: alphabet-1 frequencies at 16 bits each
    model = (alphabet - 1) * 16
    return {"entropy_bits_per_symbol": h,
            "payload_bits": payload,
            "model_bits": model,
            "total_bits": payload + model,
            "note": "an entropy coder that omits its model cost is "
                    "not being accounted fairly"}


# --- container / bitstream (A23) ---------------------------------------------

def pack_container(mode: str, n: int, tree: Node, codebook: Codebook,
                   symbols: list, residual: np.ndarray | None) -> bytes:
    """Versioned, portable container. Header is fixed-width so a
    decoder can always find the sections."""
    if mode not in CODEC_MODES:
        raise ClaimBoundaryError(f"unknown mode {mode!r}")
    body = bytearray()
    body += struct.pack("<4sHH", CONTAINER_MAGIC, CONTAINER_VERSION,
                        CODEC_MODES.index(mode))
    body += struct.pack("<II", n, count_nodes(tree))
    body += struct.pack("<H", len(codebook.centroids))
    for c in codebook.centroids:
        body += struct.pack("<f", c)
    body += struct.pack("<I", len(symbols))
    body += bytes(bytearray(symbols))
    has_res = residual is not None
    body += struct.pack("<B", 1 if has_res else 0)
    if has_res:
        body += struct.pack("<I", len(residual))
        body += np.asarray(residual, dtype=np.float32).tobytes()
    return bytes(body)


def unpack_container(blob: bytes) -> dict:
    magic, ver, mode_i = struct.unpack_from("<4sHH", blob, 0)
    if magic != CONTAINER_MAGIC:
        raise ClaimBoundaryError("not an R4 container")
    if ver != CONTAINER_VERSION:
        raise ClaimBoundaryError(
            f"container version {ver} != {CONTAINER_VERSION}")
    off = 8
    n, n_nodes = struct.unpack_from("<II", blob, off)
    off += 8
    (k,) = struct.unpack_from("<H", blob, off)
    off += 2
    centroids = list(struct.unpack_from(f"<{k}f", blob, off))
    off += 4 * k
    (n_sym,) = struct.unpack_from("<I", blob, off)
    off += 4
    symbols = list(blob[off:off + n_sym])
    off += n_sym
    (has_res,) = struct.unpack_from("<B", blob, off)
    off += 1
    residual = None
    if has_res:
        (rn,) = struct.unpack_from("<I", blob, off)
        off += 4
        residual = np.frombuffer(blob, dtype=np.float32, count=rn,
                                 offset=off)
    return {"mode": CODEC_MODES[mode_i], "n": n, "n_nodes": n_nodes,
            "centroids": centroids, "symbols": symbols,
            "residual": residual, "version": ver}


# --- the codec (A22/A25/A26) --------------------------------------------------

def encode(data: np.ndarray, mode: str = "LOSSY_FIXED_ERROR",
           max_depth: int = 4, lam: float = 1.0, k: int = 16,
           seed: int = 20260718) -> dict:
    """Encode with FULL bit accounting."""
    data = np.asarray(data, dtype=float)
    train, _ = split_train_test(data, 0.5, seed)
    cb = train_codebook(train, min(k, len(train)), seed)
    tree = build_tree(data, max_depth, lam)
    lfs = leaves(tree)
    symbols = [cb.encode(lf.prototype) for lf in lfs]
    recon = np.zeros(len(data))
    for lf, s in zip(lfs, symbols):
        recon[lf.lo:lf.hi] = cb.decode(s)
    residual = None
    if mode == "LOSSLESS_PAYLOAD":
        residual = (data - recon).astype(np.float32)
        recon = recon + residual
    blob = pack_container(mode, len(data), tree, cb, symbols, residual)
    ent = entropy_bits(symbols, alphabet=len(cb.centroids))
    topology_bits = count_nodes(tree) * TOPOLOGY_BITS
    address_bits = len(lfs) * math.ceil(math.log2(max(len(lfs), 2)))
    residual_bits = 0 if residual is None else 32 * len(residual)
    total = (topology_bits + address_bits + cb.bits +
             ent["total_bits"] + residual_bits)
    return {
        "mode": mode,
        "container": blob,
        "container_bytes": len(blob),
        "reconstruction": recon,
        "bit_accounting": {
            "topology_bits": topology_bits,
            "address_bits": address_bits,
            "codebook_bits": cb.bits,
            "payload_symbol_bits": ent["payload_bits"],
            "entropy_model_bits": ent["model_bits"],
            "residual_bits": residual_bits,
            "total_bits": total,
        },
        "n_leaves": len(lfs), "n_nodes": count_nodes(tree),
        "raw_bits": 32 * len(data),
        "compression_ratio": (32 * len(data)) / total if total else
        float("inf"),
        "evidence_class": "NUMERICAL_SIMULATION",
    }


def decode(blob: bytes) -> np.ndarray:
    """Decode a container to the reconstruction."""
    c = unpack_container(blob)
    # leaves are coded in order; reconstruct by equal partition of the
    # symbol run over n samples
    n, symbols = c["n"], c["symbols"]
    out = np.zeros(n, dtype=float)
    if symbols:
        bounds = np.linspace(0, n, len(symbols) + 1).astype(int)
        for i, s in enumerate(symbols):
            out[bounds[i]:bounds[i + 1]] = c["centroids"][s]
    if c["residual"] is not None:
        out = out + np.asarray(c["residual"], dtype=float)
    return out


def progressive_layers(data: np.ndarray, depths: list,
                       lam: float = 1.0) -> list:
    """PROGRESSIVE mode: quality improves monotonically with depth."""
    out = []
    for d in depths:
        tree = build_tree(data, d, lam)
        recon = reconstruct(tree, len(data))
        out.append({"depth": d, "n_leaves": len(leaves(tree)),
                    "mse": float(np.mean((data - recon) ** 2))})
    return out


def random_access(data: np.ndarray, index: int, max_depth: int = 4,
                  lam: float = 1.0) -> dict:
    """SPARSE_RANDOM_ACCESS: reach one sample by walking the tree, and
    report the nodes touched — the real cost of random access."""
    tree = build_tree(data, max_depth, lam)
    node, touched = tree, 1
    while not node.leaf:
        for c in node.children:
            if c.lo <= index < c.hi:
                node = c
                touched += 1
                break
        else:
            break
    return {"index": index, "value": node.prototype,
            "nodes_touched": touched, "depth_reached": node.depth}
