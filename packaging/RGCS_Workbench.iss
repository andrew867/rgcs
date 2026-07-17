; Inno Setup script for RGCS Workbench (v4.5, P03).
;
; Per-user install (no admin). Tokens are supplied by
; tools/v45_build_windows.py via environment variables at compile time:
;   RGCS_VERSION      release version, e.g. 4.5.0
;   RGCS_BUILD_ROOT   the PyInstaller onedir (dist/RGCSWorkbench)
;   RGCS_OUTPUT_ROOT  where the compiled Setup EXE is written
;
; The build is UNSIGNED; this script deliberately declares no code
; signing so it can never imply a signature it does not have. The
; workbook is
; bundled inside BuildRoot\templates by the build tool, so it is copied
; by the recursive [Files] rule below (no fragile relative path).

#define MyAppName "RGCS Workbench"
#define MyAppVersion GetEnv("RGCS_VERSION")
#define MyAppPublisher "RGCS"
#define MyAppExeName "RGCSWorkbench.exe"
#define BuildRoot GetEnv("RGCS_BUILD_ROOT")
#define OutputRoot GetEnv("RGCS_OUTPUT_ROOT")

[Setup]
AppId={{C533D640-6298-4C52-8E57-2810AB465247}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\RGCS Workbench
DefaultGroupName=RGCS Workbench
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputRoot}
OutputBaseFilename=RGCS-Workbench-{#MyAppVersion}-Windows-x64-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ChangesAssociations=no
DisableProgramGroupPage=yes

[Files]
Source: "{#BuildRoot}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\RGCS Workbench"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\RGCS Diagnostics"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--doctor"
Name: "{autodesktop}\RGCS Workbench"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--first-run"; Description: "Launch RGCS Workbench"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; The per-user workspace lives in the user's Documents and is NOT
; removed on uninstall; user work is never destroyed silently.

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  { Data migrations belong in the application, not installer script. }
end;
