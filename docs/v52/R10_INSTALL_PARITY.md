# R10 P20 — runtime, wheel, sdist and clean-install parity

Phase P20, closing the artifact-facing half of P04.

## Why this exists

`SOURCE_ROOTS` (in `rgcs_desktop/build_meta.py`) governs the
build-freshness hash. `[tool.setuptools.packages.find].include` (in
`pyproject.toml`) governs what `pip install` puts on disk. They are two
lists, and until R9 nothing checked that they agreed.

They did not agree. The `include` list stopped at `r4`, so v4.9.0,
v5.0.0 and v5.1.0 each shipped a wheel containing **none** of `r6`,
`r7` or `r8` — the headline research packages of those very releases.
A clone hid it completely: `pythonpath = ["."]` in the pytest config
makes the source tree importable whether or not packaging agrees, so
every test passed on every platform while the published artifact was
missing thirty modules.

`tests/v52/test_r9_packaging.py` made the two lists agree by
assertion. That is a *configuration* test. This phase adds the
*artifact* test: build the real wheel and sdist, read what is inside
them, install into a virtualenv that cannot see the repository, and
import from that installed copy.

## Artifact matrix

Built on branch `v52-r10`, from a clean source export carrying the
`r10` packaging fix described under "Drift found". Wheel
`rgcs-5.2.1-py3-none-any.whl`, sdist `rgcs-5.2.1.tar.gz`.

Counts are `.py` files, excluding `__pycache__`.

| Package | on disk | in wheel | in sdist | imports from install |
|---|---:|---:|---:|---|
| `cspc` | 12 | 12 | 12 | yes |
| `fkey_instrument` | 10 | 10 | 10 | yes |
| `pmwr` | 8 | 8 | 8 | yes |
| `r3` | 8 | 8 | 8 | yes |
| `r4` | 9 | 9 | 9 | yes |
| `r6` | 16 | 16 | 16 | yes |
| `r7` | 9 | 9 | 9 | yes |
| `r8` | 6 | 6 | 6 | yes |
| `r9` | 6 | 6 | 6 | yes |
| `r10` | 6 | 6 | 6 | yes |
| `resonator_platform` | 16 | 16 | 16 | yes |
| `rgcs_core` | 26 | 26 | 26 | yes |
| `rgcs_desktop` | 49 | 49 | 49 | yes |
| `rgcs_workbench` | 5 | 5 | 5 | yes |
| `rscs2_core` | 59 | 59 | 59 | yes |
| `rscs_core` | 25 | 25 | 25 | yes |
| `consciousness_lane`\* | 3 | 3 | 3 | yes |

\* distributed but **not** in `SOURCE_ROOTS` — see "Drift found" below.

Package data: both declared data files are present in both artifacts
and load from the installed copy — `rscs_core/registry/rscs_registry.yaml`
and `rscs2_core/registry/rscs2_registry.yaml`. These are the only
non-`.py` files under any source root; there are no undeclared ones.

`top_level.txt` in the wheel lists all sixteen source roots plus
`consciousness_lane`. Every `.py` file on disk under a source root
reaches both artifacts; no file, and no subpackage at any depth, is
dropped.

## Commands run

Paths are shown as `$REPO` (the checkout) and `$SCRATCH` (a temporary
directory outside the checkout). Everything was built outside the
repository: the checkout lives on OneDrive, which intermittently locks
build artifacts, and building in place would also have polluted the
working tree.

Build tooling: Python 3.13.2, setuptools 83.0.0, `build` 1.5.0.

```sh
# 1. clean source export, outside the checkout
git archive HEAD | tar -x -C "$SCRATCH/src"

# 2. isolated build environment
python -m venv "$SCRATCH/buildenv"
"$SCRATCH/buildenv/Scripts/python" -m pip install --upgrade \
    pip build setuptools wheel

# 3. build both artifacts
"$SCRATCH/buildenv/Scripts/python" -m build \
    --outdir "$SCRATCH/dist" "$SCRATCH/src"

# 4. fresh environment with no repository on the path
python -m venv "$SCRATCH/instenv"
"$SCRATCH/instenv/Scripts/python" -m pip install "$SCRATCH/dist"/*.whl

# 5. import every package from the installed copy.
#    -E ignores PYTHONPATH, -s ignores user site-packages, and the
#    working directory is outside the checkout, so nothing can
#    satisfy an import from the source tree.
cd "$SCRATCH/elsewhere"
"$SCRATCH/instenv/Scripts/python" -E -s importcheck.py
```

Step 5 is the check that would have caught the original defect. Each
imported module's `__file__` is asserted to resolve inside the
environment's `site-packages`, not merely to import successfully —
importing successfully is exactly what the broken releases did from a
clone.

The guard added by this phase reproduces steps 1–3 automatically:

```sh
RGCS_R10_BUILD_PARITY=1 python -m pytest tests/v52/test_r10_install_parity.py
```

## What passed

* Both artifacts build cleanly from a clean export.
* Every package in `SOURCE_ROOTS` that exists on disk is present in
  **both** the wheel and the sdist, with a `.py` file count exactly
  matching the working tree. No package is missing; no package is
  partially shipped.
* All seventeen distributed top-level packages import from a fresh
  virtualenv with `-E -s` and a working directory outside the
  checkout, and every one resolves to `site-packages`.
