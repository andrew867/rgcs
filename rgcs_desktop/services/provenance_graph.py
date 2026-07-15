"""Mathematical provenance graph builder (RGCS v3, Agent 08).

Headless (Qt-free) view-model for the desktop provenance-graph viewer:
builds a nodes+edges graph from the three machine registries --

  - the frozen v2 registry `docs/model_registry.yaml` (RGCS-M.*),
  - the RSCS registry `rscs_core/registry/rscs_registry.yaml`
    (RSCS-C.*/RSCS-O.*),
  - the equation-provenance ledger `references/equation_provenance.yaml`
    (EP-* rows linking RSCS entries to their sources).

Node kinds: rgcs_equation, rscs_coordinate, rscs_operator, source, ep_row.
Edge kinds: adapts (EP -> source), feeds (EP -> RSCS id),
reproduces (RSCS id -> RGCS-M id). Every node carries its classification so
the UI can keep claims and source provenance visible (brief desktop rule 5).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[2]


def _load_yaml(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build_provenance_graph(repo_root: str | Path | None = None
                           ) -> dict[str, Any]:
    """Build the full provenance graph as {nodes: [...], edges: [...]}.

    Deterministic (sorted) so the viewer and tests get a stable layout
    seed. Raises loudly if a registry file is missing or malformed."""
    root = Path(repo_root) if repo_root else REPO
    rgcs = _load_yaml(root / "docs" / "model_registry.yaml")
    rscs = _load_yaml(root / "rscs_core" / "registry" / "rscs_registry.yaml")
    prov = _load_yaml(root / "references" / "equation_provenance.yaml")

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    for eq in rgcs.get("equations", rgcs.get("entries", [])):
        eq_id = eq.get("id") or eq.get("equation_id")
        if not eq_id:
            continue
        nodes[eq_id] = {"id": eq_id, "kind": "rgcs_equation",
                        "label": eq.get("name", eq_id),
                        "classification": eq.get("classification",
                                                 eq.get("class", "")),
                        "frozen": True}

    for coord in rscs.get("coordinates", []):
        nodes[coord["id"]] = {"id": coord["id"], "kind": "rscs_coordinate",
                              "label": coord.get("name", coord["id"]),
                              "classification": coord.get("class", ""),
                              "module": coord.get("module", ""),
                              "frozen": False}
    for op in rscs.get("operators", []):
        nodes[op["id"]] = {"id": op["id"], "kind": "rscs_operator",
                           "label": op.get("name", op["id"]),
                           "classification": op.get("class", ""),
                           "module": op.get("module", ""),
                           "frozen": False}
        for m_id in op.get("v2_reproduces", []) or []:
            edges.append({"from": op["id"], "to": m_id,
                          "kind": "reproduces"})

    entries = list(rscs.get("coordinates", [])) + list(
        rscs.get("operators", []))
    ep_targets: dict[str, list[str]] = {}
    for entry in entries:
        for ep in entry.get("provenance", []) or []:
            ep_targets.setdefault(ep, []).append(entry["id"])

    for eq in prov.get("equations", []):
        ep_id = eq["prov_id"]
        src_id = eq["source_id"]
        if src_id not in nodes:
            nodes[src_id] = {"id": src_id, "kind": "source",
                             "label": src_id, "classification": "SRC",
                             "frozen": True}
        nodes[ep_id] = {"id": ep_id, "kind": "ep_row",
                        "label": eq.get("name", ep_id),
                        "classification": "SRC-adapted",
                        "forbidden_transfer": eq.get("forbidden_transfer",
                                                     ""),
                        "frozen": True}
        edges.append({"from": ep_id, "to": src_id, "kind": "adapts"})
        for target in ep_targets.get(ep_id, []):
            edges.append({"from": ep_id, "to": target, "kind": "feeds"})

    node_ids = set(nodes)
    for e in edges:
        # 'reproduces' may point at frozen RGCS-M ids not present when the
        # v2 registry uses a different id field; create stubs, never drop
        for end in ("from", "to"):
            if e[end] not in node_ids:
                nodes[e[end]] = {"id": e[end], "kind": "rgcs_equation",
                                 "label": e[end], "classification": "",
                                 "frozen": True}
                node_ids.add(e[end])

    return {
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "edges": sorted(edges, key=lambda e: (e["from"], e["to"],
                                              e["kind"])),
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "by_kind": {k: sum(1 for n in nodes.values()
                               if n["kind"] == k)
                        for k in sorted({n["kind"]
                                         for n in nodes.values()})},
        },
    }
