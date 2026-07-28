# Install on Windows


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Recommended release install

Use the signed installer or portable archive when the R10.13 release candidate provides one. A packaged build contains Python and the required runtime.

1. Download the release artifact and `SHA256SUMS.txt`.
2. Verify the SHA-256 hash.
3. Install or extract to a folder that you can write to.
4. Start `rgcs-workbench`.
5. Run the doctor command from a terminal:

```powershell
rgcs doctor
```

## Source install

Install Python 3.11 or newer and Git. Then:

```powershell
git clone https://github.com/andrew867/rgcs.git
cd rgcs
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[desktop,workbook,dev]"
```

The current public entry points are:

```powershell
rgcs-v4 --help
rgcs-workbook --help
rgcs-workbench
```

The target release also provides:

```powershell
rgcs --help
```

## Optional tools

- Gmsh is required for three-dimensional mesh generation.
- An OpenCL runtime is optional for supported sweeps.
- OpenSCAD is optional for rendering the reference apparatus model.

RGCS must detect each optional tool. It must not silently substitute a different backend.
