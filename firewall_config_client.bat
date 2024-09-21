@echo off
echo Configuring firewall for TransferX Client...

:: Allow outgoing TCP connections from TransferX.exe
netsh advfirewall firewall add rule name="TransferX Client (TCP Out)" dir=out action=allow program="%~dp0TransferX.exe" protocol=TCP

:: Allow incoming TCP connections to TransferX.exe
netsh advfirewall firewall add rule name="TransferX Client (TCP In)" dir=in action=allow program="%~dp0TransferX.exe" protocol=TCP

:: Allow outgoing UDP connections for server discovery
netsh advfirewall firewall add rule name="TransferX Client Discovery (UDP Out)" dir=out action=allow protocol=UDP remoteport=5000

:: Allow incoming UDP connections for server discovery responses
netsh advfirewall firewall add rule name="TransferX Client Discovery (UDP In)" dir=in action=allow protocol=UDP localport=5000

echo Firewall rules added for TransferX Client.
echo If you still experience connection issues, please check your antivirus settings.
pause