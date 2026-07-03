; Optional: builds a distributable MarkItDown-1.0-Setup.exe.
; Needs Inno Setup (https://jrsoftware.org/isdl.php). build.bat runs this
; automatically if ISCC is found; otherwise use install.bat (no tooling needed).
#define AppName "MarkItDown"
#define AppVersion "1.0"
#define AppExe "MarkItDownGUI.exe"

[Setup]
AppId={{6F3A2C7E-2B4D-4E9A-9C21-A1B2C3D4E5F6}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=MarkItDown GUI
DefaultDirName={autopf}\MarkItDown
DefaultGroupName=MarkItDown
UninstallDisplayIcon={app}\{#AppExe}
OutputDir=dist
OutputBaseFilename=MarkItDown-{#AppVersion}-Setup
SetupIconFile=icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\MarkItDownGUI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\MarkItDown"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\MarkItDown"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch MarkItDown"; Flags: nowait postinstall skipifsilent
