[Setup]
AppName=TransferX Server
AppVersion=0.0.6
DefaultDirName={pf}\TransferX Server
DefaultGroupName=TransferX Server
OutputDir=.\App
OutputBaseFilename=TransferXServer-v0.0.6
Compression=lzma
SolidCompression=yes
SetupIconFile=..\Logo\AppIcon.ico
AppPublisher=AbdulAhad

[Files]
Source: "dist\TransferXServer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Logo\AppIcon.ico"; DestDir: "{app}\Logo"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TransferX Server"; Filename: "{app}\TransferXServer.exe"; IconFilename: "{app}\Logo\AppIcon.ico"
Name: "{group}\Uninstall TransferX Server"; Filename: "{uninstallexe}"
Name: "{userdesktop}\TransferX Server"; Filename: "{app}\TransferXServer.exe"; IconFilename: "{app}\Logo\AppIcon.ico"

[Run]
Filename: "{app}\TransferXServer.exe"; Description: "Launch TransferX Server"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  OldFilePath, NewFilePath: string;
begin
  if CurStep = ssInstall then
  begin
    OldFilePath := ExpandConstant('{app}\TransferXServer.exe');
    NewFilePath := ExpandConstant('{app}\TransferXServer_old.exe');
    if FileExists(OldFilePath) then
    begin
      FileCopy(OldFilePath, NewFilePath, False);
      DeleteFile(OldFilePath);
    end;
  end;
end;

[UninstallDelete]
Type: files; Name: "{app}\TransferXServer_old.exe"