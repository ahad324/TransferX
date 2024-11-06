[Setup]
AppName=TransferX Server
AppVersion = 0.0.1
DefaultDirName={pf}\TransferX Server
DefaultGroupName=TransferX Server
OutputDir=.\App
OutputBaseFilename=TransferXServer
Compression=lzma
SolidCompression=yes
SetupIconFile=..\Logo\AppIcon.ico
AppPublisher=AbdulAhad

[Files]
Source: "dist\TransferXServer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Logo\AppIcon.ico"; DestDir: "{app}\Logo"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".\update_launcher.bat"; DestDir: "{app}"; Flags: ignoreversion;
Source: "..\poppins.ttf"; DestDir: "{fonts}"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\TransferX Server"; Filename: "{app}\TransferXServer.exe"; IconFilename: "{app}\Logo\AppIcon.ico"
Name: "{group}\Uninstall TransferX Server"; Filename: "{uninstallexe}"
Name: "{userdesktop}\TransferX Server"; Filename: "{app}\TransferXServer.exe"; IconFilename: "{app}\Logo\AppIcon.ico"

[Registry]
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"; ValueType: string; ValueName: "Poppins"; ValueData: "poppins.ttf"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\TransferXServer.exe"; Description: "Launch TransferX Server"; Flags: nowait postinstall skipifsilent