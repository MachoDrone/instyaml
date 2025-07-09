#!/usr/bin/env python3
"""
ULTIMATE EFI ISO CREATOR - Clean Slate Approach
PURPOSE: Archive everything, start fresh, create working EFI ISO
VERSION: 3.0.0 - FINAL CLEAN SLATE SOLUTION
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

VERSION = "3.0.0"
SCRIPT_NAME = "ultimate_efi_creator.py"

class UltimateEFICreator:
    def __init__(self):
        self.home_dir = Path.home()
        self.iso_dir = self.home_dir / "iso"
        self.archive_dir = self.iso_dir / f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Target files
        self.ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
        self.ubuntu_url = "https://releases.ubuntu.com/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
        self.final_iso = "final_efi_working.iso"
        
    def show_header(self):
        """Show script header"""
        print("🚀 ULTIMATE EFI ISO CREATOR - CLEAN SLATE")
        print("=" * 60)
        print(f"📋 SCRIPT: {SCRIPT_NAME} VERSION: {VERSION}")
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 Goal: Create ONE working EFI bootable Ubuntu ISO")
        print("🧹 Method: Archive everything, start completely fresh")
        print()
        
    def setup_workspace(self):
        """Create clean workspace"""
        print("🏗️ SETTING UP CLEAN WORKSPACE")
        print("-" * 40)
        
        # Ensure iso directory exists
        self.iso_dir.mkdir(exist_ok=True)
        os.chdir(self.iso_dir)
        print(f"📂 Working in: {self.iso_dir}")
        
        # Archive existing files
        if any(self.iso_dir.iterdir()):
            print("📦 Archiving existing files...")
            self.archive_dir.mkdir(exist_ok=True)
            
            for item in self.iso_dir.iterdir():
                if item.name != self.archive_dir.name:
                    try:
                        if item.is_dir():
                            shutil.move(str(item), str(self.archive_dir / item.name))
                        else:
                            shutil.move(str(item), str(self.archive_dir / item.name))
                        print(f"   Archived: {item.name}")
                    except Exception as e:
                        print(f"   ⚠️  Could not archive {item.name}: {e}")
            
            print(f"✅ Files archived to: {self.archive_dir}")
        else:
            print("✅ Directory already clean")
        
        return True
    
    def install_dependencies(self):
        """Install required tools"""
        print("\n🔧 INSTALLING DEPENDENCIES")
        print("-" * 30)
        
        required = ["xorriso", "7z", "wget"]
        missing = []
        
        for tool in required:
            if shutil.which(tool) is None:
                missing.append(tool)
        
        if missing:
            print(f"📥 Installing: {', '.join(missing)}")
            try:
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "xorriso", "p7zip-full", "wget"], check=True)
                print("✅ Dependencies installed")
            except subprocess.CalledProcessError:
                print("❌ Failed to install dependencies")
                return False
        else:
            print("✅ All dependencies available")
        
        return True
    
    def download_ubuntu_iso(self):
        """Download fresh Ubuntu ISO"""
        print("\n📥 DOWNLOADING FRESH UBUNTU ISO")
        print("-" * 35)
        
        if Path(self.ubuntu_iso).exists():
            size = Path(self.ubuntu_iso).stat().st_size
            if size == 3213064192:  # Exact expected size
                print("✅ Valid Ubuntu ISO already exists")
                return True
            else:
                print("🗑️ Removing corrupted ISO")
                Path(self.ubuntu_iso).unlink()
        
        print(f"📡 Downloading: {self.ubuntu_url}")
        try:
            subprocess.run([
                "wget", "-O", self.ubuntu_iso, self.ubuntu_url
            ], check=True)
            
            # Verify size
            size = Path(self.ubuntu_iso).stat().st_size
            if size == 3213064192:
                print("✅ Ubuntu ISO downloaded and verified")
                return True
            else:
                print(f"❌ Download incomplete: {size} bytes")
                return False
                
        except subprocess.CalledProcessError:
            print("❌ Download failed")
            return False
    
    def create_working_efi_iso(self):
        """Create the working EFI ISO using proven method"""
        print("\n🏗️ CREATING WORKING EFI ISO")
        print("-" * 32)
        
        # Extract ISO
        extract_dir = Path("ubuntu_extracted")
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir()
        
        print("📂 Extracting Ubuntu ISO...")
        try:
            subprocess.run([
                "7z", "x", f"-o{extract_dir}", self.ubuntu_iso
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("❌ Extraction failed")
            return False
        
        # Inject HelloWorld.txt
        hello_file = extract_dir / "HelloWorld.txt"
        hello_content = f"""🎉 EFI BOOT SUCCESS PROOF!

