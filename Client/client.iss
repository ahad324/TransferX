[Setup]
AppName=TransferX Client
AppVersion=1.0
DefaultDirName={pf}\TransferX Client
DefaultGroupName=TransferX Client
OutputDir=.\App
OutputBaseFilename=TransferXClientSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\client.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Logo\logo.ico"; DestDir: "{app}\Logo"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TransferX Client"; Filename: "{app}\client.exe"; IconFilename: "{app}\Logo\logo.ico"
Name: "{group}\Uninstall TransferX Client"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\client.exe"; Description: "Launch TransferX Client"; Flags: nowait postinstall skipifsilent