* Submodule smoke: all five `r9` submodules and all five `r10`
  submodules import from the installed copy.
* Both registry YAML files are present in the installed copy.
* `pip install` of the wheel pulls the declared runtime dependencies
  and needs nothing from the checkout.

## Drift found

**1. `r10` was in neither list.** (`R10-D-001`, fixed here.)

`r10/` — six modules, added during the R10 programme — was present in
the working tree but absent from both `SOURCE_ROOTS` and the packaging
`include` list. This is R8-D-006 and R9-D-004 starting over one
generation later, from the same cause: a new research package added to
the tree and not to the two lists that govern hashing and
distribution. Left alone it would have produced a fourth release
shipping a wheel without its own headline package, and a build-freshness
hash that did not respond to `r10` changing.

The guards caught it rather than a release doing so —
`tests/v51/test_r8_source_coverage.py::test_every_package_is_covered_by_the_source_hash`
failed as soon as the directory appeared. That is the mechanism
working as designed. `r10` has been added to `SOURCE_ROOTS` and to the
`include` list, and the rebuilt artifacts carry all six modules.

Adding `r10` to `SOURCE_ROOTS` changes `compute_source_hash`. Nothing
in-tree pins that value: the stale `_build_stamp.json` at the repo root
is only compared against live source by `tests/v4/test_v45_frozen.py`,
which skips unless a frozen `dist/RGCSWorkbench.exe` is present. The
next freeze will stamp the new hash. This is the intended behaviour —
a new package *must* invalidate a previously frozen dist.

**2. `consciousness_lane` ships but is not hashed.** (Open; a decision,
not a bug.)

The quarantined theory lane is matched by the packaging `include`
list, so it is in both artifacts, in `top_level.txt`, and importable
after `pip install`. It is not in `SOURCE_ROOTS`, so a change to it
does not invalidate a frozen dist. This is the *mirror* of R8-D-006: a
package that ships without being covered by the freshness hash.

The asymmetry is defensible — the hash protects the provenance of the
frozen desktop app, and the lane is not bundled into that binary
(`packaging/RGCSWorkbench.spec` does not reference it) — but it was
implicit, and the comment on the `EXCLUDED` entry in
`tests/v51/test_r8_source_coverage.py` asserts the lane is "not
shipped", which is true of the frozen app and **false of the wheel**.

This has not been changed unilaterally, because both available fixes
carry release consequences: adding it to `SOURCE_ROOTS` widens the
freshness hash, and removing it from `include` withdraws a package that
v5.1.0 and v5.2.x wheels already installed. It is now named explicitly
in `DISTRIBUTED_NOT_HASHED` in the new guard, with the reasoning
attached, so that a *second* such package cannot appear silently. The
stale comment in the R8 test should be corrected whichever way the
decision goes.

## The guard

`tests/v52/test_r10_install_parity.py`, ten tests in two tiers.

**Tier 1 (eight tests, always runs, needs only setuptools)** checks the
properties that determine artifact contents before any build happens:

* the wheel package set covers every existing `SOURCE_ROOTS` entry;
* coverage holds at *every level of nesting* — a top-level package can
  ship while one of its subpackages is missing, and the parent still
  imports, so the gap surfaces only when someone imports the child.
  Nothing was checking below the first level;
* no package would be dropped for want of an `__init__.py`.
  `find_packages` cannot see a PEP 420 namespace package but a clone
  imports it fine — this is R9-D-003, and it is how a future `r11`
  added the way `r9` was would go missing from the wheel;
* every `.py` file under a source root lands inside a discovered
  package;
* every non-`.py` file under a source root is declared in
  `[tool.setuptools.package-data]`, or the installed copy imports
  cleanly and fails at first read;
* the sdist is governed by the same package set as the wheel, and no
  `MANIFEST.in` exclusion narrows it (there is no `MANIFEST.in` today;
  the test is armed for the day there is one);
* anything distributed but outside the freshness hash is named
  explicitly with a reason.

**Tier 2 (two tests, opt-in)** builds a real wheel and sdist and reads
their manifests, asserting per-package `.py` counts against the working
tree and checking `top_level.txt`. It is gated behind
`RGCS_R10_BUILD_PARITY=1` because it needs the `build` package and
writes `build/` and `*.egg-info` into the checkout. Both tier-2 tests
have been run and pass; they are not left unverified.

### Collection safety

R9-D-020 is the governing constraint. `tests/v52/test_r9_packaging.py`
once imported setuptools at module level; setuptools is a build-system
requirement, not a runtime one, and it is absent from CI's portable
job — so that module failed *collection* on all three CI platforms
while passing locally, where the venv happened to have it. A packaging
guard that cannot run in CI is not a guard.

This module repeats none of that: setuptools comes in through
`pytest.importorskip`, and `build` through a guarded import feeding a
`skipif`. On a machine with neither, the file skips cleanly. Verified:
tier 1 runs and tier 2 skips under the project venv (which has no
`build`); all ten pass under an environment that has both.

## Status

P20 artifact matrix, installed-file inventory and portable smoke
receipts: **complete and green**. One live packaging defect (`r10`)
found and fixed. One documented asymmetry (`consciousness_lane`) made
explicit and left for an operator decision.
