; Inno Setup script - WeighLock installer
#define MyAppName "Weigh Lock"
#define MyAppVersion "1.0.0"
#define MyAppExeName "WeighLock.exe"
[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={pf}\WeighLock
DefaultGroupName=Weigh Lock
OutputDir=installer_out
OutputBaseFilename=WeighLock_Setup_1.0.0
Compression=lzma
SolidCompression=yes
[Files]
Source: "dist\WeighLock.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\Weigh Lock"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\Weigh Lock"; Filename: "{app}\{#MyAppExeName}"
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Weigh Lock chalu korun"; Flags: nowait postinstall skipifsilent
