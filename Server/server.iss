[Setup]
AppName=TransferX Server
AppVersion=1.0
DefaultDirName={pf}\TransferX Server
DefaultGroupName=TransferX Server
OutputDir=.\App
OutputBaseFilename=TransferXServerSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\server.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Logo\AppIcon.ico"; DestDir: "{app}\Logo"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TransferX Server"; Filename: "{app}\server.exe"; IconFilename: "{app}\Logo\AppIcon.ico"
Name: "{group}\Uninstall TransferX Server"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\server.exe"; Description: "Launch TransferX Server"; Flags: nowait postinstall skipifsilent