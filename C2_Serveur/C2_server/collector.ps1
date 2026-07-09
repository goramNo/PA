$info = @{
    Hostname = $env:COMPUTERNAME
    Username = $env:USERNAME
    OS       = (Get-WmiObject Win32_OperatingSystem).Caption
    Users    = Get-LocalUser | Select-Object Name, Enabled, LastLogon, Description
    Date     = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$json = $info | ConvertTo-Json -Depth 4

# Sauvegarde locale (méthode qui marche à tous les coups)
$json | Out-File -FilePath "C:\Users\Public\results.json" -Encoding UTF8 -Force

Write-Host "[+] Fichier créé avec succès : C:\Users\Public\results.json"