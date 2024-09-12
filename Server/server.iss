[Setup]
AppName=TransferX Server
AppVersion=1.3
DefaultDirName={pf}\TransferX Server
DefaultGroupName=TransferX Server
OutputDir=.\App
OutputBaseFilename=TransferXServerSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=..\Logo\AppIcon.ico
AppPublisher=AbdulAhad

[Files]
Source: "dist\TransferX Server.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Logo\AppIcon.ico"; DestDir: "{app}\Logo"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TransferX Server"; Filename: "{app}\TransferX Server.exe"; IconFilename: "{app}\Logo\AppIcon.ico"
Name: "{group}\Uninstall TransferX Server"; Filename: "{uninstallexe}"
Name: "{userdesktop}\TransferX Server"; Filename: "{app}\TransferX Server.exe"; IconFilename: "{app}\Logo\AppIcon.ico"

[Run]
Filename: "{app}\TransferX Server.exe"; Description: "Launch TransferX Server"; Flags: nowait postinstall skipifsilent