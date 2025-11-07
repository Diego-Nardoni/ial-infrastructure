#!/bin/bash
# Build IAL v3.1 for Windows

echo "🚀 Building IAL v3.1 for Windows..."

# Check if we're in the right directory
if [[ ! -f "../../natural_language_processor.py" ]]; then
    echo "❌ Please run from /home/ial/dist/windows/"
    exit 1
fi

cd ../../

# Activate virtual environment
source venv/bin/activate

# Install Windows build dependencies
pip install pyinstaller

# Build Windows executable
echo "📦 Building Windows executable..."
pyinstaller ialctl.spec --clean --onefile --distpath dist/windows/

# Copy to current directory
cp dist/windows/ialctl.exe dist/windows/ialctl.exe

# Update version
echo "3.1.0" > dist/windows/VERSION

echo "✅ Windows build complete!"
echo ""
echo "📦 Generated files:"
echo "  dist/windows/ialctl.exe - Windows executable"
echo "  dist/windows/install.ps1 - PowerShell installer"
echo ""
echo "🎯 Test installation:"
echo "  powershell -ExecutionPolicy Bypass -File install.ps1"
