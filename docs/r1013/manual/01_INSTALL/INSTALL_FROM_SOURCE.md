# Install from Source


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Clone and create an isolated environment

```bash
git clone https://github.com/andrew867/rgcs.git
cd rgcs
python -m venv .venv
```

Activate the environment and install:

```bash
python -m pip install -U pip
python -m pip install -e '.[desktop,workbook,dev]'
```

## Run the tests

```bash
python -m pytest
```

The test count changes by release. Do not hard-code an expected count in a user guide. Record the exact count in release notes and proof bundles.

## Verify package metadata

```bash
python -c "import importlib.metadata as m; print(m.version('rgcs'))"
```

## Build a wheel

```bash
python -m pip install build
python -m build
```

Install the wheel into a new environment. Do not use the source tree for the final clean-install test.
