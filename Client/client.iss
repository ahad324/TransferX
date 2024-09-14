[Setup]
AppName=TransferX
AppVersion=1.4
DefaultDirName={pf}\TransferX
DefaultGroupName=TransferX
OutputDir=.\App
OutputBaseFilename=TransferX
Compression=lzma
SolidCompression=yes
SetupIconFile=..\Logo\AppIcon.ico
AppPublisher=AbdulAhad

[Files]
Source: "dist\TransferX.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Logo\AppIcon.ico"; DestDir: "{app}\Logo"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TransferX"; Filename: "{app}\TransferX.exe"; IconFilename: "{app}\Logo\AppIcon.ico"
Name: "{group}\Uninstall TransferX"; Filename: "{uninstallexe}"
Name: "{userdesktop}\TransferX"; Filename: "{app}\TransferX.exe"; IconFilename: "{app}\Logo\AppIcon.ico"

[Run]
Filename: "{app}\TransferX.exe"; Description: "Launch TransferX"; Flags: nowait postinstall skipifsilent