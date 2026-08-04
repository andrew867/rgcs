"""P09 — Five-token base-100 route parser, reconstruction, and prefix tree.

The locked route core (Locked Decision 13) is a **five-token base-100**
representation, for example ``01|65|87|65|23``. This module parses the compact
route exactly, reconstructs it losslessly, supports variable depth (1..N
tokens), and provides prefix-tree operations (insert, lookup, common prefix,
ancestry, siblings, comparison) over routes.

Design rules honoured here:

* **Left-pad odd-length strings to even length only under the named codec.**
  The ``LEFT_PAD_TO_EVEN`` policy pads ``"165876523"`` -> ``"0165876523"``.
  Under the ``EXPLICIT`` policy an odd-length string is refused, not repaired.
* **Preserve raw digits and the leading-zero policy.** The canonical even-length
  digit string and the policy that produced it are both carried in the record;
  the original operator input is preserved for provenance.
* **Support 1..N tokens with exact reconstruction.** ``parse`` accepts variable
  depth; :meth:`RouteCore.to_raw` / :meth:`RouteCore.to_wire` reconstruct the
  exact token string, so ``parse(reconstruct(route)) == route`` (round-trip).
* **Malformed input is refused, never guessed.** A wrong token count (for the
  five-token parser), a non-digit character, or an odd length under the
  ``EXPLICIT`` policy raises :class:`RouteError`, not a silent repair.

A parsed route is an exact arithmetic re-expression of the operator's digit
string: evidence class ``DERIVED_MATHEMATICS``, claim class
``MATHEMATICAL_TRANSLATION``. It is **not** a decoded location and it does not
validate the source origin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from cwatlas.claims import ClaimClass, ClaimError
from cwatlas.codec_base100 import decode_to_path as _b100_decode
from cwatlas.codec_base100 import encode as _b100_encode
from cwatlas.r1082 import claims as _r1082

#: Route codec identity (matches ``source_route_core.schema.json``).
CODEC_ID = "CW_BASE100_ROUTE_V2"

#: The locked route core is five base-100 tokens (Locked Decision 13).
FIVE_TOKEN = 5

TOKEN_MIN = 0
TOKEN_MAX = 99
_TOKEN_DIGITS = 2

#: Leading-zero policies. ``LEFT_PAD_TO_EVEN`` pads an odd-length digit string
#: to even length under the named codec; ``EXPLICIT`` refuses odd lengths.
POLICY_LEFT_PAD = "LEFT_PAD_TO_EVEN"
POLICY_EXPLICIT = "EXPLICIT"
_POLICIES = frozenset({POLICY_LEFT_PAD, POLICY_EXPLICIT})

#: Separators accepted between tokens in a human-written route.
_SEPARATORS = "| ,-_/"
_DECIMAL_DIGITS = frozenset("0123456789")


class RouteError(ClaimError):
    """Raised when a route string is malformed and is refused (no repair)."""


@dataclass(frozen=True)
class RouteCore:
    """A parsed base-100 route, conforming to ``source_route_core.schema.json``.

    ``raw`` is the canonical even-length digit string; ``tokens`` are the
    integer tokens (0..99). ``original_input`` preserves what the operator
    supplied (before separator stripping / padding) and is *not* serialized to
    the schema (which forbids extra properties).
    """

    raw: str
    tokens: tuple[int, ...]
    codec_id: str = CODEC_ID
    leading_zero_policy: str = POLICY_LEFT_PAD
    variable_depth: bool = True
    original_input: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        if self.codec_id != CODEC_ID:
            raise RouteError(
                f"route codec_id must be {CODEC_ID!r}, got {self.codec_id!r}.")
        if not self.tokens:
            raise RouteError("a route must carry at least one token.")
        for i, t in enumerate(self.tokens):
            if isinstance(t, bool) or not isinstance(t, int):
                raise RouteError(f"token {i} must be an int, got {t!r}.")
            if not TOKEN_MIN <= t <= TOKEN_MAX:
                raise RouteError(
                    f"token {i}={t} out of range [{TOKEN_MIN}, {TOKEN_MAX}].")

    @property
    def depth(self) -> int:
        return len(self.tokens)

    def to_raw(self) -> str:
        """Reconstruct the exact canonical even-length digit string."""
        return _b100_encode(self.tokens)

    def to_wire(self, sep: str = "|") -> str:
        """Reconstruct the human-readable ``01|65|87|65|23`` form."""
        return sep.join(f"{t:0{_TOKEN_DIGITS}d}" for t in self.tokens)

    def to_dict(self) -> dict:
        """Serialize to the ``source_route_core`` schema (no extra keys)."""
        return {
            "raw": self.raw,
            "tokens": list(self.tokens),
            "codec_id": self.codec_id,
            "leading_zero_policy": self.leading_zero_policy,
            "variable_depth": self.variable_depth,
        }


def _strip_separators(text: str) -> str:
    return "".join(ch for ch in text if ch not in _SEPARATORS)


def normalize(text: str, *, leading_zero_policy: str = POLICY_LEFT_PAD) -> str:
    """Return the canonical even-length digit string for ``text``.

    Separators (``| ,-_/``) are stripped. Under ``LEFT_PAD_TO_EVEN`` an
    odd-length digit run is left-padded with a single ``0``; under ``EXPLICIT``
    an odd length is refused. Non-digit content is always refused.
    """
    if leading_zero_policy not in _POLICIES:
        raise RouteError(
            f"unknown leading_zero_policy {leading_zero_policy!r}; "
            f"expected one of {sorted(_POLICIES)}.")
    if not isinstance(text, str):
        raise RouteError(f"route input must be a str, got {type(text).__name__}.")
    digits = _strip_separators(text)
    if not digits:
        raise RouteError("route input has no digits after separator stripping.")
    if any(ch not in _DECIMAL_DIGITS for ch in digits):
        raise RouteError(
            "route input must be base-10 decimal digits (with optional "
            f"separators {_SEPARATORS!r}); refused (no silent repair).")
    if len(digits) % _TOKEN_DIGITS != 0:
        if leading_zero_policy == POLICY_EXPLICIT:
            raise RouteError(
                f"odd-length route {digits!r} refused under the EXPLICIT "
                f"policy; only LEFT_PAD_TO_EVEN may pad to even length.")
        digits = "0" + digits  # LEFT_PAD_TO_EVEN, only under the named codec
    return digits


def parse(text: str, *, leading_zero_policy: str = POLICY_LEFT_PAD,
          expect_tokens: int | None = None) -> RouteCore:
    """Parse a route string into an exact :class:`RouteCore`.

    Accepts the pipe form ``01|65|87|65|23`` and the bare digit form
    ``165876523`` (or ``0165876523``); both yield the same five tokens. Set
    ``expect_tokens`` to enforce an exact token count (a wrong count is
    refused). ``leading_zero_policy`` selects odd-length handling.
    """
    canonical = normalize(text, leading_zero_policy=leading_zero_policy)
    tokens = _b100_decode(canonical)  # reuses the CW-BASE100 grammar
    if expect_tokens is not None and len(tokens) != expect_tokens:
        raise RouteError(
            f"expected exactly {expect_tokens} base-100 tokens, got "
            f"{len(tokens)} from {text!r}; refused.")
    return RouteCore(
        raw=canonical,
        tokens=tokens,
        codec_id=CODEC_ID,
        leading_zero_policy=leading_zero_policy,
        variable_depth=expect_tokens is None,
        original_input=text,
    )


def parse_five_token(text: str, *,
                     leading_zero_policy: str = POLICY_LEFT_PAD) -> RouteCore:
    """Parse the locked five-token route; a non-five token count is refused."""
    route = parse(text, leading_zero_policy=leading_zero_policy,
                  expect_tokens=FIVE_TOKEN)
    return RouteCore(
        raw=route.raw, tokens=route.tokens, codec_id=route.codec_id,
        leading_zero_policy=route.leading_zero_policy, variable_depth=False,
        original_input=route.original_input)


def reconstruct(route: RouteCore, *, wire: bool = False) -> str:
    """Reconstruct the digit (default) or pipe (``wire=True``) form."""
    return route.to_wire() if wire else route.to_raw()


# -- prefix / ancestry operations -------------------------------------------

def common_prefix(a: Sequence[int], b: Sequence[int]) -> tuple[int, ...]:
    """The longest shared leading run of two token sequences."""
    out: list[int] = []
    for ta, tb in zip(a, b):
        if ta != tb:
            break
        out.append(ta)
    return tuple(out)


def common_prefix_length(a: Sequence[int], b: Sequence[int]) -> int:
    """Length of the longest shared leading run."""
    return len(common_prefix(a, b))


def is_ancestor(ancestor: Sequence[int], descendant: Sequence[int]) -> bool:
    """True iff ``ancestor`` is a strict prefix of ``descendant``."""
    a, d = tuple(ancestor), tuple(descendant)
    return len(a) < len(d) and d[:len(a)] == a


def are_siblings(a: Sequence[int], b: Sequence[int]) -> bool:
    """True iff two routes have equal depth and share all but the last token."""
    a, b = tuple(a), tuple(b)
    return len(a) == len(b) and len(a) >= 1 and a[:-1] == b[:-1] and a != b


def compare(a: Sequence[int], b: Sequence[int]) -> int:
    """Lexicographic route comparison: -1, 0, or +1."""
    a, b = tuple(a), tuple(b)
    return (a > b) - (a < b)


def is_line_like_terminal_progression(
        routes: Iterable[Sequence[int]]) -> bool:
    """True iff routes share one prefix and their terminal tokens are linear.

    Verifies the locked ``01|65|89|27|43/63/83`` behaviour: every route shares
    the same leading prefix (all tokens but the last) and the terminal tokens
    form an arithmetic progression (a constant step), i.e. a line-like
    terminal progression.
    """
    seqs = [tuple(r) for r in routes]
    if len(seqs) < 2:
        return False
    depth = len(seqs[0])
    if any(len(s) != depth or depth < 1 for s in seqs):
        return False
    prefix = seqs[0][:-1]
    if any(s[:-1] != prefix for s in seqs):
        return False
    terminals = [s[-1] for s in seqs]
    step = terminals[1] - terminals[0]
    return all(terminals[i + 1] - terminals[i] == step
               for i in range(len(terminals) - 1))


class RoutePrefixTree:
    """A prefix (radix-by-token) tree over base-100 routes.

    Supports ``insert`` / ``contains`` (exact lookup), ``has_prefix``,
    ``longest_common_prefix`` across all stored routes, and ``descendants`` of
    a given prefix. Pure structure over integer tokens; nothing measured.
    """

    __slots__ = ("_children", "_terminal", "_count")

    def __init__(self) -> None:
        self._children: dict[int, RoutePrefixTree] = {}
        self._terminal = False
        self._count = 0  # number of full routes stored at or below this node

    def insert(self, route: Sequence[int]) -> None:
        node = self
        node._count += 1
        for tok in route:
            if not TOKEN_MIN <= tok <= TOKEN_MAX:
                raise RouteError(
                    f"prefix-tree token {tok} out of range "
                    f"[{TOKEN_MIN}, {TOKEN_MAX}].")
            node = node._children.setdefault(tok, RoutePrefixTree())
            node._count += 1
        node._terminal = True

    def _walk(self, path: Sequence[int]) -> "RoutePrefixTree | None":
        node = self
        for tok in path:
            node = node._children.get(tok)
            if node is None:
                return None
        return node

    def contains(self, route: Sequence[int]) -> bool:
        """Exact route lookup."""
        node = self._walk(route)
        return node is not None and node._terminal

    def has_prefix(self, prefix: Sequence[int]) -> bool:
        """True iff any stored route begins with ``prefix``."""
        return self._walk(prefix) is not None

    def descendants(self, prefix: Sequence[int]) -> int:
        """Number of stored routes at or below ``prefix``."""
        node = self._walk(prefix)
        return 0 if node is None else node._count

    def longest_common_prefix(self) -> tuple[int, ...]:
        """The longest token prefix shared by every stored route."""
        out: list[int] = []
        node = self
        total = node._count
        if total == 0:
            return ()
        while len(node._children) == 1 and not node._terminal:
            (tok, child), = node._children.items()
            if child._count != total:
                break
            out.append(tok)
            node = child
        return tuple(out)


def route_core_report() -> dict:
    """P09 declaration receipt. Exact arithmetic; nothing measured or located."""
    return {
        "phase_id": "P09",
        "tranche": "T03",
        "what_this_is": (
            "an exact five-token base-100 route parser, lossless "
            "reconstruction, variable-depth support (1..N tokens), and "
            "prefix-tree operations (insert/lookup/common-prefix/ancestry/"
            "siblings/compare) over routes."),
        "codec_id": CODEC_ID,
        "five_token_locked": FIVE_TOKEN,
        "token_range": [TOKEN_MIN, TOKEN_MAX],
        "leading_zero_policies": sorted(_POLICIES),
        "evidence_class": _r1082.EvidenceClass.DERIVED_MATHEMATICS.value,
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "reversible": True,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "GREEN_R10_8_2_P09_FIVE-TOKEN_BASE-100_PARSER_AND_PREFIX_TREE",
        "what_this_does_not_say": (
            "A parsed route is an exact re-expression of the operator's digit "
            "string, not a decoded location. Source-vector geographic "
            "semantics remain NOT_CLAIMED."),
    }
