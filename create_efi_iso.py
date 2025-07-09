#!/usr/bin/env python3
"""
Minimal EFI Bootable ISO Creator with HelloWorld.txt Injection
Purpose: Prove EFI boot functionality with minimal file injection
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

class MinimalEFIISOCreator:
    def __init__(self):
        self.work_dir = Path("work")
        self.extract_dir = self.work_dir / "extracted"
        self.output_iso = "helloefi.iso"
        self.ubuntu_iso_url = "https://releases.ubuntu.com/24.04.2/ubuntu-24.04.2-desktop-amd64.iso"
        self.ubuntu_iso = "ubuntu-24.04.2-desktop-amd64.iso"
        
    def check_dependencies(self):
        """Check if required tools are available"""
        print("🔍 Checking dependencies...")
        required = ["xorriso", "7z"]
        missing = []
        
        for tool in required:
            if shutil.which(tool) is None:
                missing.append(tool)
        
        if missing:
            print(f"❌ Missing tools: {missing}")
            print("Install with: sudo apt install xorriso p7zip-full")
            return False
        
        print("✅ All dependencies available")
        return True
    
    def download_ubuntu_iso(self):
        """Download Ubuntu ISO if not present"""
        if Path(self.ubuntu_iso).exists():
            print(f"✅ {self.ubuntu_iso} already exists")
            return True
            
        print(f"📥 Downloading {self.ubuntu_iso}...")
        try:
            subprocess.run([
                "wget", "-O", self.ubuntu_iso, self.ubuntu_iso_url
            ], check=True)
            print("✅ Download complete")
            return True
        except subprocess.CalledProcessError:
            print("❌ Download failed")
            return False
    
    def extract_iso(self):
        """Extract Ubuntu ISO"""
        print(f"📂 Extracting {self.ubuntu_iso}...")
        
        # Clean and create directories
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        self.extract_dir.mkdir(parents=True)
        
        try:
            subprocess.run([
                "7z", "x", f"-o{self.extract_dir}", self.ubuntu_iso
            ], check=True)
            print("✅ Extraction complete")
            return True
        except subprocess.CalledProcessError:
            print("❌ Extraction failed")
            return False
    
    def inject_helloworld(self):
        """Inject HelloWorld.txt file"""
        print("📝 Injecting HelloWorld.txt...")
        
        hello_file = self.extract_dir / "HelloWorld.txt"
        hello_content = """Hello World from Custom EFI ISO!

This file proves that:
✅ File injection works
✅ ISO customization successful
✅ EFI boot structure preserved

Created by: MinimalEFIISOCreator
Date: $(date)
Purpose: Verify EFI bootable ISO creation
"""
        
        hello_file.write_text(hello_content)
        print(f"✅ HelloWorld.txt created at {hello_file}")
        return True
    
    def verify_efi_structure(self):
        """Verify EFI boot structure exists"""
        print("🔍 Verifying EFI structure...")
        
        efi_boot_file = self.extract_dir / "EFI" / "boot" / "bootx64.efi"
        boot_catalog = self.extract_dir / "boot" / "grub" / "i386-pc" / "eltorito.img"
        
        if not efi_boot_file.exists():
            print(f"❌ Missing: {efi_boot_file}")
            return False
            
        if not boot_catalog.exists():
            print(f"❌ Missing: {boot_catalog}")
            return False
            
        print("✅ EFI structure verified")
        print(f"  - EFI boot file: {efi_boot_file}")
        print(f"  - BIOS boot file: {boot_catalog}")
        return True
    
    def create_efi_iso(self):
        """Create EFI bootable ISO using xorriso"""
        print("🏗️ Creating EFI bootable ISO...")
        
        # Ubuntu 24.04.2 requires specific EFI boot parameters
        xorriso_cmd = [
            "xorriso", "-as", "mkisofs",
            "-r",
            "-V", "HelloEFI Ubuntu 24.04.2",
            "-J", "-joliet-long",
            "-b", "boot/grub/i386-pc/eltorito.img",
            "-c", "boot.catalog",
            "-no-emul-boot",
            "-boot-load-size", "4",
            "-boot-info-table",
            "-eltorito-alt-boot",
            "-e", "EFI/boot/bootx64.efi",  # CRITICAL: Direct EFI file for Ubuntu 24.04.2
            "-no-emul-boot",
            "-isohybrid-gpt-basdat",
            "-partition_offset", "16",
            "-o", self.output_iso,
            str(self.extract_dir)
        ]
        
        print("Running xorriso command:")
        print(" ".join(xorriso_cmd))
        
        try:
            result = subprocess.run(xorriso_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ ISO creation successful")
                iso_size = Path(self.output_iso).stat().st_size / (1024*1024*1024)
                print(f"📊 Output: {self.output_iso} ({iso_size:.1f} GB)")
                return True
            else:
                print("❌ ISO creation failed")
                print("STDERR:", result.stderr)
                return False
        except subprocess.CalledProcessError as e:
            print(f"❌ xorriso failed: {e}")
            return False
    
    def verify_injection(self):
        """Verify HelloWorld.txt was included in ISO"""
        print("🔍 Verifying file injection...")
        
        try:
            result = subprocess.run([
                "7z", "l", self.output_iso, "HelloWorld.txt"
            ], capture_output=True, text=True)
            
            if "HelloWorld.txt" in result.stdout:
                print("✅ HelloWorld.txt found in ISO")
                return True
            else:
                print("❌ HelloWorld.txt NOT found in ISO")
                return False
        except subprocess.CalledProcessError:
            print("❌ ISO verification failed")
            return False
    
    def cleanup(self):
        """Clean up work directory"""
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
            print("🧹 Cleanup complete")
    
    def run(self):
        """Main execution flow"""
        print("🚀 Minimal EFI ISO Creator Starting...")
        print("=" * 50)
        
        steps = [
            ("Check Dependencies", self.check_dependencies),
            ("Download Ubuntu ISO", self.download_ubuntu_iso),
            ("Extract ISO", self.extract_iso),
            ("Inject HelloWorld.txt", self.inject_helloworld),
            ("Verify EFI Structure", self.verify_efi_structure),
            ("Create EFI ISO", self.create_efi_iso),
            ("Verify Injection", self.verify_injection),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 Step: {step_name}")
            if not step_func():
                print(f"❌ FAILED: {step_name}")
                self.cleanup()
                return False
        
        print("\n🎉 SUCCESS: EFI bootable ISO created!")
        print(f"📁 Output: {self.output_iso}")
        print("\n🧪 Next Steps:")
        print("1. Test EFI boot in VirtualBox/QEMU")
        print("2. Verify HelloWorld.txt is accessible")
        print("3. Confirm Ubuntu boots normally")
        
        return True

if __name__ == "__main__":
    creator = MinimalEFIISOCreator()
    success = creator.run()
    sys.exit(0 if success else 1)