This file proves:
✅ ISO customization works
✅ EFI boot successful  
✅ File injection verified

Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Script: {SCRIPT_NAME} v{VERSION}
Method: Ubuntu's exact boot method
"""
        hello_file.write_text(hello_content)
        print("✅ HelloWorld.txt injected")
        
        # Use Ubuntu's EXACT method - bootx64.efi with minimal parameters
        print("🔨 Building EFI ISO with Ubuntu's exact method...")
        xorriso_cmd = [
            "xorriso", "-as", "mkisofs",
            "-r",
            "-V", "Ubuntu-EFI-Working",
            "-J", "-joliet-long",
            "-b", "boot/grub/i386-pc/eltorito.img",
            "-c", "boot.catalog",
            "-no-emul-boot",
            "-boot-load-size", "4",
            "-boot-info-table",
            "-eltorito-alt-boot",
            "-e", "EFI/boot/bootx64.efi",  # Ubuntu's method
            "-no-emul-boot",
            "-isohybrid-gpt-basdat",
            "-o", self.final_iso,
            str(extract_dir)
        ]
        
        try:
            result = subprocess.run(xorriso_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                size = Path(self.final_iso).stat().st_size / (1024**3)
                print(f"✅ EFI ISO created: {self.final_iso} ({size:.1f} GB)")
                
                # Verify HelloWorld.txt in ISO
                verify_result = subprocess.run([
                    "7z", "l", self.final_iso, "HelloWorld.txt"
                ], capture_output=True, text=True)
                
                if "HelloWorld.txt" in verify_result.stdout:
                    print("✅ HelloWorld.txt verified in ISO")
                    return True
                else:
                    print("❌ HelloWorld.txt missing from ISO")
                    return False
            else:
                print("❌ ISO creation failed")
                print(f"Error: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ xorriso failed: {e}")
            return False
    
    def show_results(self):
        """Show final results and testing instructions"""
        print("\n🎉 ULTIMATE EFI CREATOR COMPLETED!")
        print("=" * 45)
        
        if Path(self.final_iso).exists():
            size = Path(self.final_iso).stat().st_size / (1024**3)
            print(f"✅ FINAL ISO: {self.final_iso} ({size:.1f} GB)")
            print(f"📂 Location: {self.iso_dir / self.final_iso}")
            
            print("\n🧪 EFI BOOT TEST INSTRUCTIONS:")
            print("1. Copy ISO to machine with VirtualBox")
            print("2. Create VM: Linux > Ubuntu (64-bit)")
            print("3. ⚡ CRITICAL: Enable EFI in VM settings")
            print("4. Mount ISO and boot")
            print("5. Verify GRUB loads and Ubuntu boots")
            print("6. Check HelloWorld.txt exists")
            
            print(f"\n📋 SUCCESS CRITERIA:")
            print("✅ Short boot messages (like original Ubuntu)")
            print("✅ GRUB menu appears")
            print("✅ Ubuntu boots to login")
            print("✅ HelloWorld.txt accessible")
            
            if self.archive_dir.exists():
                print(f"\n📦 Previous files archived: {self.archive_dir}")
            
            return True
        else:
            print("❌ No ISO created - check errors above")
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        temp_dirs = ["ubuntu_extracted", "work"]
        for temp_dir in temp_dirs:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
        print("🧹 Temporary files cleaned")
    
    def run(self):
        """Execute complete workflow"""
        self.show_header()
        
        steps = [
            ("Setup Clean Workspace", self.setup_workspace),
            ("Install Dependencies", self.install_dependencies),
            ("Download Ubuntu ISO", self.download_ubuntu_iso),
            ("Create Working EFI ISO", self.create_working_efi_iso),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ FAILED: {step_name}")
                return False
        
        self.cleanup()
        success = self.show_results()
        
        if success:
            print(f"\n🚀 READY FOR TESTING: {self.final_iso}")
            print("This ISO uses Ubuntu's proven EFI boot method")
        
        return success

if __name__ == "__main__":
    creator = UltimateEFICreator()
    success = creator.run()
    sys.exit(0 if success else 1)