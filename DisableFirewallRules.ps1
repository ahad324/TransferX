# Check if the script is running as Administrator
If (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    # If not running as admin, restart the script as admin
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

# Disable Firewall Rules if they are currently enabled

# TCP Inbound
$tcpInboundRule = netsh advfirewall firewall show rule name="Allow TCP Inbound"
if ($tcpInboundRule -match "No rules match the specified criteria") {
    Write-Host "TCP Inbound rule is already disabled."
} else {
    netsh advfirewall firewall delete rule name="Allow TCP Inbound"
    Write-Host "TCP Inbound rule disabled successfully!"
}

# TCP Outbound
$tcpOutboundRule = netsh advfirewall firewall show rule name="Allow TCP Outbound"
if ($tcpOutboundRule -match "No rules match the specified criteria") {
    Write-Host "TCP Outbound rule is already disabled."
} else {
    netsh advfirewall firewall delete rule name="Allow TCP Outbound"
    Write-Host "TCP Outbound rule disabled successfully!"
}

# UDP Inbound
$udpInboundRule = netsh advfirewall firewall show rule name="Allow UDP Inbound"
if ($udpInboundRule -match "No rules match the specified criteria") {
    Write-Host "UDP Inbound rule is already disabled."
} else {
    netsh advfirewall firewall delete rule name="Allow UDP Inbound"
    Write-Host "UDP Inbound rule disabled successfully!"
}

# UDP Outbound
$udpOutboundRule = netsh advfirewall firewall show rule name="Allow UDP Outbound"
if ($udpOutboundRule -match "No rules match the specified criteria") {
    Write-Host "UDP Outbound rule is already disabled."
} else {
    netsh advfirewall firewall delete rule name="Allow UDP Outbound"
    Write-Host "UDP Outbound rule disabled successfully!"
}

Write-Host "Firewall rules disabling process completed!"
Read-Host -Prompt "Press Enter to exit"

