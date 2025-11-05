# IAL Windows Installer
Write-Host "🚀 Installing IAL..." -ForegroundColor Green

if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Please run as Administrator" -ForegroundColor Red
    exit 1
}

$InstallDir = "C:\Program Files\IAL"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item "ialctl.exe" -Destination "$InstallDir\ialctl.exe" -Force

$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($CurrentPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$CurrentPath;$InstallDir", "Machine")
}

Write-Host "✅ IAL installed successfully!" -ForegroundColor Green
