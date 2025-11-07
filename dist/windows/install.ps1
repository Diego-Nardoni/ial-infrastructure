# IAL Windows Installer v3.1
Write-Host "🚀 Installing IAL v3.1..." -ForegroundColor Green

if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Please run as Administrator" -ForegroundColor Red
    exit 1
}

# Check Node.js requirement
try {
    $nodeVersion = node --version 2>$null
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Node.js not found. Installing..." -ForegroundColor Yellow
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
}

# Install IAL
$InstallDir = "C:\Program Files\IAL"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item "ialctl.exe" -Destination "$InstallDir\ialctl.exe" -Force

# Update PATH
$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($CurrentPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$CurrentPath;$InstallDir", "Machine")
}

Write-Host "✅ IAL v3.1 installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Quick Start:" -ForegroundColor Cyan
Write-Host "  ialctl start        - Deploy IAL infrastructure" -ForegroundColor White
Write-Host "  ialctl configure    - Configure settings" -ForegroundColor White
Write-Host "  ialctl interactive  - Interactive mode" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation: https://github.com/Diego-Nardoni/ial-infrastructure" -ForegroundColor Blue
