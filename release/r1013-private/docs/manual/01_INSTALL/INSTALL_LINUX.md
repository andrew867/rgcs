# Install on Linux


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Source install

```bash
git clone https://github.com/andrew867/rgcs.git
cd rgcs
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[desktop,workbook,dev]'
```

Verify the current commands:

```bash
rgcs-v4 --help
rgcs-workbook --help
python -m rgcs_desktop
```

Verify the R10.13 target command after implementation:

```bash
rgcs doctor
rgcs self-test
```

## Gmsh

Install the Gmsh executable or Python-provided console wrapper. RGCS uses it as an external process and exchanges files with it.

Test:

```bash
gmsh --version
```

## Headless use

The CLI can run without the desktop extra. For a server:

```bash
python -m pip install -e '.[workbook]'
```

A full FEM solve can consume substantial memory. Begin with a coarse `clmax_mm` and a small mode count.
