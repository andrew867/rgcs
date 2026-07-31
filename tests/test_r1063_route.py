"""R10.63 -- the route lane, and the null that refuted its first reading.

The geometry tests are ordinary. The ones that matter are the pair
pinning the defect that made the first pass of this analysis look
positive: in absolute-bearing mode a step's direction depends only on
the digit's value, so displacement is essentially a vector sum and
commutes. The invariance is EXACT in the plane and approximate on a
sphere (~4e-5), an order of magnitude below the null's own spread. Both
facts are asserted here so the metric can never be quoted as evidence
of routing again.
"""

import math
import random

import pytest

from r1053 import projector, route

PAYLOAD = "101672770075311773227352216477536105260021"


# ------------------------------------------------------ field parsing

def test_payload_satisfies_the_wide_envelope_width_law():
    """126 = 21 + 3(35). Exact, and the reason this record is well-formed."""
    n_oct = len(PAYLOAD)
    assert n_oct * 3 == 126
    chain = n_oct - 7                      # E3 + S_tor + S_pol + S_rad
    assert chain == 35
    assert 126 == 21 + 3 * chain


def test_parse_splits_into_the_documented_fields():
    f = route.parse_payload(PAYLOAD, d_left=17)
    assert f["d_left"] == 17 and f["d_right"] == 18
    assert len(f["chain_left"]) + len(f["chain_right"]) == 35
    for k in ("E3", "S_tor", "S_pol", "S_rad"):
        assert 0 <= f[k] < 64
    assert f["width_law_ok"]


def test_all_36_splits_are_legal_and_conserve_the_chain():
    total = len(PAYLOAD) - 7
    seen = 0
    for d in range(total + 1):
        f = route.parse_payload(PAYLOAD, d)
        assert len(f["chain_left"]) + len(f["chain_right"]) == total
        seen += 1
    assert seen == 36


def test_out_of_range_split_is_refused():
    with pytest.raises(route.RouteError):
        route.parse_payload(PAYLOAD, d_left=99)


# ---------------------------------------------------------- geometry

def test_a_step_lands_the_stated_distance_and_bearing_away():
    lat, lon = 45.0, -73.0
    for bearing in (0.0, 45.0, 90.0, 180.0, 315.0):
        p = route._step(lat, lon, bearing, 100.0)
        assert projector.haversine_km(lat, lon, *p) == pytest.approx(100.0,
                                                                     rel=1e-9)
        assert projector.bearing_deg(lat, lon, *p) == pytest.approx(bearing,
                                                                    abs=1e-6)


def test_walk_produces_one_more_waypoint_than_steps():
    pts = route.walk("0123", (0.0, 0.0))
    assert len(pts) == 5


def test_legs_sum_to_the_reported_total():
    r = route.route_record("01234567", (10.0, 20.0))
    assert sum(l["km"] for l in r["legs"]) == pytest.approx(r["total_km"],
                                                            rel=1e-9)
    assert len(r["turns"]) == len(r["legs"]) - 1


def test_a_straight_chain_is_perfectly_straight():
    """All-zero digits = due north every step."""
    r = route.route_record("0" * 10, (0.0, 0.0))
    assert r["straightness"] == pytest.approx(1.0, abs=1e-6)
    assert r["mean_abs_turn_deg"] == pytest.approx(0.0, abs=1e-6)


def test_turn_angles_are_signed_and_wrapped():
    r = route.route_record("02", (0.0, 0.0))       # north then east
    t = r["turns"][0]
    assert t["turn_deg"] == pytest.approx(90.0, abs=1e-3)
    assert t["direction"] == "right"


def test_unknown_mode_is_refused():
    with pytest.raises(route.RouteError):
        route.walk("012", (0.0, 0.0), mode="nonsense")


# ------------------------------------------- the defect, pinned as a test

