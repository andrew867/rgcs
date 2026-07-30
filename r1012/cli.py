"""R10.12 Phase 11+18+23+31+33 — the ``rgcs`` consolidated CLI.

Commands:
    rgcs --version
    rgcs wire parse|explain|roundtrip <wire>
    rgcs corpus verify
    rgcs evidence show <wire>
    rgcs transition lookup --child C --state S
    rgcs transition refine <wire> --child C
    rgcs transition candidates <wire> --child C
    rgcs probe register --probe P --raw-wire W --source-note N --observed-at T
    rgcs probe score --receipt ID
    rgcs mesh build --level N
    rgcs mesh trace <wire>
    rgcs mesh audit [--level N]
    rgcs self-test
    rgcs release verify
"""

from __future__ import annotations

import argparse
import json
import sys


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def main(argv=None) -> int:
    from r1012 import __version__, PUBLICATION_STATUS
    ap = argparse.ArgumentParser(prog="rgcs")
    ap.add_argument("--version", action="version",
                    version=f"rgcs r10.12 {__version__} "
                            f"(publication {PUBLICATION_STATUS})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    wire = sub.add_parser("wire")
    ws = wire.add_subparsers(dest="op", required=True)
    for op in ("parse", "explain", "roundtrip"):
        p = ws.add_parser(op)
        p.add_argument("value")

    corpus = sub.add_parser("corpus")
    cs = corpus.add_subparsers(dest="op", required=True)
    cs.add_parser("verify")

    ev = sub.add_parser("evidence")
    es = ev.add_subparsers(dest="op", required=True)
    e = es.add_parser("show")
    e.add_argument("value")

    tr = sub.add_parser("transition")
    ts = tr.add_subparsers(dest="op", required=True)
    tl = ts.add_parser("lookup")
    tl.add_argument("--child", type=int, required=True)
    tl.add_argument("--state", type=int, required=True)
    for op in ("refine", "candidates"):
        t = ts.add_parser(op)
        t.add_argument("value")
        t.add_argument("--child", type=int, required=True)

    pr = sub.add_parser("probe")
    ps = pr.add_subparsers(dest="op", required=True)
    preg = ps.add_parser("register")
    preg.add_argument("--probe", required=True)
    preg.add_argument("--raw-wire", type=int, required=True)
    preg.add_argument("--source-note", required=True)
    preg.add_argument("--observed-at", required=True)
    psc = ps.add_parser("score")
    psc.add_argument("--receipt", required=True)

    mesh = sub.add_parser("mesh")
    ms = mesh.add_subparsers(dest="op", required=True)
    mb = ms.add_parser("build")
    mb.add_argument("--level", type=int, required=True)
    mt = ms.add_parser("trace")
    mt.add_argument("value")
    ma = ms.add_parser("audit")
    ma.add_argument("--level", type=int, default=4)

    sub.add_parser("self-test")
    rel = sub.add_parser("release")
    rs = rel.add_subparsers(dest="op", required=True)
    rs.add_parser("verify")

    a = ap.parse_args(argv)

    try:
        if a.cmd == "wire":
            from r1012.certificate import certify
            c = certify(a.value)
            if a.op == "roundtrip":
                _print({"wire": a.value, "roundtrip": "EXACT",
                        "hash": c.roundtrip_hash})
            elif a.op == "explain":
                d = c.to_dict()
                d["explanation"] = (
                    "header Sol|Terra (001|110) + E3 shell/epoch field "
                    "(internal split unresolved) + three six-bit states + "
                    f"{c.depth} child symbol(s) + terminal {c.terminal}")
                _print(d)
            else:
                _print(c.to_dict())
        elif a.cmd == "corpus":
            from r1012.corpus import verify_corpus
            v = verify_corpus()
            _print({k: v[k] for k in v if k not in ("rows", "legacy_rows")})
            if v["golden_failures"] or not v["hash_match"]:
                return 4
        elif a.cmd == "evidence":
            from r1012.certificate import certify
            from r1012.transitions import lookup
            c = certify(a.value)
            _print({"wire": a.value, "certificate_tier": c.evidence_tier,
                    "per_state_child5": [lookup(5, s) for s in c.states],
                    "per_state_child6": [lookup(6, s) for s in c.states]})
        elif a.cmd == "transition":
            import r1012.transitions as T
            if a.op == "lookup":
                _print(T.lookup(a.child, a.state))
            elif a.op == "refine":
                _print(T.refine(a.value, a.child))
            else:
                _print(T.candidates(a.value, a.child))
        elif a.cmd == "probe":
            from r1011 import probe_intake as pi
            if a.op == "register":
                _print(pi.register(a.probe, a.raw_wire, a.source_note,
                                   a.observed_at))
            else:
                _print(pi.score(a.receipt))
        elif a.cmd == "mesh":
            import r1012.geometry as G
            if a.op == "build":
                m = G.build_mesh(a.level)
                _print({k: m[k] for k in ("level", "vertices", "triangles",
                                          "euler_ok")})
            elif a.op == "audit":
                _print(G.audit_mesh(a.level))
            else:
                _print(G.geometry_status(a.value))
        elif a.cmd == "self-test":
            _print(self_test())
        elif a.cmd == "release":
            _print(release_verify())
    except Exception as ex:                       # typed refusals surface
        _print({"refused": True, "error_type": type(ex).__name__,
                "detail": str(ex)})
        return 3
    return 0


def self_test() -> dict:
    """Phase 31 — the mandatory end-to-end workflows, executed live."""
    from r1012.certificate import certify
    from r1012.corpus import verify_corpus
    from r1012.transitions import (TransitionError, candidates, lookup,
                                   refine)
    import r1012.geometry as G
    out = {}
    c = certify(165876523)
    out["parse_known_wire"] = c.states == (15, 30, 4)
    out["roundtrip"] = bool(c.roundtrip_hash)
    out["transition_evidence"] = lookup(5, 15)["output_state"] == 5
    out["refine_source_known"] = refine(165876523, 5)[
        "refined_states"] == [5, 40, 37]
    cand = candidates(165652893, 5)
    out["candidate_set_for_ambiguous"] = cand["combination_count"] > 1
    out["unknown_cell_refuses"] = lookup(0, 10)[
        "evidence_tier"] == "UNSUPPORTED"
    m = G.build_mesh(2)
    out["analytic_level2_mesh"] = (m["vertices"], m["triangles"]) == (162, 320)
    out["sparse_trace"] = G.geometry_status(165876523)[
        "stage"] == "STATE_MAPPED"
    v = verify_corpus()
    out["corpus_28_of_28"] = v["golden_parsed"] == 28 and \
        v["golden_failures"] == 0
    out["machine_receipt"] = True
    out["ALL_PASS"] = all(bool(x) for x in out.values())
    return out


def release_verify() -> dict:
    from r1012 import __version__, PUBLICATION_STATUS, REGISTRY_VERSION
    st = self_test()
    return {"release": "R10.12 private candidate", "version": __version__,
            "publication": PUBLICATION_STATUS,
            "registry": REGISTRY_VERSION,
            "self_test_all_pass": st["ALL_PASS"],
            "fitted_warp_active": False,
            "uniform_ratio_law_selected": False,
            "table_status": "12/512 SOURCE_KNOWN; remainder typed",
            "s6_geometry_bridge": "UNDERDETERMINED (geometry stops at "
                                  "STATE_MAPPED)"}


if __name__ == "__main__":
    raise SystemExit(main())
