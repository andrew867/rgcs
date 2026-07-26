# RGCS Lab CLI

`rgcs-lab` exposes deterministic public demonstrator receipts for Codex-owned
core modules:

```bash
rgcs-lab doctor
rgcs-lab golay demo --random-flips 3
rgcs-lab frames example earth-south-up
rgcs-lab memory benchmark examples/rgcs_lab/memory
rgcs-lab dual-pole audit examples/rgcs_lab/claim_yellow.json
rgcs-lab lattice run --steps 100
rgcs-lab metasurface sweep --points 9
```

All commands emit canonical JSON. Lattice receipts report dimensionless modal
norm ledgers. Metasurface receipts report SI units and explicitly warn that the
reduced-order electromagnetic model does not compute gravity.
