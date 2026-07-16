# V4 Agent Dependency Graph (Agent B0)

```mermaid
graph TD
  B0[B0 baseline] --> M1[M1 sources/provenance]
  B0 --> M2[M2 capability firewall]
  M1 --> M2
  M2 --> M3[M3 torsion/OAM/chirality]
  M2 --> M4[M4 spin/exciton/magnon/phonon]
  M2 --> M5[M5 dynamic ME]
  M2 --> M6[M6 dynamic boundary/symmetry]
  M2 --> M7[M7 metacrystal]
  M2 --> M8[M8 calibration]
  M3 --> M4
  M1 --> M13[M13 FDT quarantine]
  M2 --> M11[M11 IOME LiNiPO4]
  M5 --> M11
  M2 --> M12[M12 nonlinear spin/exchange]
  M3 --> M14[M14 channel ablation]
  M11 --> M14
  M1 --> M10[M10 source lore]
  M3 --> M9[M9 eye expansion + 110mm]
  M6 --> M9
  M14 --> M9
  M9 --> D1[D1 docs/manuscript]
  M13 --> D1
  D1 --> Q1[Q1 adversarial QA]
  Q1 --> R1[R1 RC + release]
```

Machine-readable edge list: each edge is "consumer needs producer's
merged interfaces". Sequential execution order chosen (DV4C-004):

B0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M11 → M12 → M13 → M14 →
M10 → M9 → D1 → Q1 → R1

This is a valid topological order of the graph above.

## Shared-file ownership (orchestrator-owned)

`docs/v4/V4C_DECISION_LOG.md`, master registries under
`docs/v4/registers/`, `pyproject.toml` version, `CHANGELOG`/release
notes, `.github/workflows/ci.yml`, final proof-bundle manifest, tags.
Agents write only inside their declared paths (each agent's run log
declares them) and hand shared edits to the orchestrator.
