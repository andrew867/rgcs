# RGCS Recursive Infrastructure Lab — Quick Start

## Install

```bash
python -m pip install -e ".[workbench,dev]"
rgcs-lab doctor
```

## Local server (loopback default)

```bash
rgcs-lab serve
```

Open http://127.0.0.1:8765/ — privacy banner reports `telemetry=False`.

Non-loopback binds require `--allow-remote`.

## Static hub (no server)

```bash
python tools/lab/build_static_hub.py
```

Open `static/hub/index.html` in a browser (`file://` works). Module pages load golden fixtures; they do not reimplement packet, Golay, quaternion, or solver mathematics in JavaScript.

## Example commands

```bash
rgcs-lab coordinate decode 165876523
rgcs-lab golay demo --random-flips 3
rgcs-lab frames earth-south-up
rgcs-lab memory benchmark --query "golay transport"
rgcs-lab dual-pole audit examples/lab/claim.json
rgcs-lab lattice run counterrotating-ring
rgcs-lab metasurface sweep
rgcs-lab predictions freeze examples/lab/prediction.json
rgcs-lab predictions verify examples/lab/prediction_frozen.json
```

## YELLOW lanes

Physical Earth projection, high-fidelity spoof-SPP, and prospective predictions remain **YELLOW** until measurement receipts exist. The hub shows these badges prominently.
