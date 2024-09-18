[Setup]
AppName=TransferX
AppVersion=0.0.5
DefaultDirName={pf}\TransferX
DefaultGroupName=TransferX
OutputDir=.\App
OutputBaseFilename=TransferX-v0.0.5
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

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  OldFilePath, NewFilePath: string;
begin
  if CurStep = ssInstall then
  begin
    OldFilePath := ExpandConstant('{app}\TransferX.exe');
    NewFilePath := ExpandConstant('{app}\TransferX_old.exe');
    if FileExists(OldFilePath) then
    begin
      FileCopy(OldFilePath, NewFilePath, False);
      DeleteFile(OldFilePath);
    end;
  end;
end;

[UninstallDelete]
Type: files; Name: "{app}\TransferX_old.exe"