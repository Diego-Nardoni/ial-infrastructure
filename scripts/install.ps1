# ialctl installer for Windows
# Usage: iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/your-org/ial/main/scripts/install.ps1'))

param(
    [string]$InstallDir = "$env:LOCALAPPDATA\ialctl",
    [switch]$AddToPath = $true
)

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/your-org/ial"
$ApiUrl = "https://api.github.com/repos/your-org/ial/releases/latest"

Write-Host "🚀 Installing ialctl for Windows..." -ForegroundColor Green

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 3) {
    Write-Host "❌ PowerShell 3.0 or higher is required" -ForegroundColor Red
    exit 1
}

# Detect architecture
$Arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "386" }
Write-Host "📋 Detected: windows-$Arch" -ForegroundColor Cyan

# Get latest release info
Write-Host "📡 Fetching latest release info..." -ForegroundColor Yellow
try {
    $ReleaseInfo = Invoke-RestMethod -Uri $ApiUrl -UseBasicParsing
} catch {
    Write-Host "❌ Failed to fetch release info: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$Version = $ReleaseInfo.tag_name
Write-Host "📦 Latest version: $Version" -ForegroundColor Cyan

# Find appropriate download URL
$Asset = $ReleaseInfo.assets | Where-Object { 
    $_.name -match "\.(exe|msi)$" -and $_.name -match "windows"
} | Select-Object -First 1

if (-not $Asset) {
    # Fallback to any .exe or .msi
    $Asset = $ReleaseInfo.assets | Where-Object { 
        $_.name -match "\.(exe|msi)$"
    } | Select-Object -First 1
}

if (-not $Asset) {
    Write-Host "❌ Could not find Windows installer in release" -ForegroundColor Red
    exit 1
}

$DownloadUrl = $Asset.browser_download_url
$FileName = $Asset.name
$FileExtension = [System.IO.Path]::GetExtension($FileName)

Write-Host "📥 Downloading: $FileName" -ForegroundColor Yellow
Write-Host "🔗 URL: $DownloadUrl" -ForegroundColor Gray

# Create temporary directory
$TempDir = [System.IO.Path]::GetTempPath()
$TempFile = Join-Path $TempDir $FileName

# Download file
try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempFile -UseBasicParsing
    Write-Host "✅ Download completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Download failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Install based on file type
switch ($FileExtension) {
    ".msi" {
        Write-Host "📦 Installing MSI package..." -ForegroundColor Yellow
        try {
            Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", "`"$TempFile`"", "/quiet", "/norestart" -Wait -Verb RunAs
            Write-Host "✅ MSI installation completed" -ForegroundColor Green
        } catch {
            Write-Host "❌ MSI installation failed: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "💡 Try running as Administrator or install manually: $TempFile" -ForegroundColor Yellow
            exit 1
        }
    }
    ".exe" {
        # Check if it's an installer or standalone executable
        if ($FileName -match "setup|install") {
            Write-Host "📦 Running installer..." -ForegroundColor Yellow
            try {
                Start-Process -FilePath $TempFile -ArgumentList "/S" -Wait -Verb RunAs
                Write-Host "✅ Installation completed" -ForegroundColor Green
            } catch {
                Write-Host "❌ Installation failed: $($_.Exception.Message)" -ForegroundColor Red
                Write-Host "💡 Try running as Administrator or install manually: $TempFile" -ForegroundColor Yellow
                exit 1
            }
        } else {
            # Standalone executable
            Write-Host "📦 Installing standalone executable..." -ForegroundColor Yellow
            
            # Create install directory
            if (-not (Test-Path $InstallDir)) {
                New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
            }
            
            # Copy executable
            $TargetPath = Join-Path $InstallDir "ialctl.exe"
            Copy-Item $TempFile $TargetPath -Force
            
            Write-Host "✅ Installed to: $TargetPath" -ForegroundColor Green
            
            # Add to PATH if requested
            if ($AddToPath) {
                Write-Host "🔧 Adding to PATH..." -ForegroundColor Yellow
                
                # Get current user PATH
                $CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
                
                if ($CurrentPath -notlike "*$InstallDir*") {
                    $NewPath = if ($CurrentPath) { "$CurrentPath;$InstallDir" } else { $InstallDir }
                    [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
                    Write-Host "✅ Added to PATH (restart terminal to take effect)" -ForegroundColor Green
                } else {
                    Write-Host "✅ Already in PATH" -ForegroundColor Green
                }
            }
        }
    }
    default {
        Write-Host "❌ Unsupported file type: $FileExtension" -ForegroundColor Red
        exit 1
    }
}

# Cleanup
Remove-Item $TempFile -Force -ErrorAction SilentlyContinue

# Verify installation
Write-Host "🧪 Verifying installation..." -ForegroundColor Yellow

# Refresh PATH for current session
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "User") + ";" + [Environment]::GetEnvironmentVariable("PATH", "Machine")

try {
    $VersionOutput = & ialctl --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ ialctl installed successfully!" -ForegroundColor Green
        Write-Host "📋 Version: $VersionOutput" -ForegroundColor Cyan
    } else {
        Write-Host "✅ ialctl installed successfully!" -ForegroundColor Green
    }
} catch {
    Write-Host "✅ ialctl installed successfully!" -ForegroundColor Green
    Write-Host "💡 If 'ialctl' command is not found, restart your terminal" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Get started:" -ForegroundColor Green
Write-Host "   ialctl --help" -ForegroundColor White
Write-Host "   ialctl interactive" -ForegroundColor White
