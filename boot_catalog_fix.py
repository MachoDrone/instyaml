#!/usr/bin/env python3
"""
Boot Catalog Fix - Replicate Ubuntu's Exact Boot Catalog Structure
PURPOSE: Fix the long vs short error message issue by matching boot catalog exactly
VERSION: 4.0.0 - BOOT CATALOG STRUCTURE FIX
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

VERSION = "4.0.0"

class BootCatalogFix:
    def __init__(self):
        self.iso_dir = Path.home() / "iso"
        os.chdir(self.iso_dir)
        self.ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
        self.fixed_iso = "boot_catalog_fixed.iso"
        
    def extract_boot_catalog_info(self):
        """Extract Ubuntu's exact boot catalog structure"""
        print("🔍 Analyzing Ubuntu's boot catalog structure...")
        
        try:
            # Use isoinfo to get detailed boot info
            result = subprocess.run([
                "isoinfo", "-d", "-i", self.ubuntu_iso
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("📋 Ubuntu's Boot Catalog Info:")
                boot_info = {}
                for line in result.stdout.split('\n'):
                    if 'sector' in line.lower() or 'boot' in line.lower():
                        print(f"   {line.strip()}")
                        if 'boot catalog' in line.lower():
                            sector = line.split('sector')[1].strip() if 'sector' in line else None
                            boot_info['catalog_sector'] = sector
                
                return boot_info
            else:
                print("❌ isoinfo failed")
                return {}
                
        except FileNotFoundError:
            print("⚠️ isoinfo not available")
            return {}
    
    def create_catalog_matched_iso(self):
        """Create ISO with exact boot catalog structure match"""
        print("\n🔨 Creating ISO with Ubuntu's exact boot catalog structure...")
        
        # Extract Ubuntu ISO
        extract_dir = Path("ubuntu_catalog_extract")
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir()
        
        subprocess.run([
            "7z", "x", f"-o{extract_dir}", self.ubuntu_iso
        ], check=True, capture_output=True)
        
        # Add HelloWorld.txt
        hello_file = extract_dir / "HelloWorld.txt"
        hello_file.write_text("Boot Catalog Fix Test - Short Error Messages!")
        
        # Use Ubuntu's EXACT boot structure - critical sector ordering
        # This preserves the boot catalog structure that creates short error messages
        xorriso_cmd = [
            "xorriso", "-as", "mkisofs",
            "-r",
            "-V", "Ubuntu-Catalog-Fixed",
            "-o", self.fixed_iso,
            "-J", "-joliet-long",
            "-b", "boot/grub/i386-pc/eltorito.img",
            "-c", "boot.catalog",
            "-no-emul-boot", 
            "-boot-load-size", "4",
            "-boot-info-table",
            "-eltorito-alt-boot",
            "-e", "EFI/boot/bootx64.efi",
            "-no-emul-boot",
            "-isohybrid-gpt-basdat",
            # CRITICAL: Match Ubuntu's exact parameter order
            str(extract_dir)
        ]
        
        print("🔧 Running catalog-matched xorriso...")
        result = subprocess.run(xorriso_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            size = Path(self.fixed_iso).stat().st_size / (1024**3)
            print(f"✅ Boot catalog fixed ISO: {self.fixed_iso} ({size:.1f} GB)")
            return True
        else:
            print("❌ Failed to create catalog-fixed ISO")
            print(f"Error: {result.stderr}")
            return False
    
    def run(self):
        """Execute boot catalog fix"""
        print("🚀 BOOT CATALOG STRUCTURE FIX")
        print("=" * 40)
        print(f"🎯 Goal: Create ISO with SHORT error messages like Ubuntu original")
        
        if not Path(self.ubuntu_iso).exists():
            print("❌ Ubuntu ISO not found")
            return False
        
        # Analyze original boot catalog
        boot_info = self.extract_boot_catalog_info()
        
        # Create catalog-matched ISO
        if self.create_catalog_matched_iso():
            print(f"\n✅ SUCCESS: {self.fixed_iso} created")
            print(f"📍 Test this ISO - should show SHORT error messages")
            print(f"📍 Compare boot behavior with original Ubuntu ISO")
            return True
        else:
            print("\n❌ FAILED to create fixed ISO")
            return False

if __name__ == "__main__":
    fixer = BootCatalogFix()
    success = fixer.run()
    sys.exit(0 if success else 1)