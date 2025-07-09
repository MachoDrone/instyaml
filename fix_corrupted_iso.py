#!/usr/bin/env python3
"""
Fix Corrupted ISO - Download Fresh Ubuntu Server ISO
Purpose: Detect and fix corrupted ISO downloads
"""

import os
import sys
import subprocess
import hashlib
from pathlib import Path

class ISOIntegrityFixer:
    def __init__(self):
        # Use ~/iso as working directory to match user's workflow
        self.iso_dir = Path.home() / "iso"
        self.iso_dir.mkdir(exist_ok=True)
        os.chdir(self.iso_dir)
        
        self.ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
        self.expected_size = 3213064192  # Official Ubuntu Server size
        self.expected_sha256 = "9a17ce2b9bbf82e8dc3b5b3d2e6d3de76b0c2c937c7c9bd6e2b7f0b2c4b5e9d8"  # Example
        
        # Multiple download mirrors
        self.mirrors = [
            "https://releases.ubuntu.com/24.04.2/ubuntu-24.04.2-live-server-amd64.iso",
            "https://mirror.pilotfiber.com/ubuntu-iso/24.04.2/ubuntu-24.04.2-live-server-amd64.iso", 
            "https://ubuntu.osuosl.org/releases/24.04.2/ubuntu-24.04.2-live-server-amd64.iso",
            "https://mirror.genesishosting.com/ubuntu-releases/24.04.2/ubuntu-24.04.2-live-server-amd64.iso",
            "https://ubuntu.mirror.constant.com/releases/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
        ]
    
    def check_iso_integrity(self):
        """Check if ISO file exists and has correct size"""
        print("🔍 Checking ISO integrity...")
        
        if not Path(self.ubuntu_iso).exists():
            print(f"❌ ISO file not found: {self.ubuntu_iso}")
            return False
            
        file_size = Path(self.ubuntu_iso).stat().st_size
        print(f"📊 File size: {file_size:,} bytes ({file_size/(1024**3):.2f} GB)")
        print(f"📊 Expected: {self.expected_size:,} bytes ({self.expected_size/(1024**3):.2f} GB)")
        
        if file_size != self.expected_size:
            print(f"❌ Size mismatch! File is corrupted.")
            print(f"   Difference: {abs(file_size - self.expected_size):,} bytes")
            return False
            
        print("✅ File size correct")
        return True
    
    def test_iso_extraction(self):
        """Quick test to see if ISO can be read"""
        print("🧪 Testing ISO readability...")
        
        try:
            result = subprocess.run([
                "7z", "l", self.ubuntu_iso
            ], capture_output=True, text=True, timeout=30)
            
            if "ERROR" in result.stdout or result.returncode != 0:
                print("❌ ISO has read errors")
                return False
                
            print("✅ ISO readable")
            return True
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print("❌ ISO read test failed")
            return False
    
    def remove_corrupted_iso(self):
        """Remove corrupted ISO file"""
        print("🗑️ Removing corrupted ISO...")
        
        if Path(self.ubuntu_iso).exists():
            Path(self.ubuntu_iso).unlink()
            print(f"✅ Removed: {self.ubuntu_iso}")
        
        # Also remove any partial downloads
        for pattern in ["*.part", "*.tmp", "*.download"]:
            for file in Path(".").glob(pattern):
                file.unlink()
                print(f"✅ Removed partial: {file}")
    
    def download_fresh_iso(self):
        """Download fresh ISO from working mirror"""
        print("📥 Downloading fresh Ubuntu Server ISO...")
        
        for i, mirror_url in enumerate(self.mirrors, 1):
            print(f"\n🌍 Trying mirror {i}/{len(self.mirrors)}: {mirror_url}")
            
            try:
                # Use wget with resume capability and progress
                result = subprocess.run([
                    "wget",
                    "--continue",           # Resume downloads
                    "--progress=bar",       # Show progress
                    "--timeout=30",         # Connection timeout
                    "--tries=3",           # Retry attempts
                    "-O", self.ubuntu_iso,
                    mirror_url
                ], timeout=1800)  # 30 minute timeout
                
                if result.returncode == 0:
                    print(f"✅ Download completed from mirror {i}")
                    return True
                else:
                    print(f"❌ Download failed from mirror {i}")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ Download timeout from mirror {i}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Download error from mirror {i}: {e}")
        
        print("❌ All mirrors failed")
        return False
    
    def verify_download(self):
        """Verify the downloaded ISO"""
        print("\n🔍 Verifying downloaded ISO...")
        
        # Check size again
        if not self.check_iso_integrity():
            return False
            
        # Quick extraction test
        if not self.test_iso_extraction():
            return False
            
        print("✅ ISO verification passed!")
        return True
    
    def run(self):
        """Main execution flow"""
        print("🚀 ISO Integrity Fixer")
        print("=" * 40)
        print(f"📂 Working in: {os.getcwd()}")
        
        # Check current ISO
        if self.check_iso_integrity() and self.test_iso_extraction():
            print("✅ Current ISO is valid - no action needed")
            return True
        
        print("\n🚨 Corrupted ISO detected!")
        
        # Remove corrupted file
        self.remove_corrupted_iso()
        
        # Download fresh copy
        if not self.download_fresh_iso():
            print("❌ Failed to download fresh ISO")
            return False
        
        # Verify new download
        if not self.verify_download():
            print("❌ New ISO also corrupted")
            return False
        
        print("\n🎉 SUCCESS: Fresh ISO downloaded and verified!")
        print(f"📁 Ready: {self.ubuntu_iso}")
        print("\n🚀 Next step: Run complete EFI solution again")
        return True

if __name__ == "__main__":
    fixer = ISOIntegrityFixer()
    success = fixer.run()
    sys.exit(0 if success else 1)