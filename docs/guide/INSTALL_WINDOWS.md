# Install on Windows

There are three ways to run RGCS on Windows. Use the first one that a given
release supports:

- **A. Installer** — a release that ships `RGCS-Workbench-<version>-Windows-x64-Setup.exe`.
- **B. Portable ZIP** — a release that ships `RGCS-Workbench-<version>-Windows-x64-portable.zip`.
- **C. From source** — any release, or none: install into a Python venv,
  exactly like Linux.

The installer and portable builds are **self-contained**: they bundle their
own Python and every dependency. You do not need Python installed to use A or
B. Both provide the desktop workbench and the bundled `rgcs-v4` /
`rgcs-workbook` tools.

Release assets are on the project's GitHub **Releases** page. Check the
version's assets list to see which of A/B are available.

---

## A. Installer (recommended)

Use when the release has `...-Windows-x64-Setup.exe`.

1. Download `RGCS-Workbench-<version>-Windows-x64-Setup.exe` from the release.
2. Run it. Windows SmartScreen may warn about an unrecognized publisher
   (the build is unsigned) — choose **More info → Run anyway** if you trust
   the source.
3. Follow the wizard. It installs the app and creates a **Start Menu**
   shortcut (RGCS Workbench).
4. Launch **RGCS Workbench** from the Start Menu. On first launch a
   **first-run wizard** creates your workspace at
   `%USERPROFILE%\Documents\RGCS Workspace`.

**Verify the install** — open a terminal (PowerShell) and run the bundled
executable with a diagnostic flag (adjust the path to where it installed,
typically under `%LOCALAPPDATA%\Programs\RGCS Workbench\`):

```powershell
& "$env:LOCALAPPDATA\Programs\RGCS Workbench\RGCS-Workbench.exe" --doctor
& "$env:LOCALAPPDATA\Programs\RGCS Workbench\RGCS-Workbench.exe" --build-info
```

`--doctor` prints version, Python, platform, workspace, and dependency
status. `--build-info` prints the version, git commit, and source hash the
binary was built from (its provenance stamp).

**Uninstall** via *Settings → Apps → RGCS Workbench → Uninstall*, or the
entry's uninstaller. Your workspace folder is left in place; delete it
manually if you want it gone.

---

## B. Portable ZIP

Use when the release has `...-Windows-x64-portable.zip` (or when you prefer
no installer). This is the Windows equivalent of "extract and run".

1. Download `RGCS-Workbench-<version>-Windows-x64-portable.zip`.
2. Right-click the ZIP → **Extract All…** → choose a folder you can write to,
   e.g. `%USERPROFILE%\RGCS`. (Extract it fully — do **not** run the `.exe`
   from inside the ZIP viewer.)
3. Open the extracted folder and double-click **`RGCS-Workbench.exe`**.
4. First launch runs the same first-run wizard and creates
   `%USERPROFILE%\Documents\RGCS Workspace`.

No admin rights and no installation are required; delete the folder to remove
it. Verify the same way as above, from inside the extracted folder:

```powershell
cd $env:USERPROFILE\RGCS
.\RGCS-Workbench.exe --doctor
.\RGCS-Workbench.exe --build-info
```

> If SmartScreen or your antivirus quarantines the extracted `.exe`, allow it
> (unsigned PyInstaller builds are commonly flagged). Compare the download
> against the release's `SHA256SUMS.txt` if you want to confirm integrity.

---

## C. From source (same as Linux)

Use for any release, or when a release has **no** Windows binary. This is
identical to the Linux flow, with PowerShell activation.

### 1. Prerequisites

- **Python 3.11+** from python.org (during setup, tick **"Add python.exe to
  PATH"**), or from the Microsoft Store.
- **git** (optional — you can also download and extract a source ZIP).

Check the version (must be 3.11+):

```powershell
python --version
```

### 2. Get the source and enter it

```powershell
git clone https://github.com/andrew867/rgcs.git
cd rgcs
```

Or download the source ZIP from the release, extract it, and `cd` into the
folder.

### 3. Create and activate a venv

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks the activation script, allow it for your user once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

(Alternatively use `.\.venv\Scripts\activate.bat` from `cmd.exe`.)

### 4. Install

```powershell
# core CLI + importable packages
pip install -e .

# + desktop workbench and .xlsx export
pip install -e ".[desktop,workbook]"

# + test suite
pip install -e ".[desktop,workbook,dev]"
```

### 5. Verify and run

```powershell
rgcs-v4 --help
rgcs-v4 devices
rgcs-workbench --doctor        # if you installed the desktop extra
rgcs-workbench                 # launches the GUI (or: python -m rgcs_desktop)
```

Optional external tools behave as on Linux: **gmsh** on `PATH` for
`rgcs-v4 mesh`, an **OpenCL** runtime for `rgcs-v4 sweep --backend opencl`.

---

## Which do I have?

| The release page shows… | Do this |
|---|---|
| a `...Setup.exe` | **A. Installer** |
| only a `...portable.zip` | **B. Portable ZIP** |
| only source (`.zip` / `.tar.gz`), or nothing | **C. From source** |

After installing, continue with [Configuration](CONFIGURATION.md) and
[Using the desktop app](USING_THE_DESKTOP_APP.md).