def test_absolute_mode_straightness_is_order_invariant_to_1e4():
    """THE defect that made the first pass of R10.63 look positive.

    In absolute-bearing mode a step's direction depends only on the
    digit's value, so net displacement is essentially a vector sum --
    and vector addition commutes. In the PLANE the invariance is exact
    (measured deviation 1.7e-16). On a SPHERE translations commute only
    approximately, so the measured deviation is ~4e-5 relative.

    That residual is an order of magnitude below the permutation null's
    own spread (~1e-3 in straightness units), so straightness in this
    mode still cannot carry routing information and must never be quoted
    as evidence. The earlier claim that it was *exactly* invariant was
    too strong and is corrected here.
    """
    chain = "10167277007531177322735221647753"
    base = route.route_record(chain, (0.0, 0.0), mode="octant")
    rng = random.Random(5)
    worst = 0.0
    for _ in range(40):
        shuffled = "".join(rng.sample(chain, len(chain)))
        r = route.route_record(shuffled, (0.0, 0.0), mode="octant")
        worst = max(worst, abs(r["straightness"] - base["straightness"])
                    / base["straightness"])
        assert r["total_km"] == pytest.approx(base["total_km"], rel=1e-9)
    assert worst < 1e-3, worst          # far below the null's own spread
    assert worst > 0.0                  # and not exactly zero, on a sphere


def test_planar_vector_sum_is_exactly_order_invariant():
    """The plane is where the commutativity argument is exact."""
    chain = "10167277007531177322735221647753"
    def flat(ch):
        x = y = 0.0
        for c in ch:
            b = math.radians(45 * int(c, 8))
            x += math.sin(b); y += math.cos(b)
        return math.hypot(x, y) / len(ch)
    base = flat(chain)
    rng = random.Random(9)
    for _ in range(50):
        assert flat("".join(rng.sample(chain, len(chain)))) ==             pytest.approx(base, abs=1e-12)


def test_relative_mode_straightness_does_depend_on_order():
    """The mode where the test is meaningful. Order must matter here."""
    chain = "10167277007531177322735221647753"
    base = route.route_record(chain, (0.0, 0.0), mode="octant_relative")
    rng = random.Random(6)
    differs = 0
    for _ in range(25):
        shuffled = "".join(rng.sample(chain, len(chain)))
        r = route.route_record(shuffled, (0.0, 0.0), mode="octant_relative")
        if abs(r["straightness"] - base["straightness"]) > 1e-6:
            differs += 1
    assert differs >= 20


# ------------------------------------------------------------ the null

def test_random_walk_null_matches_theory():
    """A random walk drifts ~sqrt(n) steps, so straightness ~ 1/sqrt(n)."""
    for n in (10, 20, 35):
        c = route.coherence("0" * n, (0.0, 0.0), trials=300, seed=3)
        assert c["straightness_null_mean"] == pytest.approx(1 / math.sqrt(n),
                                                            abs=0.08)
        assert c["turn_null_mean"] == pytest.approx(90.0, abs=4.0)


def test_the_recorded_null_holds_for_this_specimen():
    """R10.63 N5: no split beats a permutation null in relative mode.

    Kept small enough to run in CI; the full 3000-shuffle sweep is in
    negative_results/R1063_WIDE_ENVELOPE_NULLS.md.
    """
    rng = random.Random(41)
    hits = 0
    tested = 0
    for d_left in (9, 11, 17, 21, 25):
        f = route.parse_payload(PAYLOAD, d_left)
        chain = f["chain_left"]
        start = route.start_from_surface(f["S_tor"], f["S_pol"], f["S_rad"])
        obs = route.route_record(chain, start, mode="octant_relative")
        null = []
        for _ in range(400):
            sh = "".join(rng.sample(chain, len(chain)))
            null.append(route.route_record(
                sh, start, mode="octant_relative")["straightness"])
        p = sum(1 for x in null if x >= obs["straightness"]) / len(null)
        tested += 1
        if p < 0.05:
            hits += 1
    assert hits == 0, f"{hits}/{tested} splits beat the null; N5 would need revisiting"


def test_module_never_claims_the_semantics_are_known():
    r = route.route_record("0123456", (0.0, 0.0))
    assert r["geometry_is_exact"] is True
    assert r["chain_semantics_are_a_hypothesis"] is True
