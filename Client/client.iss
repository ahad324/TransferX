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
AppPublisher=AbdulAhad

[Files]
Source: "dist\TransferX Client.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Logo\AppIcon.ico"; DestDir: "{app}\Logo"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TransferX Client"; Filename: "{app}\TransferX Client.exe"; IconFilename: "{app}\Logo\AppIcon.ico"
Name: "{group}\Uninstall TransferX Client"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\TransferX Client.exe"; Description: "Launch TransferX Client"; Flags: nowait postinstall skipifsilent