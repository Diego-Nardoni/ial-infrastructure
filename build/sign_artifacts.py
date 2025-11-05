#!/usr/bin/env python3
"""
Digital signing and checksum generation for ialctl artifacts
"""

import os
import sys
import hashlib
import subprocess
import glob
from pathlib import Path

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def sign_file_gpg(filepath, gpg_key_id=None):
    """Sign a file with GPG"""
    try:
        cmd = ["gpg", "--detach-sign", "--armor"]
        if gpg_key_id:
            cmd.extend(["--local-user", gpg_key_id])
        cmd.append(filepath)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Signed: {filepath}")
            return True
        else:
            print(f"❌ Failed to sign {filepath}: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ GPG not found. Install GPG to enable signing.")
        return False

def generate_checksums(dist_dir):
    """Generate checksums.txt file for all artifacts"""
    checksums = []
    
    # Find all artifacts
    patterns = [
        "**/*.exe", "**/*.msi", "**/*.deb", "**/*.rpm", 
        "**/*.AppImage", "**/ialctl", "**/*.tar.gz", "**/*.zip"
    ]
    
    artifacts = []
    for pattern in patterns:
        artifacts.extend(glob.glob(os.path.join(dist_dir, pattern), recursive=True))
    
    # Calculate checksums
    for artifact in artifacts:
        if os.path.isfile(artifact):
            rel_path = os.path.relpath(artifact, dist_dir)
            checksum = calculate_sha256(artifact)
            checksums.append(f"{checksum}  {rel_path}")
            print(f"📋 Checksum: {rel_path}")
    
    # Write checksums file
    checksums_file = os.path.join(dist_dir, "checksums.txt")
    with open(checksums_file, "w") as f:
        f.write("\n".join(checksums) + "\n")
    
    print(f"✅ Checksums written to: {checksums_file}")
    return checksums_file

def main():
    """Main signing and checksum generation"""
    print("🔐 Signing artifacts and generating checksums...")
    
    # Get GPG key ID from environment or argument
    gpg_key_id = os.getenv("GPG_KEY_ID")
    if len(sys.argv) > 1:
        gpg_key_id = sys.argv[1]
    
    # Find dist directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    dist_dir = project_root / "dist"
    
    if not dist_dir.exists():
        print("❌ dist/ directory not found. Run build scripts first.")
        sys.exit(1)
    
    # Generate checksums
    checksums_file = generate_checksums(str(dist_dir))
    
    # Sign artifacts if GPG is available
    if gpg_key_id:
        print(f"🔐 Signing with GPG key: {gpg_key_id}")
        
        # Find all signable artifacts
        patterns = [
            "**/*.exe", "**/*.msi", "**/*.deb", "**/*.rpm", 
            "**/*.AppImage", "**/ialctl", "**/*.tar.gz", "**/*.zip"
        ]
        
        artifacts = []
        for pattern in patterns:
            artifacts.extend(glob.glob(os.path.join(dist_dir, pattern), recursive=True))
        
        # Sign each artifact
        signed_count = 0
        for artifact in artifacts:
            if os.path.isfile(artifact):
                if sign_file_gpg(artifact, gpg_key_id):
                    signed_count += 1
        
        # Sign checksums file
        if sign_file_gpg(checksums_file, gpg_key_id):
            signed_count += 1
        
        print(f"✅ Signed {signed_count} files")
    else:
        print("⚠️ No GPG key specified. Set GPG_KEY_ID environment variable to enable signing.")
        print("   Example: export GPG_KEY_ID=your-key-id")
    
    print("🎉 Artifact signing and checksum generation completed!")

if __name__ == "__main__":
    main()
