#define AppName "OpenPDF Studio"
#define AppVersion "40.6"
[Setup]
AppId={{A94653C4-3C6E-4B8D-BF1C-728A7EDB1C2A}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Abdelhalim Talbi
DefaultDirName={autopf}\OpenPDF Studio
DefaultGroupName=OpenPDF Studio
OutputDir=..\01-Application\binary\.staging-v40.6
OutputBaseFilename=OpenPDF-Studio-V40.6-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\OpenPDF-Studio.exe
[Files]
Source: "dist\OpenPDF-Studio\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
[Icons]
Name: "{group}\OpenPDF Studio"; Filename: "{app}\OpenPDF-Studio.exe"
Name: "{autodesktop}\OpenPDF Studio"; Filename: "{app}\OpenPDF-Studio.exe"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Creer un raccourci sur le bureau"; GroupDescription: "Raccourcis :"
[Run]
Filename: "{app}\OpenPDF-Studio.exe"; Description: "Lancer OpenPDF Studio"; Flags: nowait postinstall skipifsilent
