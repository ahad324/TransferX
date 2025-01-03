[Setup]
AppName=TransferX
AppVersion = 1.0.0
DefaultDirName={pf}\TransferX
DefaultGroupName=TransferX
OutputDir=.\App
OutputBaseFilename=TransferX
Compression=lzma  
SolidCompression=yes
SetupIconFile=..\Logo\Logo.ico
AppPublisher=AbdulAhad

[Files]
Source: "dist\TransferX.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Logo\Logo.ico"; DestDir: "{app}\Logo"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".\update_launcher.bat"; DestDir: "{app}"; Flags: ignoreversion;
Source: "..\poppins.ttf"; DestDir: "{fonts}"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\TransferX"; Filename: "{app}\TransferX.exe"; IconFilename: "{app}\Logo\Logo.ico"
Name: "{group}\Uninstall TransferX"; Filename: "{uninstallexe}"
Name: "{userdesktop}\TransferX"; Filename: "{app}\TransferX.exe"; IconFilename: "{app}\Logo\Logo.ico"

[Registry]
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"; ValueType: string; ValueName: "Poppins"; ValueData: "poppins.ttf"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\TransferX.exe"; Description: "Launch TransferX"; Flags: nowait postinstall skipifsilent