#!/usr/bin/env python3
"""
Boot Order Fix - Use Ubuntu's Exact xorriso Boot Sequence
Purpose: Fix boot catalog order to match successful Ubuntu ISO
VERSION: 1.0.1 - Cache-busted with version display
"""

VERSION = "1.0.1"
SCRIPT_NAME = "boot_order_fix.py"

import os
import sys
import subprocess
import shutil
from pathlib import Path

class BootOrderFix:
    def __init__(self):
        # Use ~/iso as working directory
        self.iso_dir = Path.home() / "iso"
        self.iso_dir.mkdir(exist_ok=True)
        os.chdir(self.iso_dir)
        
        self.ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
        self.extract_dir = self.iso_dir / "boot_fix_extract"
        
    def extract_and_modify(self):
        """Extract Ubuntu ISO and add HelloWorld.txt"""
        print("📂 Extracting Ubuntu ISO with HelloWorld.txt...")
        
        if self.extract_dir.exists():
            shutil.rmtree(self.extract_dir)
        self.extract_dir.mkdir()
        
        try:
            subprocess.run([
                "7z", "x", f"-o{self.extract_dir}", self.ubuntu_iso
            ], check=True)
            
            # Add HelloWorld.txt
            hello_file = self.extract_dir / "HelloWorld.txt"
            hello_file.write_text("Hello World - Boot Order Fix Test!")
            print("✅ HelloWorld.txt injected")
            
            return True
        except subprocess.CalledProcessError:
            print("❌ Extraction failed")
            return False
    
    def create_minimal_xorriso_iso(self):
        """Create ISO with minimal xorriso parameters - exactly like Ubuntu"""
        print("\n🔧 Creating ISO with MINIMAL Ubuntu-like parameters...")
        
        # This mirrors Ubuntu's exact xorriso sequence for server ISOs
        # Removed problematic parameters that cause boot catalog differences
        minimal_cmd = [
            "xorriso", "-as", "mkisofs",
            "-r",
            "-V", "Ubuntu-Server 24.04.2 BootFix",
            "-J", "-joliet-long", 
            "-b", "boot/grub/i386-pc/eltorito.img",
            "-c", "boot.catalog",
            "-no-emul-boot",
            "-boot-load-size", "4",
            "-boot-info-table",
            "-eltorito-alt-boot",
            "-e", "EFI/boot/bootx64.efi",  # Use bootx64.efi like Ubuntu original
            "-no-emul-boot",
            "-isohybrid-gpt-basdat",
            "-o", "helloefi_minimal.iso",
            str(self.extract_dir)
        ]
        
        print("Running minimal xorriso command:")
        print(" ".join(minimal_cmd))
        
        try:
            result = subprocess.run(minimal_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Minimal ISO created successfully")
                iso_size = Path("helloefi_minimal.iso").stat().st_size / (1024*1024*1024)
                print(f"📊 Output: helloefi_minimal.iso ({iso_size:.1f} GB)")
                return True
            else:
                print("❌ Minimal ISO creation failed")
                print("STDERR:", result.stderr)
                return False
        except subprocess.CalledProcessError as e:
            print(f"❌ xorriso failed: {e}")
            return False
    
    def create_exact_ubuntu_sequence(self):
        """Create ISO with the exact same parameter sequence as Ubuntu build"""
        print("\n🔧 Creating ISO with EXACT Ubuntu build sequence...")
        
        # This is Ubuntu's exact sequence from their official build scripts
        # Order matters for boot catalog generation!
        exact_cmd = [
            "xorriso", "-as", "mkisofs",
            "-r",
            "-V", "Ubuntu-Server 24.04.2 Exact",
            "-o", "helloefi_exact.iso",
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
            str(self.extract_dir)
        ]
        
        print("Running exact Ubuntu sequence:")
        print(" ".join(exact_cmd))
        
        try:
            result = subprocess.run(exact_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Exact sequence ISO created successfully")
                iso_size = Path("helloefi_exact.iso").stat().st_size / (1024*1024*1024)
                print(f"📊 Output: helloefi_exact.iso ({iso_size:.1f} GB)")
                return True
            else:
                print("❌ Exact sequence ISO creation failed")
                print("STDERR:", result.stderr)
                return False
        except subprocess.CalledProcessError as e:
            print(f"❌ xorriso failed: {e}")
            return False
    
    def create_grubx64_priority_iso(self):
        """Create ISO with grubx64.efi as primary (our previous approach)"""
        print("\n🔧 Creating ISO with grubx64.efi priority...")
        
        grub_cmd = [
            "xorriso", "-as", "mkisofs",
            "-r",
            "-V", "Ubuntu-Server 24.04.2 GrubPriority", 
            "-J", "-joliet-long",
            "-b", "boot/grub/i386-pc/eltorito.img",
            "-c", "boot.catalog",
            "-no-emul-boot",
            "-boot-load-size", "4",
            "-boot-info-table",
            "-eltorito-alt-boot",
            "-e", "EFI/boot/grubx64.efi",  # Use grubx64.efi
            "-no-emul-boot", 
            "-isohybrid-gpt-basdat",
            "-o", "helloefi_grub_priority.iso",
            str(self.extract_dir)
        ]
        
        print("Running grubx64.efi priority command:")
        print(" ".join(grub_cmd))
        
        try:
            result = subprocess.run(grub_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Grub priority ISO created successfully")
                iso_size = Path("helloefi_grub_priority.iso").stat().st_size / (1024*1024*1024)
                print(f"📊 Output: helloefi_grub_priority.iso ({iso_size:.1f} GB)")
                return True
            else:
                print("❌ Grub priority ISO creation failed")
                print("STDERR:", result.stderr)
                return False
        except subprocess.CalledProcessError as e:
            print(f"❌ xorriso failed: {e}")
            return False
    
    def show_test_results(self):
        """Show which ISOs were created for testing"""
        print("\n📁 BOOT ORDER TEST ISOs CREATED:")
        print("=" * 50)
        
        test_isos = [
            ("helloefi_minimal.iso", "Minimal Ubuntu parameters"),
            ("helloefi_exact.iso", "Exact Ubuntu build sequence"),
            ("helloefi_grub_priority.iso", "grubx64.efi priority"),
            ("helloefi.iso", "Previous attempt (if exists)")
        ]
        
        created_isos = []
        for iso_name, description in test_isos:
            if Path(iso_name).exists():
                size = Path(iso_name).stat().st_size / (1024*1024*1024)
                created_isos.append(iso_name)
                print(f"✅ {iso_name} ({size:.1f} GB) - {description}")
            else:
                print(f"❌ {iso_name} - Not created")
        
        print(f"\n🧪 TEST PRIORITY ORDER:")
        print("1. helloefi_minimal.iso (most likely to work)")
        print("2. helloefi_exact.iso (exact Ubuntu sequence)")
        print("3. helloefi_grub_priority.iso (our grubx64.efi approach)")
        
        print(f"\n🎯 HYPOTHESIS:")
        print("The working ISO should show SHORTER boot error messages")
        print("Like the original Ubuntu ISO you mentioned!")
        
        return created_isos
    
    def run(self):
        """Main execution flow"""
        print(f"🚀 Boot Order Fix - Match Ubuntu's Boot Sequence")
        print("=" * 60)
        print(f"📋 SCRIPT: {SCRIPT_NAME} VERSION: {VERSION}")
        print(f"📂 Working in: {os.getcwd()}")
        print("🎯 Goal: Create ISO with shorter boot error messages")
        
        if not Path(self.ubuntu_iso).exists():
            print(f"❌ Ubuntu ISO not found: {self.ubuntu_iso}")
            return False
        
        # Extract and modify
        if not self.extract_and_modify():
            return False
        
        # Create multiple test ISOs with different approaches
        success_count = 0
        if self.create_minimal_xorriso_iso():
            success_count += 1
        if self.create_exact_ubuntu_sequence():
            success_count += 1
        if self.create_grubx64_priority_iso():
            success_count += 1
        
        # Show results
        created_isos = self.show_test_results()
        
        if success_count > 0:
            print(f"\n🎉 SUCCESS: {success_count} test ISOs created!")
            print("🧪 Test each one in VirtualBox with EFI enabled")
            print("🎯 Look for the one with SHORTER error messages!")
            return True
        else:
            print("❌ No ISOs created successfully")
            return False

if __name__ == "__main__":
    fixer = BootOrderFix()
    success = fixer.run()
    sys.exit(0 if success else 1)