@echo off
echo Configuring firewall for TransferX Server...

:: Allow incoming TCP connections on port 5000
netsh advfirewall firewall add rule name="transferxserver" dir=in action=allow protocol=TCP localport=5000

:: Allow outgoing TCP connections from TransferXServer.exe
netsh advfirewall firewall add rule name="transferxserver" dir=out action=allow program="%~dp0TransferXServer.exe" protocol=TCP

:: Allow incoming UDP connections on port 5000 for discovery
netsh advfirewall firewall add rule name="transferxserver" dir=in action=allow protocol=UDP localport=5000

:: Allow outgoing UDP connections from TransferXServer.exe for discovery responses
netsh advfirewall firewall add rule name="transferxserver" dir=out action=allow program="%~dp0TransferXServer.exe" protocol=UDP

echo Firewall rules added for TransferX Server.
echo If you still experience connection issues, please check your antivirus settings.
pause