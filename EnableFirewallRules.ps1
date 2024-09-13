# Check if the script is running as Administrator
If (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    # If not running as admin, restart the script as admin
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

# Enable Firewall Rules if they are not already enabled

# TCP Inbound
$tcpInboundRule = netsh advfirewall firewall show rule name="Allow TCP Inbound"
if ($tcpInboundRule -match "No rules match the specified criteria") {
    netsh advfirewall firewall add rule name="Allow TCP Inbound" protocol=TCP dir=in action=allow
    Write-Host "TCP Inbound rule enabled successfully!"
} else {
    Write-Host "TCP Inbound rule is already enabled."
}

# TCP Outbound
$tcpOutboundRule = netsh advfirewall firewall show rule name="Allow TCP Outbound"
if ($tcpOutboundRule -match "No rules match the specified criteria") {
    netsh advfirewall firewall add rule name="Allow TCP Outbound" protocol=TCP dir=out action=allow
    Write-Host "TCP Outbound rule enabled successfully!"
} else {
    Write-Host "TCP Outbound rule is already enabled."
}

# UDP Inbound
$udpInboundRule = netsh advfirewall firewall show rule name="Allow UDP Inbound"
if ($udpInboundRule -match "No rules match the specified criteria") {
    netsh advfirewall firewall add rule name="Allow UDP Inbound" protocol=UDP dir=in action=allow
    Write-Host "UDP Inbound rule enabled successfully!"
} else {
    Write-Host "UDP Inbound rule is already enabled."
}

# UDP Outbound
$udpOutboundRule = netsh advfirewall firewall show rule name="Allow UDP Outbound"
if ($udpOutboundRule -match "No rules match the specified criteria") {
    netsh advfirewall firewall add rule name="Allow UDP Outbound" protocol=UDP dir=out action=allow
    Write-Host "UDP Outbound rule enabled successfully!"
} else {
    Write-Host "UDP Outbound rule is already enabled."
}

Write-Host "Firewall rules enabling process completed!"
Read-Host -Prompt "Press Enter to exit"
