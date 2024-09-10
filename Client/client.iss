[Setup]
AppName=TransferX Client
AppVersion=1.0
DefaultDirName={pf}\TransferX Client
DefaultGroupName=TransferX Client
OutputDir=.\App
OutputBaseFilename=TransferXClientSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=..\Logo\AppIcon.ico

VersionInfoCompany=AbdulAhad
VersionInfoCopyright=Copyright © 2024 AbdulAhad

[Files]
Source: "dist\client.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Logo\AppIcon.ico"; DestDir: "{app}\Logo"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TransferX Client"; Filename: "{app}\client.exe"; IconFilename: "{app}\Logo\AppIcon.ico"
Name: "{group}\Uninstall TransferX Client"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\client.exe"; Description: "Launch TransferX Client"; Flags: nowait postinstall skipifsilent